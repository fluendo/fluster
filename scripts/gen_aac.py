#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2024, Fluendo, S.A.
#  Author: Michalis Dimopoulod <mdimopoulos@fluendo.com>, Fluendo, S.A.
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
import re
from html.parser import HTMLParser
from multiprocessing import Pool
import os
import sys
import urllib.request
import multiprocessing

# pylint: disable=wrong-import-position
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite, TestVector

# pylint: enable=wrong-import-position

BASE_URL = "https://standards.iso.org/"
URL_13818_ADTS = (
    BASE_URL
    + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/compressedAdts"
)
URL_13818_RAW = (
    BASE_URL
    + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/referencesWav"
)
URL_13818_RAW_CHECKSUMS = (
    BASE_URL
    + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/referencesWav/_checksum"
)

BITSTREAM_EXTS = [".adts"]
MD5_EXTS = [".wav.md5sum"]
MD5_EXCLUDES = []
RAW_EXTS = [".wav"]


class HREFParser(HTMLParser):
    """Custom parser to find href links"""

    def __init__(self):
        self.links = []
        super().__init__()

    def error(self, message):
        print(message)

    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            for name, value in attrs:
                # If href is defined, print it.
                if name == "href":
                    base_url = BASE_URL if BASE_URL[-1] != "/" else BASE_URL[0:-1]
                    self.links.append(base_url + value)


class AACGenerator:
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

    def generate(self, download, jobs):
        """Generates the test suite and saves it to a file"""
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            "resources",
            self.suite_name,
            self.codec,
            self.description,
            dict(),
        )

        hparser = HREFParser()
        print(f"Download list of compressed bitstreams from {self.site + self.name}")
        with urllib.request.urlopen(self.site + self.name) as resp:
            data = str(resp.read())
            hparser.feed(data)

        compressed_bitstream_links = [
            url for url in hparser.links if url.endswith(tuple(BITSTREAM_EXTS))
        ]

        for url in compressed_bitstream_links:
            filename = os.path.basename(url)
            test_vector_name = os.path.splitext(filename)[0]
            test_vector = TestVector(
                test_vector_name, url, "__skip__", filename, OutputFormat.UNKNOWN, ""
            )
            test_suite.test_vectors[test_vector_name] = test_vector

        # Download test suite input files
        if download:
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        # Download test suite output reference and md5 checksum files
        with Pool(jobs) as pool:

            def _callback_error(err):
                print(f"\nError downloading -> {err}\n")
                pool.terminate()

            downloads = []

            for test_vector in test_suite.test_vectors.values():
                print(f"Downloading output reference file for test vector {test_vector.name}")
                downloads.append(
                    pool.apply_async(
                        utils.download,
                        args=(
                            URL_13818_RAW + "/" + test_vector.name + RAW_EXTS[0],
                            os.path.join(
                                test_suite.resources_dir,
                                test_suite.name,
                                test_vector.name,
                            ),
                        ),
                        error_callback=_callback_error,
                    )
                )

                print(f"Downloading output reference checksum file for test vector {test_vector.name}")
                downloads.append(
                    pool.apply_async(
                        utils.download,
                        args=(
                            URL_13818_RAW_CHECKSUMS + "/" + test_vector.name + MD5_EXTS[0],
                            os.path.join(
                                test_suite.resources_dir,
                                test_suite.name,
                                test_vector.name,
                            ),
                        ),
                        error_callback=_callback_error,
                    )
                )
            pool.close()
            pool.join()

        for job in downloads:
            if not job.successful():
                sys.exit("Some download failed")

        for test_vector in test_suite.test_vectors.values():
            dest_dir = os.path.join(
                test_suite.resources_dir, test_suite.name, test_vector.name
            )
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))

            test_vector.input_file = utils.find_by_ext(dest_dir, BITSTREAM_EXTS)
            absolute_input_path = test_vector.input_file
            test_vector.input_file = test_vector.input_file.replace(
                os.path.join(
                    test_suite.resources_dir, test_suite.name, test_vector.name
                )
                + os.sep,
                "",
            )
            if not test_vector.input_file:
                raise Exception(f"Bitstream file not found in {dest_dir}")

            # Calculate source file checksum
            test_vector.source_checksum = utils.file_checksum(dest_path)

            # Extract sample format of input file using ffprobe
            if self.use_ffprobe:
                ffprobe = utils.normalize_binary_cmd("ffprobe")
                command = [
                    ffprobe,
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=sample_fmt",
                    "-of",
                    "default=nokey=1:noprint_wrappers=1",
                    absolute_input_path,
                ]

                sample_format = utils.run_command_with_output(command).splitlines()[0]
                try:
                    test_vector.output_format = OutputFormat[sample_format.upper()]
                except KeyError as key_err:
                    raise key_err

            # Read or calculate checksum of expected raw output
            self._fill_checksum_aac(test_vector, dest_dir)

        test_suite.to_json_file(output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_aac(test_vector, dest_dir):
        checksum_file = utils.find_by_ext(dest_dir, MD5_EXTS)
        if checksum_file is None:
            raise Exception("MD5 not found")
        with open(checksum_file, "r") as checksum_file:
            regex = re.compile(rf"([a-fA-F0-9]{{32,}}).*(?:\.(wav))?")
            lines = checksum_file.readlines()
            # Filter out empty lines
            filtered_lines = [line.strip() for line in lines if line.strip()]
            # Prefer lines matching the regex pattern
            match = next(
                (regex.match(line) for line in filtered_lines if regex.match(line)),
                None,
            )
            if match:
                test_vector.result = match.group(1).lower()
            # Assert that we have extracted a valid MD5 from the file
            assert (
                len(test_vector.result) == 32
                and re.search(r"^[a-fA-F0-9]{32}$", test_vector.result) is not None
            ), f"{test_vector.result} is not a valid MD5 hash"

        raw_file = utils.find_by_ext(dest_dir, RAW_EXTS)
        if raw_file is None or len(raw_file) == 0:
            raise Exception(f"RAW file not found in {dest_dir}")
        test_vector.result = utils.file_checksum(raw_file)


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

    generator = AACGenerator(
        "",
        "ISO_IEC_13818-4_2004",
        Codec.AAC,
        "ISO IEC 13814-4 AAC ADTS test suite",
        URL_13818_ADTS,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
