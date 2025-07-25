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
import urllib.request
from html.parser import HTMLParser
from typing import List, Optional, Tuple
from urllib.parse import urljoin

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://standards.iso.org/ittf/PubliclyAvailableStandards/"
RESOURCES = {
    "simple_profile_4_5": {
        "type": "directory",
        "url": BASE_URL + "c041491_ISO_IEC0_14496-4_2004_Amd_10_2005_Conformance_Testing/",
    },
    "profile_6": {"type": "direct", "url": BASE_URL + "c046298_ISOIEC_14496-4_2004_Amd_28_2008_bitstreams.zip"},
}
BITSTREAM_EXTS = [".bits", ".bit", ".m4v", ".cmp", ".tgz", ".zip"]


class HREFParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def error(self, message: str) -> None:
        pass

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    if not value.startswith("javascript") and not value.startswith("mailto"):
                        if value.startswith("http"):
                            full_url = value
                        else:
                            full_url = urljoin(BASE_URL, value)
                        self.links.append(full_url)


class MPEG4VIDEOGenerator:
    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        resources: List[str],
        use_ffprobe: bool = False,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.resources = resources
        self.use_ffprobe = use_ffprobe

    def generate(self, download: bool, jobs: int) -> None:
        absolute_dest_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_resources_dir = os.path.join(absolute_dest_dir, "resources", self.name)
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath, absolute_resources_dir, self.suite_name, self.codec, self.description, {}
        )

        for resource_name in self.resources:
            if resource_name not in RESOURCES:
                continue
            resource = RESOURCES[resource_name]
            if resource["type"] == "directory":
                files_found = self.get_files_in_directory(resource["url"])
                for file_url in files_found:
                    filename = os.path.basename(file_url)
                    if any(filename.lower().endswith(ext) for ext in BITSTREAM_EXTS):
                        name = os.path.splitext(filename)[0]
                        file_input = f"{name}.bin"
                        test_vector = TestVector(name, file_url, "__skip__", file_input, OutputFormat.UNKNOWN, "")
                        test_suite.test_vectors[name] = test_vector
            elif resource["type"] == "direct":
                filename = os.path.basename(resource["url"])
                name = os.path.splitext(filename)[0]
                file_input = f"{name}.bin"
                test_vector = TestVector(name, resource["url"], "__skip__", file_input, OutputFormat.UNKNOWN, "")
                test_suite.test_vectors[name] = test_vector

        if download:
            test_suite.download(
                jobs=jobs, out_dir=test_suite.resources_dir, verify=False, extract_all=True, keep_file=True
            )

        for test_vector in test_suite.test_vectors.values():
            dest_dir = os.path.join(test_suite.resources_dir, test_suite.name, test_vector.name)
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
            input_file_path = utils.find_by_ext(dest_dir, BITSTREAM_EXTS)
            if not input_file_path:
                continue
            absolute_input_path = input_file_path
            test_vector.input_file = input_file_path.replace(dest_dir + os.sep, "")
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
                if result:
                    pix_fmt = result[0]
                    try:
                        test_vector.output_format = OutputFormat[pix_fmt.upper()]
                    except KeyError:
                        pass

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)

    @staticmethod
    def get_files_in_directory(directory_url: str) -> List[str]:
        hparser = HREFParser()
        with urllib.request.urlopen(directory_url) as resp:
            data = resp.read().decode("utf-8")
        hparser.feed(data)
        links: List[str] = []
        for link in hparser.links:
            if directory_url in link:
                links.append(link)
        return links


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
    parser.add_argument(
        "--resources",
        nargs="+",
        default=["simple_profile_4_5"],
        choices=RESOURCES.keys(),
        help="resources to include in the test suite",
    )
    args = parser.parse_args()

    generator = MPEG4VIDEOGenerator(
        "simple_profile",
        "MPEG4_VIDEO-SimpleProfile",
        Codec.MPEG2_VIDEO,
        "ISO IEC 14496-4 MPEG4 video simple profile test suite",
        args.resources,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
