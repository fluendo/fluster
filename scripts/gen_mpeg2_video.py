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
from typing import Dict, List, cast

import requests
from bs4 import BeautifulSoup, Tag

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://standards.iso.org/"
URL_MPEG2 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/Video/bitstreams/"
GZ_EXT = "gz"
GZ_EXCLUDES = [".trace.gz", ".log.gz", "ps.gz", ".TRACE.gz", ".rtf.gz", ".decoded.gz"]
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
RAW_EXTS = [".yuv"]


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
    def _fill_checksum(test_vector: TestVector, dest_dir: str) -> None:
        raw_file = utils.find_by_ext(dest_dir, RAW_EXTS)
        if raw_file is None or len(raw_file) == 0:
            raise Exception(f"RAW file not found in {dest_dir}")
        test_vector.result = utils.file_checksum(raw_file)

    @staticmethod
    def get_files_in_directory(directory_url: str) -> List[str]:
        """Find main directories"""
        response = requests.get(directory_url)
        soup = BeautifulSoup(response.content, "html.parser")

        links: List[str] = []
        for link in soup.find_all("a", href=True):
            if isinstance(link, Tag):
                href = cast(str, link["href"])
                if isinstance(href, str) and not href.endswith("/"):
                    links.append(BASE_URL + href)

        return links

    @staticmethod
    def get_gz_files_in_directory(directory_url: str) -> List[str]:
        """Recursively fetches files from subdirectories"""
        gz_links: List[str] = []
        links: List[str] = []
        response = requests.get(directory_url)
        soup = BeautifulSoup(response.content, "html.parser")

        for link in soup.find_all("a", href=True):
            if isinstance(link, Tag):
                href = cast(str, link["href"])
                if isinstance(href, str) and not href.endswith("/"):
                    links.append(BASE_URL + href)

        for sub_link in links:
            if isinstance(sub_link, str):
                response = requests.get(sub_link)
                sub_soup = BeautifulSoup(response.content, "html.parser")

                for td in sub_soup.find_all("td", {"data-sort": True}):
                    if isinstance(td, Tag):
                        anchor = td.find("a", href=True)
                        if anchor and isinstance(anchor, Tag):
                            href = cast(str, anchor["href"])
                            if (
                                isinstance(href, str)
                                and href.endswith(GZ_EXT)
                                and not any(href.endswith(ext) for ext in GZ_EXCLUDES)
                            ):
                                gz_links.append(f"{BASE_URL}{href.lstrip('/')}")

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
        "MPEG2-VIDEO-422",
        Codec.MPEG2_VIDEO,
        "ISO IEC 13818-4 MPEG2 video 422 profile test suite",
        URL_MPEG2,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = MPEG2VIDEOGenerator(
        "main-profile",
        "MPEG2-VIDEO-MAIN",
        Codec.MPEG2_VIDEO,
        "ISO IEC 13818-4 MPEG2 video main profile test suite",
        URL_MPEG2,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
