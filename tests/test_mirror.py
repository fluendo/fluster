#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Canonical Ltd.
#  Author: Alexandre Esse <alexandre.esse@canonical.com>
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

import functools
import http.server
import importlib.util
import os
import tempfile
import threading
import unittest
import urllib.parse

from fluster import utils

_MIRROR_SYNC_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "mirror_sync.py")
_spec = importlib.util.spec_from_file_location("mirror_sync", _MIRROR_SYNC_PATH)
mirror_sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mirror_sync)


class TestRewriteUrl(unittest.TestCase):
    def test_basic_https(self) -> None:
        result = utils.rewrite_url(
            "https://storage.googleapis.com/aom-test-data/file.ivf",
            "http://mirror.local:8080/fluster/",
        )
        self.assertEqual(result, "http://mirror.local:8080/fluster/storage.googleapis.com/aom-test-data/file.ivf")

    def test_mirror_without_trailing_slash(self) -> None:
        result = utils.rewrite_url(
            "https://www.itu.int/wftp3/av-arch/jvt-site/draft_conformance/AVCv1/AUD_MW_E.zip",
            "http://mirror.local:8080/fluster",
        )
        self.assertEqual(
            result,
            "http://mirror.local:8080/fluster/www.itu.int/wftp3/av-arch/jvt-site/draft_conformance/AVCv1/AUD_MW_E.zip",
        )

    def test_mirror_with_trailing_slash(self) -> None:
        result = utils.rewrite_url(
            "https://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_IEC_13818-4/file.adts",
            "http://mirror.local:8080/mirror/",
        )
        self.assertEqual(
            result,
            "http://mirror.local:8080/mirror/standards.iso.org/ittf/PubliclyAvailableStandards/ISO_IEC_13818-4/file.adts",
        )

    def test_url_with_query(self) -> None:
        result = utils.rewrite_url(
            "https://example.com/path/file.zip?token=abc",
            "http://mirror.local:8080/",
        )
        self.assertEqual(result, "http://mirror.local:8080/example.com/path/file.zip?token=abc")

    def test_port_in_original_url(self) -> None:
        result = utils.rewrite_url(
            "https://example.com:8443/path/file.zip",
            "http://mirror.local:8080/fluster/",
        )
        self.assertEqual(result, "http://mirror.local:8080/fluster/example.com:8443/path/file.zip")

    def test_http_source(self) -> None:
        result = utils.rewrite_url(
            "http://example.com/path/file.zip",
            "http://mirror.local:8080/fluster/",
        )
        self.assertEqual(result, "http://mirror.local:8080/fluster/example.com/path/file.zip")


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


class TestDownloadWithMirror(unittest.TestCase):
    def _serve_dir(self, serve_root: str) -> tuple:
        handler = functools.partial(_SilentHandler, directory=serve_root)
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port

    def test_download_from_mirror_success(self) -> None:
        test_content = b"mirror test content"
        with tempfile.TemporaryDirectory() as tmpdir:
            mirror_root = os.path.join(tmpdir, "mirror")
            subpath = os.path.join(mirror_root, "fake.example.com", "data")
            os.makedirs(subpath, exist_ok=True)
            with open(os.path.join(subpath, "testfile.bin"), "wb") as f:
                f.write(test_content)

            server, port = self._serve_dir(mirror_root)
            try:
                dest_dir = os.path.join(tmpdir, "dest")
                utils.download(
                    "https://fake.example.com/data/testfile.bin",
                    dest_dir,
                    max_retries=1,
                    mirror=f"http://127.0.0.1:{port}/",
                )
                dest_file = os.path.join(dest_dir, "testfile.bin")
                self.assertTrue(os.path.exists(dest_file))
                with open(dest_file, "rb") as f:
                    self.assertEqual(f.read(), test_content)
            finally:
                server.shutdown()

    def test_download_mirror_fallback_to_original(self) -> None:
        original_content = b"original source content"
        with tempfile.TemporaryDirectory() as tmpdir:
            serve_root = os.path.join(tmpdir, "original")
            os.makedirs(serve_root, exist_ok=True)
            with open(os.path.join(serve_root, "fallback.bin"), "wb") as f:
                f.write(original_content)

            server, port = self._serve_dir(serve_root)
            try:
                dest_dir = os.path.join(tmpdir, "dest")
                utils.download(
                    f"http://127.0.0.1:{port}/fallback.bin",
                    dest_dir,
                    max_retries=1,
                    mirror="http://127.0.0.1:1/",
                )
                dest_file = os.path.join(dest_dir, "fallback.bin")
                self.assertTrue(os.path.exists(dest_file))
                with open(dest_file, "rb") as f:
                    self.assertEqual(f.read(), original_content)
            finally:
                server.shutdown()

    def test_download_without_mirror(self) -> None:
        content = b"no mirror content"
        with tempfile.TemporaryDirectory() as tmpdir:
            serve_root = os.path.join(tmpdir, "serve")
            os.makedirs(serve_root, exist_ok=True)
            with open(os.path.join(serve_root, "plain.bin"), "wb") as f:
                f.write(content)

            server, port = self._serve_dir(serve_root)
            try:
                dest_dir = os.path.join(tmpdir, "dest")
                utils.download(
                    f"http://127.0.0.1:{port}/plain.bin",
                    dest_dir,
                    max_retries=1,
                )
                dest_file = os.path.join(dest_dir, "plain.bin")
                self.assertTrue(os.path.exists(dest_file))
                with open(dest_file, "rb") as f:
                    self.assertEqual(f.read(), content)
            finally:
                server.shutdown()


def _key_to_fs_path(root: str, key: str) -> str:
    """Maps an object key (URL path) to a filesystem path under ``root``.

    Object keys can contain characters that are illegal in Windows paths (most
    notably ':' from ``host:port``) and may be percent-encoded. Decode them and
    replace ':' so the fake bucket can store them on any platform."""
    key = urllib.parse.unquote(key).lstrip("/")
    parts = [part.replace(":", "_") for part in key.split("/")]
    return os.path.join(root, *parts)


class _BucketHandler(http.server.BaseHTTPRequestHandler):
    """Minimal radosgw-like handler storing objects under a root dir."""

    root: str = ""

    def log_message(self, fmt, *args):
        pass

    def _object_path(self) -> str:
        return _key_to_fs_path(self.root, self.path)

    def do_HEAD(self):  # noqa: N802
        if os.path.isfile(self._object_path()):
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def do_PUT(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        path = self._object_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        self.send_response(200)
        self.end_headers()


class TestBucketUpload(unittest.TestCase):
    def _serve_bucket(self, root: str) -> tuple:
        handler = type("_Handler", (_BucketHandler,), {"root": root})
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port

    def test_upload_puts_object_with_mirror_key(self) -> None:
        test_content = b"bucket upload content"
        with tempfile.TemporaryDirectory() as tmpdir:
            # Source HTTP server.
            source_root = os.path.join(tmpdir, "source")
            src_sub = os.path.join(source_root, "data")
            os.makedirs(src_sub, exist_ok=True)
            with open(os.path.join(src_sub, "vector.bin"), "wb") as f:
                f.write(test_content)
            src_handler = functools.partial(_SilentHandler, directory=source_root)
            src_server = http.server.HTTPServer(("127.0.0.1", 0), src_handler)
            src_port = src_server.server_address[1]
            threading.Thread(target=src_server.serve_forever, daemon=True).start()

            # Bucket server.
            bucket_root = os.path.join(tmpdir, "bucket")
            os.makedirs(bucket_root, exist_ok=True)
            bucket_server, bucket_port = self._serve_bucket(bucket_root)

            try:
                url = f"http://127.0.0.1:{src_port}/data/vector.bin"
                mirror_sync._upload_one(  # noqa: SLF001
                    url,
                    rgw_host=f"127.0.0.1:{bucket_port}",
                    bucket="test-bucket",
                    retries=1,
                )
                expected = _key_to_fs_path(bucket_root, f"test-bucket/127.0.0.1:{src_port}/data/vector.bin")
                self.assertTrue(os.path.exists(expected), f"missing {expected}")
                with open(expected, "rb") as f:
                    self.assertEqual(f.read(), test_content)
            finally:
                src_server.shutdown()
                bucket_server.shutdown()

    def test_upload_skips_existing_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bucket_root = os.path.join(tmpdir, "bucket")
            existing = _key_to_fs_path(bucket_root, "test-bucket/127.0.0.1:9/data/vector.bin")
            os.makedirs(os.path.dirname(existing), exist_ok=True)
            with open(existing, "wb") as f:
                f.write(b"already here")

            bucket_server, bucket_port = self._serve_bucket(bucket_root)
            try:
                # Source points at an unreachable port; if not skipped, it would fail.
                url = "http://127.0.0.1:9/data/vector.bin"
                mirror_sync._upload_one(  # noqa: SLF001
                    url,
                    rgw_host=f"127.0.0.1:{bucket_port}",
                    bucket="test-bucket",
                    retries=0,
                )
                with open(existing, "rb") as f:
                    self.assertEqual(f.read(), b"already here")
            finally:
                bucket_server.shutdown()


class TestBucketObjectUrl(unittest.TestCase):
    def test_host_without_scheme(self) -> None:
        result = mirror_sync._bucket_object_url("rgw.example.com", "mybucket", "example.com/a/b.bin")  # noqa: SLF001
        self.assertEqual(result, "http://rgw.example.com/mybucket/example.com/a/b.bin")

    def test_host_with_scheme(self) -> None:
        result = mirror_sync._bucket_object_url("http://rgw.example.com/", "bucket", "/host/file.bin")  # noqa: SLF001
        self.assertEqual(result, "http://rgw.example.com/bucket/host/file.bin")


if __name__ == "__main__":
    unittest.main(verbosity=2)
