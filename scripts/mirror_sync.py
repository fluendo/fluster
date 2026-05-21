#!/usr/bin/env python3

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

import argparse
import json
import os
import sys
import urllib.parse

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


def sync_urls(urls: list[str], output_dir: str, jobs: int, retries: int) -> None:
    from multiprocessing import Pool

    def _sync_one(url: str) -> None:
        mirror_path = url_to_mirror_path(url)
        dest_dir = os.path.join(output_dir, os.path.dirname(mirror_path))
        dest_file = os.path.join(output_dir, mirror_path)

        if os.path.exists(dest_file):
            print(f"  SKIP (exists): {mirror_path}")
            return

        print(f"  DOWNLOAD: {mirror_path}")
        utils.download(url, dest_dir, max_retries=retries)

    if jobs <= 1:
        for url in urls:
            _sync_one(url)
    else:
        with Pool(jobs) as pool:
            pool.map(_sync_one, urls)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate a local mirror directory with all fluster test suite resources. "
        "The resulting directory can be served by any HTTP server (nginx, Apache, etc.) "
        "and used with: fluster download --mirror http://HOST/ROOT"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="mirror",
        help="output directory for the mirror tree (default: ./mirror)",
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

    test_suites_dir = os.path.abspath(args.test_suites_dir)
    output_dir = os.path.abspath(args.output)

    if not os.path.isdir(test_suites_dir):
        sys.exit(f"Test suites directory not found: {test_suites_dir}")

    urls = collect_source_urls(test_suites_dir)
    if not urls:
        sys.exit(f"No source URLs found in {test_suites_dir}")

    print(f"Found {len(urls)} unique source URLs in {test_suites_dir}")
    print(f"Mirror output directory: {output_dir}\n")

    os.makedirs(output_dir, exist_ok=True)
    sync_urls(urls, output_dir, args.jobs, args.retries)

    print(f"\nDone. Serve {output_dir} with an HTTP server, e.g.:")
    print(f"  cd {output_dir} && python3 -m http.server 8080")
    print("Then use: fluster download --mirror http://<HOST>:8080/")


if __name__ == "__main__":
    main()
