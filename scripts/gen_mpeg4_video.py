#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2020-2025, Fluendo, S.A.
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
import sys
from html.parser import HTMLParser
from typing import List, Optional, Tuple
from urllib.parse import urljoin

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat, Profile
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVector
from fluster.utils import create_enhanced_opener

BASE_URL = "https://standards.iso.org/ittf/PubliclyAvailableStandards/"
RESOURCES = {
    "simple_profile_4_5": {
        "type": "directory",
        "url": BASE_URL + "c041491_ISO_IEC0_14496-4_2004_Amd_10_2005_Conformance_Testing/",
    },
    "simple_profile_6": {"type": "direct", "url": BASE_URL + "c046298_ISOIEC_14496-4_2004_Amd_28_2008_bitstreams.zip"},
    "advanced_simple_profile": {
        "type": "direct",
        "url": BASE_URL + "c041935_ISO_IEC_14496-4_2004_Amd_1_2005_Cor_1_2005_Bitstreams.zip",
    },
    "advanced+studio_simple_profile": {
        "type": "direct",
        "url": BASE_URL + "C051232_ISO_IEC_14496_4_2004_Amd_1_2005_Cor_2_2008_bitstreams.zip",
    },
    "simple_studio_profile": {
        "type": "directory",
        "url": BASE_URL + "ISO_IEC_14496-4_2004_Amd_35_2009_Bitstreams/",
    },
    "simple_scalable_profile": {
        "type": "direct",
        "url": BASE_URL + "C039391_ISO_IEC_14496-4_2004_Amd_5_2005_Bitstreams.zip",
    },
}
BITSTREAM_EXTS = [".bits", ".bit", ".m4v", ".cmp", ".tgz", ".zip"]


class HREFParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def error(self, message: str) -> None:
        pass

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    if not value.startswith("javascript") and not value.startswith("mailto"):
                        if value.startswith("http"):
                            full_url = value
                        else:
                            full_url = urljoin(BASE_URL, value)
                        self.links.append(full_url)


class MPEG4VIDEOGenerator:
    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        resources: List[str],
        use_ffprobe: bool = False,
        test_method: TestMethod = TestMethod.PIXEL,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.resources = resources
        self.use_ffprobe = use_ffprobe
        self.test_method = test_method

    def generate(self, download: bool, jobs: int) -> None:
        absolute_dest_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_resources_dir = os.path.join(absolute_dest_dir, "resources", self.name)
        output_filepath = os.path.join(self.suite_name + ".json")
        test_suite = TestSuite(
            output_filepath,
            absolute_resources_dir,
            self.suite_name,
            self.codec,
            self.description,
            {},
            test_method=self.test_method,
        )

        for resource_name in self.resources:
            resource = RESOURCES.get(resource_name)
            if not resource:
                continue
            urls = []
            if resource["type"] == "directory":
                urls = self.get_files_in_directory(resource["url"])
            elif resource["type"] == "direct":
                urls = [resource["url"]]
            for file_url in urls:
                filename = os.path.basename(file_url)
                if resource["type"] == "direct" or any(filename.lower().endswith(ext) for ext in BITSTREAM_EXTS):
                    name = os.path.splitext(filename)[0]
                    file_input = f"{name}.bin"
                    test_vector = TestVector(name, file_url, "__skip__", file_input, OutputFormat.UNKNOWN, "")
                    test_suite.test_vectors[name] = test_vector

        if download:
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        original_vectors = {
            name: {"source": vector.source, "source_checksum": vector.source_checksum}
            for name, vector in test_suite.test_vectors.items()
        }

        test_suite.test_vectors = {}

        suite_dir = os.path.join(test_suite.resources_dir, test_suite.name)
        if os.path.exists(suite_dir):
            for root, _, files in os.walk(suite_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in BITSTREAM_EXTS) and not file.lower().endswith(
                        (".tgz", ".zip")
                    ):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, suite_dir)
                        name = os.path.splitext(file)[0]

                        if not self.should_include_file(rel_path, self.name, file):
                            continue

                        # Find original vector info
                        orig_info = next(
                            (info for orig_name, info in original_vectors.items() if orig_name in rel_path),
                            {"source": "", "source_checksum": ""},
                        )

                        # Clean up path: remove duplicate folders or root archive folders
                        path_parts = rel_path.split(os.sep)
                        if len(path_parts) >= 2 and (
                            path_parts[0] == path_parts[1]  # Duplicate folders
                            or any(
                                path_parts[0].lower() in os.path.basename(info.get("source", "")).lower()
                                for info in original_vectors.values()
                                if info.get("source")
                            )
                        ):
                            rel_path = os.sep.join(path_parts[1:])

                        test_vector = TestVector(
                            name, orig_info["source"], orig_info["source_checksum"], rel_path, OutputFormat.UNKNOWN, ""
                        )

                        if self.use_ffprobe and not any(
                            full_path.lower().endswith(ext) for ext in [".zip", ".tgz", ".tar.gz"]
                        ):
                            try:
                                ffprobe = utils.normalize_binary_cmd("ffprobe")
                                command = [
                                    ffprobe,
                                    "-v",
                                    "error",
                                    "-select_streams",
                                    "v:0",
                                    "-show_entries",
                                    "stream=profile,pix_fmt",
                                    "-of",
                                    "default=nokey=1:noprint_wrappers=1",
                                    full_path,
                                ]
                                result = utils.run_command_with_output(command).splitlines()
                                profile = result[0]
                                pix_fmt = result[1]
                                try:
                                    test_vector.output_format = OutputFormat[pix_fmt.upper()]
                                    if test_vector.output_format == OutputFormat.UNKNOWN:
                                        raise KeyError
                                except KeyError as key_err:
                                    exceptions_output_format = {
                                        # All information taken from mediainfo
                                        "vcon-stp5L1": OutputFormat.YUV420P,
                                        "ibm_tempete_e": OutputFormat.YUV420P,
                                        # Simple Studio Profile taken from ffmpeg and doc
                                        "vcon-stp13L2": OutputFormat.YUV444P,
                                        "vcon-stp12L2": OutputFormat.YUV444P,
                                        "vcon-stpsh2L1": OutputFormat.YUV422P,
                                        "vcon-stpsh1L1": OutputFormat.YUV422P,
                                        "vcon-stpsp1L1": OutputFormat.YUV422P,
                                    }
                                    if test_vector.name in exceptions_output_format:
                                        test_vector.output_format = exceptions_output_format[test_vector.name]
                                    else:
                                        raise key_err

                                try:
                                    test_vector.profile = Profile[profile.translate(str.maketrans(" :", "__")).upper()]
                                except KeyError as key_err:
                                    exceptions_profile = {
                                        # Values come from official spec validated with mediainfo online
                                        # Test suite: MPEG4_VIDEO-AdvancedSimpleProfile
                                        "vcon_a1ge_13_asp_l4": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_13_asp_l3": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge12_asp_L2": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_ge_1_asp_l4": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge12_asp_L3": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_10_asp_l1": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge9_asp_L1": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge9_asp_L4": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge9_asp_L2": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge2_asp_L4": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge9_asp_L3": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_13_asp_l1": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_10_asp_l3": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_10_asp_l2": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge12_asp_L1": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "vcon_a1ge_13_asp_l2": Profile.ADVANCED_SIMPLE_PROFILE,
                                        "a1ge4_asp": Profile.SIMPLE_PROFILE,
                                        # Test suite: MPEG4_VIDEO-SimpleStudioProfile
                                        "vcon-stpsh2L1": Profile.SIMPLE_STUDIO_PROFILE,
                                        "vcon-stpsh1L1": Profile.SIMPLE_STUDIO_PROFILE,
                                        "vcon-stpsp1L1": Profile.SIMPLE_STUDIO_PROFILE,
                                        "vcon-stp12L2": Profile.SIMPLE_STUDIO_PROFILE,
                                        "vcon-stp13L2": Profile.SIMPLE_STUDIO_PROFILE,
                                        # Test suite: MPEG4_VIDEO-SimpleScalableProfile
                                        "motorola_stefan": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "motorola_news": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_mobile_1": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_mobile_2": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "motorola_akiyo": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "motorola_akiyo_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_tempete": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "motorola_news_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_mobile_2_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "motorola_stefan_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_tempete_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                        "ibm_mobile_1_e": Profile.ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE,
                                    }
                                    if test_vector.name in exceptions_profile:
                                        test_vector.profile = exceptions_profile[test_vector.name]
                                    else:
                                        raise key_err
                            except Exception:
                                pass

                        # Update checksum if source exists
                        if test_vector.source:
                            orig_name = next(
                                (n for n, info in original_vectors.items() if info["source"] == test_vector.source),
                                None,
                            )
                            if orig_name:
                                downloaded_file = os.path.join(
                                    suite_dir, orig_name, os.path.basename(test_vector.source)
                                )
                                if os.path.exists(downloaded_file):
                                    test_vector.source_checksum = utils.file_checksum(downloaded_file)

                        test_suite.test_vectors[name] = test_vector

        absolute_output_filepath = os.path.join(absolute_dest_dir, output_filepath)
        test_suite.to_json_file(absolute_output_filepath)

    @staticmethod
    def get_files_in_directory(directory_url: str) -> List[str]:
        opener = create_enhanced_opener()
        response = opener.open(directory_url)
        data = response.read().decode("utf-8")

        hparser = HREFParser()
        hparser.feed(data)

        links: List[str] = []
        for link in hparser.links:
            if not link.endswith("/") and directory_url in link:
                links.append(link)
        return links

    @staticmethod
    def should_include_file(rel_path: str, profile_type: str, filename: str) -> bool:
        """Determines whether a file should be included based on the profile being generated."""
        rel_path_lower = rel_path.lower()
        filename_lower = filename.lower()

        is_stp = filename_lower.startswith("vcon-stp")
        is_ssp = filename_lower.startswith("vcon-ssp")
        is_studio = "studio" in rel_path_lower or is_stp or is_ssp

        if profile_type == "advanced_simple_profile":
            return not is_studio
        elif profile_type == "simple_studio_profile":
            return is_studio
        else:
            return True


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

    generator = MPEG4VIDEOGenerator(
        "simple_profile",
        "MPEG4_VIDEO-SimpleProfile",
        Codec.MPEG4_VIDEO,
        "ISO IEC 14496-4 MPEG4 video simple profile test suite",
        ["simple_profile_4_5", "simple_profile_6"],
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = MPEG4VIDEOGenerator(
        "advanced_simple_profile",
        "MPEG4_VIDEO-AdvancedSimpleProfile",
        Codec.MPEG4_VIDEO,
        "ISO IEC 14496-4 MPEG4 video advanced simple profile test suite",
        ["advanced_simple_profile", "advanced+studio_simple_profile"],
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = MPEG4VIDEOGenerator(
        "simple_studio_profile",
        "MPEG4_VIDEO-SimpleStudioProfile",
        Codec.MPEG4_VIDEO,
        "ISO IEC 14496-4 MPEG4 video simple studio profile test suite",
        ["advanced+studio_simple_profile", "simple_studio_profile"],
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = MPEG4VIDEOGenerator(
        "simple_scalable_profile",
        "MPEG4_VIDEO-SimpleScalableProfile",
        Codec.MPEG4_VIDEO,
        "ISO IEC 14496-4 MPEG4 video simple scalable profile test suite",
        ["simple_scalable_profile"],
        True,
    )
    generator.generate(not args.skip_download, args.jobs)
