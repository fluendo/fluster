#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020-2024, Fluendo, S.A.
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
import copy
import multiprocessing
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://www.itu.int/"
H264_URL = BASE_URL + "wftp3/av-arch/jvt-site/draft_conformance/"
BITSTREAM_EXTS = [".264", ".h264", ".jsv", ".jvt", ".avc", ".26l", ".bits"]
MD5_EXTS = ["yuv_2.md5", "yuv.md5", ".md5", "md5.txt", "md5sum.txt"]
MD5_EXCLUDES = [".bin.md5", "bit.md5"]
RAW_EXTS = ["nogray.yuv", ".yuv", ".YUV", ".qcif"]


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


class JVTGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        site: str,
        use_ffprobe: bool = False,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.site = site
        self.use_ffprobe = use_ffprobe

    def generate(self, download: bool, jobs: int) -> None:
        """Generates the test suite and saves it to a file"""
        new_test_vectors = []
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            "resources",
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
            # The first item in the AVCv1 list is a readme file
            if "00readme_H" in url:
                continue
            # MVC contains files marked as old, we want to skip those
            if "_old" in url:
                continue
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
                    exceptions = {
                        # All below test vectors from JVT-Professional_profiles_V1
                        # need to be analysed with respect to output format,
                        # for now it remains undetermined
                        "PPCV444I4_Mitsubishi_A": OutputFormat.NONE,
                        "PPCV444I5_Mitsubishi_A": OutputFormat.NONE,
                        "PPCV444I6_Mitsubishi_A": OutputFormat.NONE,
                        "PPCV444I7_SejongUniv_A": OutputFormat.NONE,
                        "PPH444I4_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444I5_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444I6_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444I7_SejongUniv_A": OutputFormat.NONE,
                        "PPH444P10_SejongUniv_A": OutputFormat.NONE,
                        "PPH444P6_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444P7_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444P8_Mitsubishi_A": OutputFormat.NONE,
                        "PPH444P9_Mitsubishi_A": OutputFormat.NONE,
                    }
                    if test_vector.name in exceptions.keys():
                        test_vector.output_format = exceptions[test_vector.name]
                    else:
                        raise key_err

            exceptions_checksum = [
                # Output checksum of all below test vectors from JVT-FRExt has to be calculated by means of
                # executing a run with the reference decoder, `fluster.py -f ...`
                "alphaconformanceG",  # Raw reference files are split streams and give false checksum value
                "FREH10-1",
                "FREH10-2",
                "Hi422FR1_SONY_A",
                "Hi422FR2_SONY_A",
                "Hi422FR3_SONY_A",
                "Hi422FR4_SONY_A",
                "Hi422FR6_SONY_A",
                "Hi422FR7_SONY_A",
                "Hi422FR8_SONY_A",
                "Hi422FR9_SONY_A",
                "Hi422FREXT16_SONY_A",
                "Hi422FREXT17_SONY_A",
                "Hi422FREXT18_SONY_A",
                "Hi422FREXT19_SONY_A",
            ]

            if test_vector.name in exceptions_checksum:
                continue

            if self.name not in (
                "Professional_profiles",
                "MVC",
            ):  # result md5 generated from h264_reference_decoder
                if self.name == "SVC":  # result md5 generated for different Lines (L0, L1...)
                    new_vectors = self._fill_checksum_h264_multiple(test_vector, dest_dir)
                    new_test_vectors.extend(new_vectors)
                    test_suite.test_vectors = {vector.name: vector for vector in new_test_vectors}
                else:
                    self._fill_checksum_h264(test_vector, dest_dir)

        test_suite.to_json_file(output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_h264(test_vector: TestVector, dest_dir: str) -> None:
        raw_file = utils.find_by_ext(dest_dir, RAW_EXTS)
        if raw_file is None or len(raw_file) == 0:
            raise Exception(f"RAW file not found in {dest_dir}")
        test_vector.result = utils.file_checksum(raw_file)

    @staticmethod
    def _fill_checksum_h264_multiple(test_vector: TestVector, dest_dir: str) -> List[TestVector]:
        def remove_r1_from_path(path: str) -> str:
            parts = path.split("/")
            if len(parts) >= 2:
                parts[-2] = re.sub(r"-r1", "", parts[-2])
                parts[-1] = re.sub(r"-r1", "", parts[-1])
            return "/".join(parts)

        multiple_test_vectors = []

        for suffix in [f"-L{i}" for i in range(8)]:  # L0 ... L7
            new_vector = copy.deepcopy(test_vector)
            new_vector.name = test_vector.name + suffix

            input_file_path = os.path.join(dest_dir, test_vector.name, f"{test_vector.name}{suffix}.264")
            result_file_path = os.path.join(dest_dir, test_vector.name, f"{test_vector.name}{suffix}.yuv")

            corrected_input_path = remove_r1_from_path(input_file_path)
            corrected_result_path = remove_r1_from_path(result_file_path)

            if os.path.exists(corrected_input_path) and os.path.exists(corrected_result_path):
                new_vector.input_file = os.path.relpath(corrected_input_path, dest_dir)
                new_vector.result = utils.file_checksum(corrected_result_path)

                multiple_test_vectors.append(new_vector)

        return multiple_test_vectors


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

    generator = JVTGenerator(
        "AVCv1",
        "JVT-AVC_V1",
        Codec.H264,
        "JVT Advanced Video Coding v1 test suite",
        H264_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JVTGenerator(
        "FRExt",
        "JVT-FR-EXT",
        Codec.H264,
        "JVT Fidelity Range Extension test suite",
        H264_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JVTGenerator(
        "MVC",
        "JVT-MVC",
        Codec.H264,
        "JVT Multiview Video Coding test suite",
        H264_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JVTGenerator(
        "Professional_profiles",
        "JVT-Professional_profiles_V1",
        Codec.H264,
        "JVT Professional Profiles test suite",
        H264_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JVTGenerator(
        "SVC",
        "JVT-SVC_V1",
        Codec.H264,
        "JVT Scalable Video Coding test suite",
        H264_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
