#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020-2025, Fluendo, S.A.
#  Author: Ruben Sanchez Sanchez <rsanchez@fluendo.com>, Fluendo, S.A.
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
import multiprocessing
import os
import sys
import urllib
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://standards.iso.org/"
URL_MPEG2 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/Video/bitstreams/"
GZ_EXT = "gz"
GZ_EXCLUDES = [".trace.gz", ".log.gz", "ps.gz", ".TRACE.gz", ".rtf.gz", ".decoded.gz", "mpeg_target_practice.mpg.gz"]
BITSTREAM_EXTS = [
    ".bits",
    ".m2v",
    ".bit",
    ".mpeg",
    ".bs",
    ".new",
    ".stream16v2",
    ".long",
    ".4f",
    ".mpg",
    ".bin",
    "gi_stream",
    "bit_stream",
    ".BITS",
]


class HREFParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def error(self, message: str) -> None:
        print(message)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    if not value.startswith("javascript") and not value.startswith("mailto"):
                        full_url = urljoin(BASE_URL, value)
                        self.links.append(full_url)


class MPEG2VIDEOGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self, name: str, suite_name: str, codec: Codec, description: str, site: str, use_ffprobe: bool = False
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.site = site
        self.use_ffprobe = use_ffprobe

    def generate(self, download: bool, jobs: int) -> None:
        """Generates the test suite and downloads bitstreams"""
        absolute_dest_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_resources_dir = os.path.join(absolute_dest_dir, "resources", self.name)
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            absolute_resources_dir,
            self.suite_name,
            self.codec,
            self.description,
            {},
        )

        print(f"Download list of bitstreams from {self.site + self.name}")
        main_links = self.get_files_in_directory(self.site + self.name)

        for main_link in main_links:
            sub_directory_links = self.get_gz_files_in_directory(main_link)

            for file_url in sub_directory_links:
                file_url_basename = os.path.basename(file_url)
                name = os.path.splitext(file_url_basename)[0]
                file_input = f"{name}.bin"
                name = os.path.splitext(name)[0]
                if "bit_stream" in name or "conf4" in name:
                    parent_dir = os.path.basename(os.path.dirname(file_url))
                    name = f"{parent_dir}_{name}"
                test_vector = TestVector(name, file_url, "__skip__", file_input, OutputFormat.UNKNOWN, "")
                test_suite.test_vectors[name] = test_vector

        if download:
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        for test_vector in test_suite.test_vectors.values():
            dest_dir = os.path.join(test_suite.resources_dir, test_suite.name, test_vector.name)
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
            test_vector.input_file = str(utils.find_by_ext(dest_dir, BITSTREAM_EXTS))
            absolute_input_path = test_vector.input_file
            test_vector.input_file = test_vector.input_file.replace(
                os.path.join(test_suite.resources_dir, test_suite.name, test_vector.name) + os.sep,
                "",
            )
            if not test_vector.input_file:
                raise Exception(f"Bitstream file not found in {dest_dir}")
            test_vector.source_checksum = utils.file_checksum(dest_path)
            if self.use_ffprobe:
                ffprobe = utils.normalize_binary_cmd("ffprobe")
                command = [
                    ffprobe,
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=pix_fmt",
                    "-of",
                    "default=nokey=1:noprint_wrappers=1",
                    absolute_input_path,
                ]

                result = utils.run_command_with_output(command).splitlines()
                pix_fmt = result[0]
                try:
                    test_vector.output_format = OutputFormat[pix_fmt.upper()]
                except KeyError as key_err:
                    exceptions: Dict[str, OutputFormat] = {}
                    if test_vector.name in exceptions.keys():
                        test_vector.output_format = exceptions[test_vector.name]
                    else:
                        raise key_err

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def get_files_in_directory(directory_url: str) -> List[str]:
        """Find main directories"""
        hparser = HREFParser()
        with urllib.request.urlopen(directory_url) as resp:
            data = str(resp.read())

        hparser.feed(data)

        links: List[str] = []
        for link in hparser.links:
            if not link.endswith("/") and directory_url in link:
                links.append(link)

        return links

    @staticmethod
    def get_gz_files_in_directory(directory_url: str) -> List[str]:
        """Recursively fetches .gz files from subdirectories"""
        gz_links: List[str] = []
        links: List[str] = []

        hparser = HREFParser()
        with urllib.request.urlopen(directory_url) as resp:
            data = str(resp.read())
        hparser.feed(data)

        for link in hparser.links:
            if not link.endswith("/") and directory_url in link:
                links.append(link)

        for sub_link in links:
            full_url = urljoin(BASE_URL, sub_link)

            try:
                with urllib.request.urlopen(full_url) as resp:
                    sub_data = str(resp.read())

                sub_hparser = HREFParser()
                sub_hparser.feed(sub_data)

                for link in sub_hparser.links:
                    if link.endswith(GZ_EXT) and not any(link.endswith(ext) for ext in GZ_EXCLUDES):
                        gz_links.append(link)
            except Exception as e:
                print(f"Error accessing {full_url}: {e}")

        return gz_links


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-download",
        help="skip extracting tarball",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-j",
        "--jobs",
        help="number of parallel jobs to use. 2x logical cores by default",
        type=int,
        default=2 * multiprocessing.cpu_count(),
    )
    args = parser.parse_args()

    generator = MPEG2VIDEOGenerator(
        "422-profile",
        "MPEG2_VIDEO-422",
        Codec.MPEG2_VIDEO,
        "ISO IEC 13818-4 MPEG2 video 422 profile test suite",
        URL_MPEG2,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = MPEG2VIDEOGenerator(
        "main-profile",
        "MPEG2_VIDEO-MAIN",
        Codec.MPEG2_VIDEO,
        "ISO IEC 13818-4 MPEG2 video main profile test suite",
        URL_MPEG2,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
