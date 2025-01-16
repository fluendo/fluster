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
import re
import sys
from typing import Any, Optional, Tuple  # noqa: F401

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.decoders import av1_aom
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

DOWNLOAD_URL = "https://storage.googleapis.com/chromiumos-test-assets-public/tast/cros/video/test_vectors/av1"

TESTS_8BPP = (
    # 8 bit
    "00000527_20210205.ivf",
    "00000535_20210205.ivf",
    "00000548_20201006.ivf",
    "48_delayed_20201006.ivf",
    "av1-1-b8-02-allintra_20201006.ivf",
    "av1-1-b8-03-sizeup_20201006.ivf",
    "av1-1-b8-23-film_grain-50_20201006.ivf",
    "ccvb_film_grain_20201006.ivf",
    "frames_refs_short_signaling_20201006.ivf",
    "non_uniform_tiling_20201006.ivf",
    "test-25fps-192x288-only-tile-cols-is-power-of-2_20210111.ivf",
    "test-25fps-192x288-only-tile-rows-is-power-of-2_20210111.ivf",
    "test-25fps-192x288-tile-rows-3-tile-cols-3_20210111.ivf",
)

TESTS_10BPP = (
    # 10 bit
    "00000671_20210310.ivf",
    "00000672_20210310.ivf",
    "00000673_20210310.ivf",
    "00000674_20210310.ivf",
    "00000675_20210310.ivf",
    "00000716_20210310.ivf",
    "00000717_20210310.ivf",
    "00000718_20210310.ivf",
    "00000719_20210310.ivf",
    "00000720_20210310.ivf",
    "00000761_20210310.ivf",
    "00000762_20210310.ivf",
    "00000763_20210310.ivf",
    "00000764_20210310.ivf",
    "00000765_20210310.ivf",
    "av1-1-b10-00-quantizer-00_20210310.ivf",
    "av1-1-b10-00-quantizer-10_20210310.ivf",
    "av1-1-b10-00-quantizer-20_20210310.ivf",
    "av1-1-b10-00-quantizer-30_20210310.ivf",
    "av1-1-b10-00-quantizer-40_20210310.ivf",
    "av1-1-b10-00-quantizer-50_20210310.ivf",
    "av1-1-b10-00-quantizer-60_20210310.ivf",
    "av1-1-b10-23-film_grain-50_20210310.ivf",
)


class ChromiumAV1Generator:
    """Generates a test suite from the conformance bitstreams used in tast tests for Chromium"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        bpp: int,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.decoder = av1_aom.AV1AOMDecoder()
        self.bpp = bpp

    def generate(self, download: bool, jobs: int) -> Any:
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

        print(f"Download list of bitstreams from {DOWNLOAD_URL}")

        tests: Optional[Tuple[str, ...]]
        if self.bpp == 10:
            tests = TESTS_10BPP
        elif self.bpp == 8:
            tests = TESTS_8BPP
        else:
            return

        for test in tests:
            file_url = f"{DOWNLOAD_URL}/{test}"
            name = re.sub(r"_[\d]*", "", test)

            test_vector = TestVector(
                name, file_url, "__skip__", test, OutputFormat.YUV420P, ""
            )

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
            test_vector.input_file = dest_path.replace(
                os.path.join(
                    test_suite.resources_dir, test_suite.name, test_vector.name
                )
                + os.sep,
                "",
            )

            if not test_vector.input_file:
                raise Exception(f"Bitstream file not found in {dest_dir}")
            test_vector.source_checksum = utils.file_checksum(dest_path)
            out420 = f"{dest_path}.i420"
            # Run the libaom av1 decoder to get the checksum as the .md5 in the JSONs are per-frame
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
    generator = ChromiumAV1Generator(
        "chromium-AV1-8bit",
        "CHROMIUM-8bit-AV1-TEST-VECTORS",
        Codec.AV1,
        "AV1 Test Vector Catalogue from https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/tast-tests/src/chromiumos/tast/local/bundles/cros/video/data/test_vectors/av1/",
        8,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = ChromiumAV1Generator(
        "chromium-AV1-10bit",
        "CHROMIUM-10bit-AV1-TEST-VECTORS",
        Codec.AV1,
        "AV1 Test Vector Catalogue from https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/tast-tests/src/chromiumos/tast/local/bundles/cros/video/data/test_vectors/av1/",
        10,
    )
    generator.generate(not args.skip_download, args.jobs)
