# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import unittest
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Tuple

from fluster.download_manager import DownloadManager
from fluster.utils import file_checksum, filename_from_url


def _url(filename: str) -> str:
    """A URL for *filename* that must never be contacted by the tests."""
    return f"https://example.invalid/{filename}"


@dataclass
class _FakeVector:
    source: str
    source_checksum: str
    input_file: str


@dataclass
class _FakeSuite:
    name: str
    test_vectors: Dict[str, _FakeVector]


def _make_zip(path: str, members: Dict[str, bytes]) -> str:
    """Create a zip file and return its checksum."""
    with zipfile.ZipFile(path, "w") as zip_file:
        for name, data in members.items():
            zip_file.writestr(name, data)
    return file_checksum(path)


def _seed_cache(out_dir: str, url: str, source_path: str) -> str:
    """Place *source_path* in the shared cache where the manager looks for it."""
    cache_dir = os.path.join(out_dir, DownloadManager.CACHE_DIR, hashlib.md5(url.encode()).hexdigest())
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, filename_from_url(url))
    shutil.copy2(source_path, cache_path)
    return cache_path


class TestDownloadManager(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name
        self.resources = os.path.join(self.tmp, "resources")
        self.build = os.path.join(self.tmp, "build")
        os.makedirs(self.build)

    def _archive(self, filename: str, members: Dict[str, bytes]) -> Tuple[str, str]:
        path = os.path.join(self.build, filename)
        checksum = _make_zip(path, members)
        url = _url(filename)
        _seed_cache(self.resources, url, path)
        return url, checksum

    def _plain(self, filename: str, data: bytes) -> Tuple[str, str]:
        path = os.path.join(self.build, filename)
        with open(path, "wb") as handle:
            handle.write(data)
        url = _url(filename)
        _seed_cache(self.resources, url, path)
        return url, file_checksum(path)

    def _download(
        self,
        suites: List[_FakeSuite],
        extract_all: bool = False,
        keep_file: bool = False,
    ) -> None:
        manager = DownloadManager(
            self.resources,
            verify=True,
            extract_all=extract_all,
            keep_file=keep_file,
            retries=1,
        )
        manager.download(suites, 1)

    def _assert_exists(self, *parts: str) -> str:
        path = os.path.join(self.resources, *parts)
        self.assertTrue(os.path.exists(path), f"expected {path} to exist")
        return path

    def _assert_missing(self, *parts: str) -> None:
        path = os.path.join(self.resources, *parts)
        self.assertFalse(os.path.exists(path), f"expected {path} to not exist")

    def test_single_source_suite_extracts_at_suite_root(self) -> None:
        url, checksum = self._archive("shared.zip", {"a.bits": b"a", "b.bits": b"b"})
        suite = _FakeSuite(
            "single",
            {
                "va": _FakeVector(url, checksum, "a.bits"),
                "vb": _FakeVector(url, checksum, "b.bits"),
            },
        )
        self._download([suite])
        self._assert_exists("single", "a.bits")
        self._assert_exists("single", "b.bits")
        self._assert_missing(DownloadManager.CACHE_DIR)

    def test_multi_source_suite_extracts_shared_archive_per_vector(self) -> None:
        url, checksum = self._archive("shared.zip", {"a.bits": b"a"})
        plain_url, plain_checksum = self._plain("other.bin", b"other")
        suite = _FakeSuite(
            "multi",
            {
                "v1": _FakeVector(url, checksum, "a.bits"),
                "v2": _FakeVector(url, checksum, "a.bits"),
                "v3": _FakeVector(plain_url, plain_checksum, "other.bin"),
            },
        )
        self._download([suite])
        self._assert_exists("multi", "v1", "a.bits")
        self._assert_exists("multi", "v2", "a.bits")
        self._assert_exists("multi", "v3", "other.bin")
        self._assert_missing("multi", "a.bits")

    def test_source_shared_by_root_and_per_vector_suites(self) -> None:
        url, checksum = self._archive("shared.zip", {"a.bits": b"a"})
        plain_url, plain_checksum = self._plain("other.bin", b"other")
        root_suite = _FakeSuite(
            "single",
            {
                "va": _FakeVector(url, checksum, "a.bits"),
                "vb": _FakeVector(url, checksum, "a.bits"),
            },
        )
        multi_suite = _FakeSuite(
            "multi",
            {
                "v1": _FakeVector(url, checksum, "a.bits"),
                "v2": _FakeVector(plain_url, plain_checksum, "other.bin"),
            },
        )
        self._download([root_suite, multi_suite])
        self._assert_exists("single", "a.bits")
        self._assert_exists("multi", "v1", "a.bits")
        self._assert_missing("multi", "a.bits")

    def test_extract_all_reextracts_into_non_empty_dir(self) -> None:
        url, checksum = self._archive("shared.zip", {"a.bits": b"a", "nested/c.bits": b"c"})
        suite = _FakeSuite("extract_all", {"v": _FakeVector(url, checksum, "ignored.bits")})
        dest_dir = os.path.join(self.resources, "extract_all", "v")
        os.makedirs(dest_dir)
        with open(os.path.join(dest_dir, ".DS_Store"), "wb"):
            pass

        self._download([suite], extract_all=True)

        self._assert_exists("extract_all", "v", "a.bits")
        self._assert_exists("extract_all", "v", "nested", "c.bits")

    def test_keep_file_leaves_archives_only_in_the_cache(self) -> None:
        url, checksum = self._archive("shared.zip", {"a.bits": b"a", "b.bits": b"b"})
        suite = _FakeSuite(
            "single",
            {
                "va": _FakeVector(url, checksum, "a.bits"),
                "vb": _FakeVector(url, checksum, "b.bits"),
            },
        )
        self._download([suite], keep_file=True)
        self._assert_exists("single", "a.bits")
        self._assert_exists(DownloadManager.CACHE_DIR, hashlib.md5(url.encode()).hexdigest(), "shared.zip")
        self._assert_missing("single", "shared.zip")

    def test_satisfied_destinations_skip_download(self) -> None:
        # The URL can never be downloaded: the test succeeds only if the
        # already extracted file is detected and the source is skipped.
        url = _url("missing.zip")
        suite = _FakeSuite("satisfied", {"v": _FakeVector(url, "unknown", "a.bits")})
        dest_dir = os.path.join(self.resources, "satisfied", "v")
        os.makedirs(dest_dir)
        with open(os.path.join(dest_dir, "a.bits"), "wb") as handle:
            handle.write(b"a")

        self._download([suite])

        self._assert_exists("satisfied", "v", "a.bits")


if __name__ == "__main__":
    unittest.main(verbosity=2)
