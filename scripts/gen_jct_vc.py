#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
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
import re

# pylint: disable=wrong-import-position
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite, TestVector

# pylint: enable=wrong-import-position

BASE_URL = "https://www.itu.int/"
H266_URL = BASE_URL + "wftp3/av-arch/jvet-site/bitstream_exchange/VVC/draft_conformance/"
H265_URL = BASE_URL + "wftp3/av-arch/jctvc-site/bitstream_exchange/draft_conformance/"
H264_URL = BASE_URL + "wftp3/av-arch/jvt-site/draft_conformance/"
BITSTREAM_EXTS = (
    ".bin",
    ".bit",
    ".264",
    ".h264",
    ".jvc",
    ".jsv",
    ".jvt",
    ".avc",
    ".26l",
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


class JCTVTGenerator:
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
            # The first item in the AVCv1 list is a readme file
            if "00readme_H" in url:
                continue
            elif "replaced" in url:
                # This is in HEVC-SHVC, we don't want that.
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
            dest_dir = os.path.join(
                test_suite.resources_dir, test_suite.name, test_vector.name
            )
            dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
            test_vector.input_file = self._find_by_ext(dest_dir, BITSTREAM_EXTS)
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
            if "main10" in test_vector.name.lower():
                test_vector.output_format = OutputFormat.YUV420P10LE
            elif self.use_ffprobe:
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
                    exceptions = {
                        # Feature: Test unequal luma and chroma bitdepth
                        # setting. The luma bitdepth is higher than the chroma
                        # bitdepth. Luma is 12bit, chroma is 8bit. Considering
                        # 12bit.
                        "Bitdepth_A_RExt_Sony_1": OutputFormat.YUV444P12LE,
                        # Same as above, but the chroma is 12bit and luma is 8bit.
                        "Bitdepth_B_RExt_Sony_1": OutputFormat.YUV444P12LE,
                        # Rest is taken by examining the error displayed by ffprobe, e.g.:
                        # The following bit-depths are currently specified: 8,
                        # 9, 10 and 12 bits, chroma_format_idc is 3, depth is 16
                        "EXTPREC_MAIN_444_16_INTRA_10BIT_RExt_Sony_1": OutputFormat.YUV444P16LE,
                        "EXTPREC_HIGHTHROUGHPUT_444_16_INTRA_16BIT_RExt_Sony_1": OutputFormat.YUV444P16LE,
                        "EXTPREC_MAIN_444_16_INTRA_16BIT_RExt_Sony_1": OutputFormat.YUV444P16LE,
                        "GENERAL_16b_400_RExt_Sony_1" : OutputFormat.GRAY16LE,
                        "GENERAL_16b_444_highThroughput_RExt_Sony_2" : OutputFormat.YUV444P16LE,
                        "GENERAL_16b_444_RExt_Sony_2": OutputFormat.YUV444P16LE,
                        "WAVETILES_RExt_Sony_2" : OutputFormat.YUV444P16LE
                    }
                    if test_vector.name in exceptions.keys():
                        test_vector.output_format = exceptions[test_vector.name]
                    else:
                        raise e


            if self.codec == Codec.H265:
                self._fill_checksum_h265(test_vector, dest_dir)
            elif self.codec == Codec.H264:
                self._fill_checksum_h264(test_vector, dest_dir)

        test_suite.to_json_file(output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    def _fill_checksum_h264(self, test_vector, dest_dir):
        raw_file = self._find_by_ext(dest_dir, RAW_EXTS)
        if raw_file is None:
            raise Exception(f"RAW file not found in {dest_dir}")
        test_vector.result = utils.file_checksum(raw_file)

    def _fill_checksum_h265(self, test_vector, dest_dir):
        checksum_file = self._find_by_ext(dest_dir, MD5_EXTS, MD5_EXCLUDES)
        if checksum_file is None:
            raise Exception("MD5 not found")
        with open(checksum_file, "r") as checksum_file:
            # The md5 is in several formats
            # Example 1
            # 158312a1a35ef4b20cb4aeee48549c03 *WP_A_Toshiba_3.bit
            # Example 2
            # MD5 (rec.yuv) = e5c4c20a8871aa446a344efb1755bcf9
            # Example 3
            # # MD5 checksums generated by MD5summer (http://www.md5summer.org)
            # # Generated 6/14/2013 4:22:11 PM
            # 29799285628de148502da666a7fc2df5 *DBLK_F_VIXS_1.bit
            # Example 4:
            # cd84e70999e4577f23eb2077c7a1d24f  EXTPREC_HIGHTHROUGHPUT_444_16_INTRA_8BIT_RExt_Sony_1_rec.yuv
            # 812d62fa8566d51544e760fd9ecbe138  EXTPREC_HIGHTHROUGHPUT_444_16_INTRA_8BIT_RExt_Sony_1.bit
            # Example 5 (extra 4 bits at the end, possible typo?)
            # 580e4041563c9cca6c30d0b6c09571aef *Slice_ACT_QP_Offsets_A_Qualcomm_2.bit
            # 2d4ffc0354dee7216567c89dc1f20391 *Slice_ACT_QP_Offsets_A_Qualcomm_2.rgb
            # Example 6:
            # 9cab6bcd74491062a8523b5a7ff6a540  CCP_8bit_RExt_QCOM.bin
            # f3e914fccdb820eac85f46642ea0e168  CCP_8bit_RExt_QCOM.gbr
            regex = re.compile(rf"([a-fA-F0-9]{{32,}}).*\.(yuv|rgb|gbr)")
            lines = checksum_file.readlines()
            # If we have a line like examples 4,5,6 anywhere in the file, prefer
            # that.
            if self.codec == Codec.H265 and any((match := regex.match(line)) for line in lines):
                test_vector.result = match.group(1)[:32].lower()
            elif self.codec == Codec.H265 and self.name == "RExt" or self.name == "MV-HEVC" or self.name == "SCC":
                # If we can't match with the regex, note that these usually come
                # with the checksum at the end
                test_vector.result = lines[-1].split(" ")[0].split("\n")[0].lower()
            else:
                for line in lines:
                    if line.startswith(("#", "\n")):
                        continue
                    if "=" in line:
                        test_vector.result = line.split("=")[-1].strip().lower()
                    else:
                        test_vector.result = line.split(" ")[0].split("\n")[0].lower()
                    break
            # Assert that we have extracted a valid MD5 from the file
            assert len(test_vector.result) == 32 and re.search(
                r"^[a-fA-F0-9]{32}$", test_vector.result) != None, f"{test_vector.result} is not a valid MD5 hash"

    def _find_by_ext(self, dest_dir, exts, excludes=None):
        excludes = excludes or []

        # Respect the priority for extensions
        for ext in exts:
            for subdir, _, files in os.walk(dest_dir):
                for filename in files:
                    excluded = False
                    filepath = subdir + os.sep + filename
                    if not filepath.endswith(ext) or "__MACOSX" in filepath:
                        continue
                    for excl in excludes:
                        if excl in filepath:
                            excluded = True
                            break
                    if not excluded:
                        return filepath
        return None


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
    generator = JCTVTGenerator(
        "HEVC_v1",
        "JCT-VC-HEVC_V1",
        Codec.H265,
        "JCT-VC HEVC version 1",
        H265_URL,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JCTVTGenerator(
        "RExt",
        "JCT-VC-RExt",
        Codec.H265,
        "JCT-VC HEVC Range Extension",
        H265_URL,
        True
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JCTVTGenerator(
        "SCC",
        "JCT-VC-SCC",
        Codec.H265,
        "JCT-VC HEVC Screen Content Coding Extension",
        H265_URL,
        True
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JCTVTGenerator(
        "MV-HEVC",
        "JCT-VC-MV-HEVC",
        Codec.H265,
        "JCT-VC HEVC Multiview Extension",
        H265_URL,
        True
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JCTVTGenerator(
        "AVCv1", "JVT-AVC_V1", Codec.H264, "JVT AVC version 1", H264_URL
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = JCTVTGenerator('draft6', 'JVET-VVC_draft6', Codec.H266,
                               'JVET VVC draft6', H266_URL)
    generator.generate(not args.skip_download, args.jobs)
