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
from typing import Any

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

ARGON_URL = "https://storage.googleapis.com/downloads.aomedia.org/assets/zip/"


class AV1ArgonGenerator:
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
        self.is_single_archive = True

    def generate(self, download: bool) -> None:
        """Generates the test suite and saves it to a file"""
        output_filepath = os.path.join(self.suite_name + ".json")
        extract_folder = "resources"
        test_suite = TestSuite(
            output_filepath,
            extract_folder,
            self.suite_name,
            self.codec,
            self.description,
            {},
            self.is_single_archive,
        )
        os.makedirs(extract_folder, exist_ok=True)
        # Download the zip file
        source_url = self.site + self.name
        if download:
            print(f"Download test suite archive from {source_url}")
            try:
                utils.download(source_url, extract_folder)
            except urllib.error.URLError as ex:
                exception_str = str(ex)
                print(f"\tUnable to download {source_url} to {extract_folder}, {exception_str}")
            except Exception as ex:
                raise Exception(str(ex)) from ex

        # Unzip the file
        test_vector_files = []
        with zipfile.ZipFile(extract_folder + "/" + self.name, "r") as zip_ref:
            print(f"Unzip files from {self.name}")
            for file_info in zip_ref.namelist():
                # Extract test vector files
                if file_info.endswith(".obu"):
                    zip_ref.extract(file_info, extract_folder)
                    test_vector_files.append(file_info)

                # Extract md5 files
                if file_info.endswith(".md5") and "md5_ref/" in file_info and "layers/" not in file_info:
                    zip_ref.extract(file_info, extract_folder)

        # Create test vectors and test suite
        print("Creating test vectors and test suite")
        source_checksum = utils.file_checksum(extract_folder + "/" + self.name)
        for idx, file in enumerate(test_vector_files):
            if (idx+1) % 500 == 0:
                print("Processing vector {} out of a total of {}".format(idx+1, len(test_vector_files)))
            filename = os.path.splitext(os.path.basename(file))[0]
            # ffprobe execution
            if self.use_ffprobe:
                full_path = os.path.abspath(extract_folder + "/" + file)
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
                    full_path,
                ]
                try:
                    result = utils.run_command_with_output(command).splitlines()
                    pix_fmt = result[0]
                    if pix_fmt == "unknown":
                        pix_fmt = "Unknown"
                except subprocess.CalledProcessError:
                    pix_fmt = "None"

            # Processing md5 files
            md5_file_to_find = os.path.splitext(filename)[0] + ".md5"
            full_path_split = full_path.split("/")
            md5_directory_path = "/".join(full_path_split[: len(full_path_split) - 2]) + "/" + "md5_ref"
            md5_file_path = os.path.join(md5_directory_path, md5_file_to_find)

            # Check the .md5 file and get checksum
            if os.path.exists(md5_file_path):
                try:
                    result_checksum = self._fill_checksum_argon(md5_file_path)
                except Exception as ex:
                    print("MD5 does not match")
                    raise ex
            else:
                try:
                    result_checksum = utils.file_checksum(full_path)
                except Exception as ex:
                    print("MD5 cannot be calculated")
                    raise ex

            # Add data to the test vector and the test suite
            test_vector = TestVector(
                filename,
                source_url,
                source_checksum,
                file,
                OutputFormat[pix_fmt.upper()],
                result_checksum,
            )
            test_suite.test_vectors[filename] = test_vector

        test_suite.to_json_file(output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_argon(dest_dir: str) -> Any:
        checksum_file = dest_dir
        if checksum_file is None:
            raise Exception("MD5 not found")
        with open(checksum_file, "r") as checksum_fh:
            regex = re.compile(r"([a-fA-F0-9]{32,}).*\.(yuv|rgb|gbr)")
            lines = checksum_fh.readlines()
            # Prefer lines matching the regex pattern
            match = next((regex.match(line) for line in lines if regex.match(line)), None)
            if match:
                result = match.group(1)[:32].lower()
            else:
                result = -1
            # Assert that we have extracted a valid MD5 from the file
            assert (
                len(result) == 32 and re.search(r"^[a-fA-F0-9]{32}$", result) is not None
            ), f"{result} is not a valid MD5 hash"
            return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-download",
        help="skip extracting tarball",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    generator = AV1ArgonGenerator(
        "argon_coveragetool_av1_base_and_extended_profiles_v2.1.1.zip",
        "AV1_ARGON_VECTORS",
        Codec.AV1,
        "AV1 Argon Streams",
        ARGON_URL,
        True,
    )
    generator.generate(not args.skip_download)
