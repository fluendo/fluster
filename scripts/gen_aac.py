#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2024, Fluendo, S.A.
#  Author: Michalis Dimopoulos <mdimopoulos@fluendo.com>, Fluendo, S.A.
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
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://standards.iso.org/"

URL_MPEG2 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/"
URL_MPEG2_ADTS = URL_MPEG2 + "compressedAdts"
URL_MPEG2_ADIF = URL_MPEG2 + "compressedAdif"

URL_MPEG4 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_14496-26_2010_Bitstreams/"
URL_MPEG4_ADIF = URL_MPEG4 + "DVD1/mpeg4audio-conformance/compressedAdif/add-opt/"
URL_MPEG4_MP4 = URL_MPEG4 + "DVD1/mpeg4audio-conformance/compressedMp4/"
URL_MPEG4_ADTS = URL_MPEG4 + "DVD1/mpeg4audio-conformance/compressedAdts/add-opt/"

BITSTREAM_EXTS = [".adts", ".adif", ".mp4"]


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


class AACGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        url_test_vectors: str,
        use_ffprobe: bool = False,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.url_test_vectors = url_test_vectors
        self.use_ffprobe = use_ffprobe

    def generate(self, download: bool, jobs: int) -> None:
        """Generates the test suite and saves it to a file"""
        absolut_dest_dir = os.path.dirname(os.path.abspath(__file__))
        absolut_resources_dir = os.path.join(absolut_dest_dir, "resources")
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            absolut_resources_dir,
            self.suite_name,
            self.codec,
            self.description,
            {},
        )

        hparser_compressed = HREFParser()

        with urllib.request.urlopen(self.url_test_vectors) as resp:
            data = str(resp.read())
            hparser_compressed.feed(data)
        compressed_bitstream_links = [url for url in hparser_compressed.links if url.endswith(tuple(BITSTREAM_EXTS))]

        # Download compressed bitstream links
        for source_url in compressed_bitstream_links:
            input_filename = os.path.basename(source_url)
            test_vector_name = os.path.splitext(input_filename)[0]
            test_vector = TestVector(test_vector_name, source_url, "__skip__", input_filename, OutputFormat.UNKNOWN, "")
            test_suite.test_vectors[test_vector_name] = test_vector

        print(f"Download list of compressed bitstreams from {self.url_test_vectors}")
        if download:
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        # MPEG4_AAC-MP4 test suite
        if test_suite.name == "MPEG4_AAC-MP4":
            print(f"Identifying MP4 files that contain audio in test suite: {self.suite_name}")

            # Validating audio files using ffprobe
            ffprobe = utils.normalize_binary_cmd("ffprobe")
            non_audio_test_vectors = []
            for test_vector in test_suite.test_vectors.values():
                dest_dir = os.path.join(test_suite.resources_dir, test_suite.name, test_vector.name)
                absolute_path = os.path.join(os.getcwd(), dest_dir, test_vector.input_file)
                command = [
                    ffprobe,
                    "-loglevel",
                    "error",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "csv=p=0",
                    absolute_path,
                ]
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

                # In case of error, create a new test vector list to be removed from the test suite
                if result.returncode != 0:
                    non_audio_test_vectors.append(test_vector.name)
                else:
                    for line in result.stdout.split():
                        if line and "aac" not in line:
                            non_audio_test_vectors.append(test_vector.name)
                            break

            # Removing non audio files test vectors
            if non_audio_test_vectors:
                print("Removing non-audio files and folders from hard drive")
                for name in non_audio_test_vectors:
                    # Removing files and folders from hard drive
                    dest_dir = os.path.join(test_suite.resources_dir, test_suite.name, name)
                    absolute_path = os.path.join(os.getcwd(), dest_dir, name + ".mp4")
                    absolute_path_folder = os.path.join(os.getcwd(), dest_dir)

                    if os.path.exists(absolute_path):
                        try:
                            os.remove(absolute_path)
                        except OSError as error:
                            raise Exception(f"The file {absolute_path} couldn't be deleted.\n{error}")
                        try:
                            os.rmdir(absolute_path_folder)
                        except OSError as error:
                            raise Exception(f"The folder {absolute_path_folder} couldn't be deleted.\n{error}")

                    # Remove test vectors from test suite and the corresponding links
                    del test_suite.test_vectors[str(name)]

        for test_vector in test_suite.test_vectors.values():
            dest_dir = os.path.join(test_suite.resources_dir, test_suite.name, test_vector.name)
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
            absolute_input_path = os.path.join(os.getcwd(), dest_dir, test_vector.input_file)

            # Check that bitstream file is located inside the corresponding test vector folder
            if not os.path.isfile(absolute_input_path):
                raise Exception(f"Bitstream file {test_vector.input_file} not found in {dest_dir}")

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

        absolut_output_filepath = os.path.join(absolut_dest_dir, output_filepath)
        test_suite.to_json_file(absolut_output_filepath)
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

    generator = AACGenerator(
        "MPEG2_AAC-ADIF",
        "MPEG2_AAC-ADIF",
        Codec.AAC,
        "ISO IEC 13818-4 MPEG2 AAC ADIF test suite",
        URL_MPEG2_ADIF,
        False,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG2_AAC-ADTS",
        "MPEG2_AAC-ADTS",
        Codec.AAC,
        "ISO IEC 13818-4 MPEG2 AAC ADTS test suite",
        URL_MPEG2_ADTS,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG4_AAC-ADIF",
        "MPEG4_AAC-ADIF",
        Codec.AAC,
        "ISO IEC 14496-26 MPEG4 AAC ADIF test suite",
        URL_MPEG4_ADIF,
        False,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG4_AAC-MP4",
        "MPEG4_AAC-MP4",
        Codec.AAC,
        "ISO IEC 14496-26 MPEG4 AAC MP4 test suite",
        URL_MPEG4_MP4,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG4_AAC-ADTS",
        "MPEG4_AAC-ADTS",
        Codec.AAC,
        "ISO IEC 14496-26 MPEG4 AAC ADTS test suite",
        URL_MPEG4_ADTS,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
