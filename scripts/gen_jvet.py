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
from html.parser import HTMLParser
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

BASE_URL = "https://www.itu.int/"
H266_URL = BASE_URL + "wftp3/av-arch/jvet-site/bitstream_exchange/VVC/draft_conformance/"
BITSTREAM_EXTS = (
    ".bit",
)
MD5_EXTS = ("yuv_2.md5", "yuv.md5", ".md5", "md5.txt", "md5sum.txt")
MD5_EXCLUDES = (".bin.md5", "bit.md5")
RAW_EXTS = ("nogray.yuv", ".yuv", ".qcif")


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


class JVETGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        site: str,
        use_ffprobe: bool = False
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
            test_vector.source_checksum = utils.file_checksum(dest_path)
            if self.use_ffprobe:
                ffprobe = utils.normalize_binary_cmd('ffprobe')
                command = [ffprobe, '-v', 'error', '-select_streams', 'v:0',
                           '-show_entries', 'stream=pix_fmt', '-of',
                           'default=nokey=1:noprint_wrappers=1',
                           absolute_input_path]

                result = utils.run_command_with_output(command).splitlines()
                pix_fmt = result[0]
                try:
                    test_vector.output_format = OutputFormat[pix_fmt.upper()]
                except KeyError as e:
                    raise e

        test_suite.to_json_file(output_filepath)
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
    generator = JVETGenerator(
        'draft6',
        'JVET-VVC_draft6',
        Codec.H266,
        'JVET VVC draft6',
        H266_URL
    )
    generator.generate(not args.skip_download, args.jobs)
