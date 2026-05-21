from __future__ import annotations

import functools
import http.server
import os
import tempfile
import threading
import unittest

from fluster import utils


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
