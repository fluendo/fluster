#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
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
import xml.etree.ElementTree as ET
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.decoders import av1_aom
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

# Sourced from test/test_data_download_worker.cmake
AV1_URL = "https://storage.googleapis.com/aom-test-data"

# Sourced from test/test_vector_test.cc
BITSTREAM_EXTS = [".ivf", ".webm", ".mkv"]


class AOMGenerator:
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
        self.decoder = av1_aom.AV1AOMDecoder()

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

        print(f"Download list of bitstreams from {self.site + self.name}")
        opener = urllib.request.build_opener()
        root = ET.parse(opener.open(self.site)).getroot()
        opener.close()

        for entry in root.findall("{*}Contents"):
            if "Contents" not in entry.tag:
                continue
            key_element = entry.find("{*}Key")
            if isinstance(key_element, ET.Element) and isinstance(
                key_element.text, str
            ):
                test_vector_filename = key_element.text
                test_vector_name = os.path.splitext(test_vector_filename)[0]
                if (
                    os.path.splitext(test_vector_filename)[1] not in BITSTREAM_EXTS
                    or "invalid" in test_vector_filename
                ):
                    continue
                file_url = f"{AV1_URL}/{key_element.text}"
                test_vector = TestVector(
                    test_vector_name,
                    file_url,
                    "__skip__",
                    test_vector_filename,
                    OutputFormat.YUV420P,
                    "",
                )
                test_suite.test_vectors[test_vector_name] = test_vector

        if download:
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        for test_vector in test_suite.test_vectors.values():
            dest_dir = os.path.join(
                test_suite.resources_dir, test_suite.name, test_vector.name
            )
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
            test_vector.input_file = dest_path.replace(
                os.path.join(
                    test_suite.resources_dir, test_suite.name, test_vector.name
                )
                + os.sep,
                "",
            )
            absolute_input_path = str(utils.find_by_ext(dest_dir, BITSTREAM_EXTS))

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

            out420 = f"{dest_path}.i420"
            # Run the libaom av1 decoder to get the checksum as the .md5 files are per-frame
            test_vector.result = self.decoder.decode(
                dest_path, out420, test_vector.output_format, 30, False, False
            )
            os.remove(out420)

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")


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
    generator = AOMGenerator(
        "libaom-AV1",
        "AV1-TEST-VECTORS",
        Codec.AV1,
        "AV1 Test Vector Catalogue from https://storage.googleapis.com/aom-test-data",
        AV1_URL,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
