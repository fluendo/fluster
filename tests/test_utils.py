# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
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

import gzip
import io
import os
import shutil
import tarfile
import tempfile
import unittest
import zipfile
from typing import Dict

from fluster import utils


def _make_zip(path: str, members: Dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zip_file:
        for name, data in members.items():
            zip_file.writestr(name, data)


class _ZipTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name

    def _zip(self, filename: str, members: Dict[str, bytes]) -> str:
        path = os.path.join(self.tmp, filename)
        _make_zip(path, members)
        return path


class TestExtractArchive(_ZipTestCase):
    def test_empty_member_means_extract_all(self) -> None:
        zp = self._zip("flat.zip", {"a.bits": b"a", "nested/c.bits": b"c"})
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        utils.extract_archive(zp, [("", out)])
        self.assertTrue(os.path.exists(os.path.join(out, "a.bits")))
        self.assertTrue(os.path.exists(os.path.join(out, "nested", "c.bits")))

    def test_named_member(self) -> None:
        zp = self._zip("flat.zip", {"a.bits": b"a", "b.bits": b"b"})
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        utils.extract_archive(zp, [("a.bits", out)])
        self.assertTrue(os.path.exists(os.path.join(out, "a.bits")))
        self.assertFalse(os.path.exists(os.path.join(out, "b.bits")))

    def test_named_member_with_prefix(self) -> None:
        zp = self._zip("pkg.zip", {"pkg.zip/a.bits": b"a", "pkg.zip/nested/c.bits": b"c"})
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        missing = utils.extract_archive(zp, [("a.bits", out)])
        self.assertEqual(missing, [])
        self.assertTrue(os.path.exists(os.path.join(out, "a.bits")))

    def test_extract_all_and_multiple_dirs(self) -> None:
        zp = self._zip("flat.zip", {"a.bits": b"a", "b.bits": b"b"})
        out1 = os.path.join(self.tmp, "out1")
        out2 = os.path.join(self.tmp, "out2")
        os.makedirs(out1)
        os.makedirs(out2)
        missing = utils.extract_archive(zp, [(None, out1), ("b.bits", out2)])
        self.assertEqual(missing, [])
        self.assertTrue(os.path.exists(os.path.join(out1, "a.bits")))
        self.assertTrue(os.path.exists(os.path.join(out1, "b.bits")))
        self.assertTrue(os.path.exists(os.path.join(out2, "b.bits")))

    def test_missing_member_reported(self) -> None:
        zp = self._zip("flat.zip", {"a.bits": b"a"})
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        missing = utils.extract_archive(zp, [("nope.bits", out)])
        self.assertEqual(missing, ["nope.bits"])

    def test_zip_slip_rejected(self) -> None:
        zp = self._zip("flat.zip", {"../escaped.txt": b"x"})
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        with self.assertRaises(ValueError):
            utils.extract_archive(zp, [(None, out)])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "escaped.txt")))

    @unittest.skipUnless(shutil.which("tar"), "tar not available")
    def test_tar_named_members_grouped_and_extract_all(self) -> None:
        tp = os.path.join(self.tmp, "pkg.tar.gz")
        with tarfile.open(tp, "w:gz") as tar_file:
            for name in ("a.bits", "b.bits"):
                info = tarfile.TarInfo(name)
                info.size = 1
                tar_file.addfile(info, io.BytesIO(b"x"))
        out1 = os.path.join(self.tmp, "out1")
        out2 = os.path.join(self.tmp, "out2")
        os.makedirs(out1)
        os.makedirs(out2)
        missing = utils.extract_archive(tp, [("a.bits", out1), ("b.bits", out1), (None, out2)])
        self.assertEqual(missing, [])
        self.assertEqual(sorted(os.listdir(out1)), ["a.bits", "b.bits"])
        self.assertEqual(sorted(os.listdir(out2)), ["a.bits", "b.bits"])

    @unittest.skipUnless(shutil.which("gunzip"), "gunzip not available")
    def test_gzip_decompressed_into_each_dir(self) -> None:
        gp = os.path.join(self.tmp, "clip.bs.gz")
        with gzip.open(gp, "wb") as gz_file:
            gz_file.write(b"data")
        out = os.path.join(self.tmp, "out")
        os.makedirs(out)
        self.assertEqual(utils.extract_archive(gp, [("ignored", out)]), [])
        with open(os.path.join(out, "clip.bs"), "rb") as handle:
            self.assertEqual(handle.read(), b"data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
