#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2024, Fluendo, S.A.
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
import re
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat, Profile
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://www.itu.int/"
H266_URL = BASE_URL + "wftp3/av-arch/jvet-site/bitstream_exchange/VVC/draft_conformance/"
# When there is only 1 element in below variables there must be a ", " at the end.
# Otherwise utils.find_by_ext() considers each character of the string as an individual
# element in the list
BITSTREAM_EXTS = [".bit"]
MD5_EXTS = [".yuv.md5"]


class HREFParser(HTMLParser):
    """Custom parser to find href links"""

    def __init__(self) -> None:
        self.links: List[Any] = []
        super().__init__()

    def error(self, message: str) -> None:
        print(message)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            for name, value in attrs:
                # If href is defined, print it.
                if name == "href":
                    base_url = BASE_URL if BASE_URL[-1] != "/" else BASE_URL[0:-1]
                    self.links.append(base_url + str(value))


class JVETGenerator:
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
        """Generates the test suite and saves it to a file"""
        absolute_dest_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_resources_dir = os.path.join(absolute_dest_dir, "resources")
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            absolute_resources_dir,
            self.suite_name,
            self.codec,
            self.description,
            {},
        )

        hparser = HREFParser()
        print(f"Download list of bitstreams from {self.site + self.name}")
        with urllib.request.urlopen(self.site + self.name) as resp:
            data = str(resp.read())
            hparser.feed(data)

        for url in hparser.links[1:]:
            file_url = os.path.basename(url)
            name = os.path.splitext(file_url)[0]
            file_input = f"{name}.bin"
            test_vector = TestVector(name, url, "__skip__", file_input, OutputFormat.YUV420P, "")
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
                    "-strict",
                    "-2",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=profile,pix_fmt",
                    "-of",
                    "default=nokey=1:noprint_wrappers=1",
                    absolute_input_path,
                ]

                result = utils.run_command_with_output(command).splitlines()
                profile = result[0]
                pix_fmt = result[1]
                try:
                    test_vector.output_format = OutputFormat[pix_fmt.upper()]
                    if test_vector.output_format == OutputFormat.UNKNOWN:
                        raise KeyError
                except KeyError as key_err:
                    # This information is deduced from other vectors with the same profile as this vector
                    exceptions_output_format = {"VPS_C_ERICSSON_1": OutputFormat.YUV420P10LE}
                    if test_vector.name in exceptions_output_format.keys():
                        test_vector.output_format = exceptions_output_format[test_vector.name]
                    else:
                        raise key_err
                try:
                    test_vector.profile = Profile[profile.translate(str.maketrans(" :", "__")).upper()]
                except KeyError as key_err:
                    # This information was deduced from mapping profile id number reported by ffprobe with profiles
                    # names found in the codec specification document https://www.itu.int/rec/T-REC-H.266-202309-S/en
                    exceptions_profile = {
                        "ILRPL_A_Huawei_2": Profile.MULTILAYER_MAIN_10,
                        "OLS_A_Tencent_4": Profile.MULTILAYER_MAIN_10,
                        "OLS_B_Tencent_4": Profile.MULTILAYER_MAIN_10,
                        "OLS_C_Tencent_4": Profile.MULTILAYER_MAIN_10,
                        "OPI_B_Nokia_2": Profile.MULTILAYER_MAIN_10,
                        "SPATSCAL444_A_Qualcomm_2": Profile.MULTILAYER_MAIN_10_4_4_4,
                        "SPATSCAL_A_Qualcomm_3": Profile.MULTILAYER_MAIN_10,
                        "STILL444_A_KDDI_1": Profile.MAIN_10_4_4_4_STILL_PICTURE,
                        "STILL_A_KDDI_1": Profile.MAIN_10_STILL_PICTURE,
                        "VPS_A_INTEL_3": Profile.MULTILAYER_MAIN_10,
                        "VPS_B_ERICSSON_1": Profile.MULTILAYER_MAIN_10,
                        "VPS_C_ERICSSON_1": Profile.MULTILAYER_MAIN_10,
                    }
                    if test_vector.name in exceptions_profile.keys():
                        test_vector.profile = exceptions_profile[test_vector.name]
                    else:
                        raise key_err

            self._fill_checksum_h266(test_vector, dest_dir)

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_h266(test_vector: TestVector, dest_dir: str) -> None:
        checksum_file = utils.find_by_ext(dest_dir, MD5_EXTS)
        if checksum_file is None:
            raise Exception("MD5 not found")
        with open(checksum_file, "r") as checksum_fh:
            regex = re.compile(r"([a-fA-F0-9]{32,}).*(?:\.(yuv|rgb|gbr))?")
            lines = checksum_fh.readlines()
            # Filter out empty lines
            filtered_lines = [line.strip() for line in lines if line.strip()]
            # Prefer lines matching the regex pattern
            match = next((regex.match(line) for line in filtered_lines if regex.match(line)), None)
            if match:
                test_vector.result = match.group(1).lower()
            # Assert that we have extracted a valid MD5 from the file
            assert len(test_vector.result) == 32 and re.search(r"^[a-fA-F0-9]{32}$", test_vector.result) is not None, (
                f"{test_vector.result} is not a valid MD5 hash"
            )


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
    generator = JVETGenerator(
        "draft6",
        "JVET-VVC_draft6",
        Codec.H266,
        "JVET VVC draft6",
        H266_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
