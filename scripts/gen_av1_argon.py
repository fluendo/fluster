#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020-2024, Fluendo, S.A.
#  Author: Martin Cesarini <mcesarini@fluendo.com>, Fluendo, S.A.
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
import os
import re
import subprocess
import sys
import urllib.error
import zipfile
from time import sleep
from typing import Any, List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.decoders import av1_aom
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

ARGON_URL = "https://aom-cwg-av1-argon-streams-public.s3.us-east-1.amazonaws.com/"


class AV1ArgonGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        site: str,
        test_vector_groups: List[str],
        use_ffprobe: bool = False,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.site = site
        self.test_vector_groups = test_vector_groups
        self.use_ffprobe = use_ffprobe
        self.decoder = av1_aom.AV1AOMDecoder()
        if any(keyword in self.suite_name for keyword in ["CORE", "STRESS"]):
            self.decoder.annexb = True

    def generate(self, download: bool) -> None:
        """Generates the test suite and saves it to a file"""
        output_filepath = self.suite_name + ".json"
        absolute_dest_dir = os.path.dirname(os.path.abspath(__file__))
        extract_folder = os.path.join(absolute_dest_dir, "resources")
        test_suite = TestSuite(
            output_filepath,
            extract_folder,
            self.suite_name,
            self.codec,
            self.description,
            {},
        )
        os.makedirs(extract_folder, exist_ok=True)
        source_url = self.site + self.name
        source_checksum_ref_url = self.site + self.name + ".md5sum"

        # Download source checksum reference file
        try:
            utils.download(source_checksum_ref_url, extract_folder)
            source_checksum_ref = self._fill_checksum_argon(os.path.join(extract_folder, self.name + ".md5sum"))
        except urllib.error.URLError as url_error:
            raise Exception(
                f"\tUnable to download {source_checksum_ref_url} to {extract_folder}, {url_error}"
            ) from url_error
        except Exception as ex:
            raise Exception(f"{ex}") from ex

        # Calculate checksum of source file on disk
        try:
            source_checksum = utils.file_checksum(os.path.join(extract_folder, self.name))
        except Exception:
            source_checksum = ""

        # Download the zip file
        if download and source_checksum != source_checksum_ref:
            print(f"Downloading test suite archive from {source_url}")
            try:
                utils.download(source_url, extract_folder)
                source_checksum = utils.file_checksum(os.path.join(extract_folder, self.name))
            except urllib.error.URLError as url_error:
                raise Exception(f"\tUnable to download {source_url} to {extract_folder}, {url_error}") from url_error
            except Exception as ex:
                raise Exception(f"{ex}") from ex
        elif not download and source_checksum and source_checksum != source_checksum_ref:
            print(
                "WARNING: You have chosen not to download the source file. However the checksum of the source file "
                "on disk does not coincide with its reference checksum, indicating some kind of issue. Please enable "
                "download and execute the script again."
            )
            sleep(10)

        # Unzip the source file
        test_vector_files = []
        with zipfile.ZipFile(os.path.join(extract_folder, self.name), "r") as zip_ref:
            print(f"Unzipping test streams and checksums from {self.name}")
            for file_info in zip_ref.namelist():
                # Process test vector groups
                test_vector_group = file_info.split(os.path.sep)[1]
                if test_vector_group in self.test_vector_groups:
                    # Extract test vector files
                    if file_info.endswith(".obu"):
                        zip_ref.extract(file_info, extract_folder)
                        test_vector_files.append(file_info)

        # Create test vectors and test suite
        print(f"Creating test suite {test_suite.name}")
        for _, tv_rel_path in enumerate(test_vector_files):
            tv_filename = os.path.splitext(os.path.basename(tv_rel_path))[0]
            tv_abs_path = os.path.abspath(os.path.join(extract_folder, tv_rel_path))
            output_format = OutputFormat.UNKNOWN
            # ffprobe execution
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
                    tv_abs_path,
                ]

                try:
                    result = utils.run_command_with_output(command).splitlines()
                    pix_fmt = result[0]
                    output_format = OutputFormat[pix_fmt.upper()]
                    if output_format == OutputFormat.UNKNOWN:
                        raise KeyError
                except (subprocess.CalledProcessError, KeyError) as error:
                    exceptions_profile1_output_format = {
                        # Exceptions for profile 1 core (annex b) vectors
                        "test54": OutputFormat.GBRP10LE,
                        "test7497": OutputFormat.GBRP,
                        "test7508_7618": OutputFormat.GBRP,
                        "test7736": OutputFormat.GBRP,
                        "test7740": OutputFormat.GBRP10LE,
                        "test7750": OutputFormat.GBRP10LE,
                        "test7762": OutputFormat.GBRP,
                        "test7763": OutputFormat.GBRP,
                        # Exceptions for profile 1 non-annex b vectors
                        "test50": OutputFormat.GBRP10LE,
                        # Exceptions for profile 1 stress vectors
                        "test2678": OutputFormat.GBRP10LE,
                        "test58915": OutputFormat.GBRP10LE,
                        "test78511": OutputFormat.GBRP10LE,
                        "test90958": OutputFormat.GBRP10LE,
                        "test98100": OutputFormat.GBRP10LE,
                    }

                    exceptions_profile2_output_format = {
                        # Exceptions for profile 2 core (annex b) vectors
                        # All that appear as unknown in the list below contain frames of changing format
                        "test15599_12921": OutputFormat.UNKNOWN,
                        "test15641": OutputFormat.GBRP12LE,
                        "test15825": OutputFormat.GRAY,
                        "test16": OutputFormat.GRAY12LE,
                        "test16042": OutputFormat.GBRP12LE,
                        "test16049_16187_16181": OutputFormat.UNKNOWN,
                        "test16086": OutputFormat.GBRP12LE,
                        "test16101_16158_16169": OutputFormat.UNKNOWN,
                        "test16154_16099_16103": OutputFormat.UNKNOWN,
                        # Exceptions for profile 2 stress vectors
                        "test32592": OutputFormat.YUV422P10LE,
                        "test39250": OutputFormat.GBRP12LE,
                        "test70691": OutputFormat.YUV444P12LE,
                        "test85818": OutputFormat.YUV422P10LE,
                    }

                    if tv_filename in exceptions_profile1_output_format.keys():
                        output_format = exceptions_profile1_output_format[tv_filename]
                    elif tv_filename in exceptions_profile2_output_format.keys():
                        output_format = exceptions_profile2_output_format[tv_filename]
                    else:
                        raise error

            temp_output_ref = f"{os.path.splitext(tv_abs_path)[0]}.out"
            try:
                # Run libaom av1 decoder to get md5 checksum of expected output
                result_checksum = self.decoder.decode(tv_abs_path, temp_output_ref, output_format, 240, False, False)
                os.remove(temp_output_ref)
            except FileNotFoundError:
                print(f"File '{temp_output_ref}' not found.")
            except PermissionError:
                print(f"Permission denied to delete the file '{temp_output_ref}'.")
            except Exception as ex:
                if "error" in tv_abs_path.split(os.path.sep)[-3]:
                    result_checksum = ""
                else:
                    raise Exception(f"\tUnable to calculate md5 checksum of {tv_filename}, {ex}") from ex

            # Add data to the test vector and the test suite
            test_vector = TestVector(
                tv_filename,
                source_url,
                source_checksum,
                tv_rel_path,
                output_format,
                result_checksum,
            )
            test_suite.test_vectors[tv_filename] = test_vector

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_argon(dest_dir: str) -> Any:
        checksum_file = dest_dir
        if checksum_file is None:
            raise Exception("MD5 not found")
        with open(checksum_file, "r") as checksum_fh:
            regex = re.compile(r"\b([a-fA-F0-9]{32})\b")
            lines = checksum_fh.readlines()
            # Prefer lines matching the regex pattern
            match = next((regex.search(line) for line in lines if regex.search(line)), None)
            if match:
                result = match.group(1)[:32].lower()
            else:
                result = -1
            # Assert that we have extracted a valid MD5 from the file
            assert len(result) == 32 and re.search(r"^[a-fA-F0-9]{32}$", result) is not None, (
                f"{result} is not a valid MD5 hash"
            )
            return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-download",
        help="skip downloading zip",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE0-CORE-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile0 Core Annex B test suite",
        ARGON_URL,
        ["profile0_core", "profile0_core_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE0-NON-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile 0 Non-Annex B test suite",
        ARGON_URL,
        ["profile0_error", "profile0_not_annexb", "profile0_not_annexb_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE0-STRESS-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile0 Stress Annex B test suite",
        ARGON_URL,
        ["profile0_stress"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE1-CORE-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile1 Core Annex B test suite",
        ARGON_URL,
        ["profile1_core", "profile1_core_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE1-NON-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile 1 Non-Annex B test suite",
        ARGON_URL,
        ["profile1_error", "profile1_not_annexb", "profile1_not_annexb_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE1-STRESS-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile1 Stress Annex B test suite",
        ARGON_URL,
        ["profile1_stress"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE2-CORE-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile2 Core Annex B test suite",
        ARGON_URL,
        ["profile2_core", "profile2_core_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE2-NON-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile 2 Non-Annex B test suite",
        ARGON_URL,
        ["profile2_error", "profile2_not_annexb", "profile2_not_annexb_special"],
        True,
    )
    generator.generate(not args.skip_download)

    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1-ARGON-PROFILE2-STRESS-ANNEX-B",
        Codec.AV1,
        "AV1 Argon Profile2 Stress Annex B test suite",
        ARGON_URL,
        ["profile2_stress"],
        True,
    )
    generator.generate(not args.skip_download)
