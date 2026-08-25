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

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from typing import Callable

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils


def collect_source_urls(test_suites_dir: str) -> list[str]:
    urls = []
    for root, _, files in os.walk(test_suites_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"WARNING: skipping {filepath}: {e}")
                continue
            for tv in data.get("test_vectors", []):
                source = tv.get("source")
                if source and source not in urls:
                    urls.append(source)
            for tv in data.get("failing_test_vectors", []):
                source = tv.get("source")
                if source and source not in urls:
                    urls.append(source)
    return urls


def url_to_mirror_path(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return os.path.join(parsed.netloc, parsed.path.lstrip("/"))


def _sync_one(url: str, output_dir: str, retries: int) -> None:
    mirror_path = url_to_mirror_path(url)
    dest_dir = os.path.join(output_dir, os.path.dirname(mirror_path))
    dest_file = os.path.join(output_dir, mirror_path)

    if os.path.exists(dest_file):
        print(f"  SKIP (exists): {mirror_path}")
        return

    print(f"  DOWNLOAD: {mirror_path}")
    utils.download(url, dest_dir, max_retries=retries)


def _bucket_object_url(rgw_host: str, bucket: str, key: str) -> str:
    """Builds the radosgw object URL for a given key, e.g.
    http://<rgw_host>/<bucket>/<key>."""
    base = rgw_host if "://" in rgw_host else f"http://{rgw_host}"
    # Keep ':' and '/' unquoted so the object key layout matches exactly what
    # fluster's rewrite_url (used by `fluster download --mirror`) requests.
    quoted_key = urllib.parse.quote(key.lstrip("/"), safe="/:")
    return f"{base.rstrip('/')}/{urllib.parse.quote(bucket, safe='')}/{quoted_key}"


def _object_exists(object_url: str, timeout: int = 60) -> bool:
    """Returns True if the object already exists in the bucket (HTTP HEAD 2xx)."""
    req = urllib.request.Request(object_url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return bool(200 <= response.status < 300)
    except urllib.error.HTTPError:
        return False
    except urllib.error.URLError:
        return False


def _put_object(object_url: str, src_path: str, timeout: int = 300) -> None:
    """Uploads a local file to the bucket via HTTP PUT, equivalent to
    'curl -X PUT --data-binary @src_path object_url'."""
    size = os.path.getsize(src_path)
    with open(src_path, "rb") as src:
        req = urllib.request.Request(object_url, data=src, method="PUT")
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("Content-Length", str(size))
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"Unexpected status {response.status} uploading to {object_url}")


def _upload_one(url: str, rgw_host: str, bucket: str, retries: int) -> None:
    key = url_to_mirror_path(url)
    object_url = _bucket_object_url(rgw_host, bucket, key)

    if _object_exists(object_url):
        print(f"  SKIP (exists): {key}")
        return

    last_exc = None
    for attempt in range(retries + 1):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                print(f"  DOWNLOAD: {key}")
                utils.download(url, tmpdir, max_retries=retries)
                src_file = os.path.join(tmpdir, os.path.basename(key))
                print(f"  UPLOAD: {object_url}")
                _put_object(object_url, src_file)
            return
        except (OSError, RuntimeError, urllib.error.URLError) as e:
            last_exc = e
            if attempt < retries:
                print(f"  WARNING: attempt {attempt + 1} failed for {key}: {e}")
    print(f"  ERROR: failed to upload {key}: {last_exc}")


def sync_urls(urls: list[str], worker: Callable[[str], None], jobs: int) -> None:
    from multiprocessing import Pool

    if jobs <= 1:
        for url in urls:
            worker(url)
    else:
        with Pool(jobs) as pool:
            pool.map(worker, urls)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate a mirror with all fluster test suite resources. "
        "By default it fills a local directory tree that can be served by any HTTP "
        "server (nginx, Apache, etc.). With --rgw-host/--bucket it instead uploads "
        "the resources to a radosgw (Ceph RGW) bucket. Either mirror can be used with: "
        "fluster download --mirror http://HOST/ROOT"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="mirror",
        help="output directory for the local mirror tree (default: ./mirror). Ignored when --rgw-host is set.",
    )
    parser.add_argument(
        "--rgw-host",
        default=None,
        help="IP or host of the radosgw endpoint (e.g. RGW_HOST or RGW_HOST:PORT). "
        "When set, resources are uploaded to a bucket instead of a local directory.",
    )
    parser.add_argument(
        "--bucket",
        default=None,
        help="name of the radosgw bucket to fill (e.g. BUCKET). Required when --rgw-host is set.",
    )
    parser.add_argument(
        "-t",
        "--test-suites-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "test_suites"),
        help="directory containing test suite JSON files",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="number of parallel downloads (default: 4)",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=2,
        help="number of retries per download (default: 2)",
    )
    args = parser.parse_args()

    if args.rgw_host and not args.bucket:
        sys.exit("--bucket is required when --rgw-host is set")

    test_suites_dir = os.path.abspath(args.test_suites_dir)

    if not os.path.isdir(test_suites_dir):
        sys.exit(f"Test suites directory not found: {test_suites_dir}")

    urls = collect_source_urls(test_suites_dir)
    if not urls:
        sys.exit(f"No source URLs found in {test_suites_dir}")

    print(f"Found {len(urls)} unique source URLs in {test_suites_dir}")

    if args.rgw_host:
        print(f"Uploading to radosgw bucket: {args.bucket} on {args.rgw_host}\n")
        worker = partial(_upload_one, rgw_host=args.rgw_host, bucket=args.bucket, retries=args.retries)
        sync_urls(urls, worker, args.jobs)
        mirror_url = _bucket_object_url(args.rgw_host, args.bucket, "").rstrip("/") + "/"
        print("\nDone. Use the bucket as a mirror with:")
        print(f"  fluster download --mirror {mirror_url}")
    else:
        output_dir = os.path.abspath(args.output)
        print(f"Mirror output directory: {output_dir}\n")
        os.makedirs(output_dir, exist_ok=True)
        worker = partial(_sync_one, output_dir=output_dir, retries=args.retries)
        sync_urls(urls, worker, args.jobs)
        print(f"\nDone. Serve {output_dir} with an HTTP server, e.g.:")
        print(f"  cd {output_dir} && python3 -m http.server 8080")
        print("Then use: fluster download --mirror http://<HOST>:8080/")


if __name__ == "__main__":
    main()
