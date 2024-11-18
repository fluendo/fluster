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

URL_MPEG2 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/"
URL_MPEG2_ADTS = URL_MPEG2 + "compressedAdts"
URL_MPEG2_ADIF = URL_MPEG2 + "compressedAdif"
URL_MPEG2_WAV_REFS = URL_MPEG2 + "referencesWav"
URL_MPEG2_WAV_REFS_MD5 = URL_MPEG2 + "referencesWav/_checksum"

URL_MPEG4 = BASE_URL + "ittf/PubliclyAvailableStandards/ISO_IEC_14496-26_2010_Bitstreams/"
URL_MPEG4_ADIF = URL_MPEG4 + "DVD1/mpeg4audio-conformance/compressedAdif/add-opt/"
URL_MPEG4_WAV_REFS = URL_MPEG4 + "DVD2/mpeg4audio-conformance/referencesWav/"
URL_MPEG4_WAV_REFS_MD5 = URL_MPEG4 + "DVD1/mpeg4audio-conformance/referencesWav/_checksum/"

BITSTREAM_EXTS = [".adts", ".adif"]
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
        url_test_vectors: str,
        url_reference_vectors: str,
        url_reference_vectors_checksums: str,
        use_ffprobe: bool = False,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.url_test_vectors = url_test_vectors
        self.url_reference_vectors = url_reference_vectors
        self.url_reference_vectors_checksums = url_reference_vectors_checksums
        self.use_ffprobe = use_ffprobe

    def _download_raw_output_references_and_checksums(self, jobs, test_suite, raw_bitstream_links,
                                                      raw_bitstream_md5_links):
        """Downloads raw output reference bitstreams and their checksums"""
        with Pool(jobs) as pool:
            def _callback_error(err):
                print(f"\nError downloading -> {err}\n")
                pool.terminate()

            downloads = []

            print(f"\tDownloading output reference files for test suite {self.suite_name}")

            for link in raw_bitstream_links:
                file_name = os.path.basename(link)
                base_name = file_name.split('.')[0]
                main_prefix = "_".join(base_name.split('_')[:2])

                directory = os.path.join(test_suite.resources_dir, test_suite.name, main_prefix)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                downloads.append(
                    pool.apply_async(
                        utils.download,
                        args=(link, directory),
                        error_callback=_callback_error,
                    )
                )

            print(f"\tDownloading output reference checksum files for test suite {self.suite_name}")

            for link in raw_bitstream_md5_links:
                file_name = os.path.basename(link)
                base_name = file_name.split('.')[0]
                main_prefix = "_".join(base_name.split('_')[:2])

                directory = os.path.join(test_suite.resources_dir, test_suite.name, main_prefix)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                downloads.append(
                    pool.apply_async(
                        utils.download,
                        args=(link, directory),
                        error_callback=_callback_error,
                    )
                )

            pool.close()
            pool.join()

        for job in downloads:
            try:
                job.get()
                if not job.successful():
                    raise ValueError("Download task was not successful")
            except Exception as e:
                sys.exit(f"Some download failed: {e}")

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

        with urllib.request.urlopen(self.url_test_vectors) as resp:
            data = str(resp.read())
            hparser.feed(data)
        compressed_bitstream_links = [url for url in hparser.links if url.endswith(tuple(BITSTREAM_EXTS))]
        compressed_bitstream_names = [os.path.splitext(os.path.basename(x))[0] for x in compressed_bitstream_links]

        with urllib.request.urlopen(self.url_reference_vectors) as resp:
            data = str(resp.read())
            hparser.feed(data)
        raw_bitstream_links = [url for url in hparser.links if url.endswith(tuple(RAW_EXTS))]

        raw_bitstream_names = [
            os.path.splitext(os.path.basename(x))[0].split('_f')[0] for x in raw_bitstream_links
        ]

        missing_files = [x for x in set(compressed_bitstream_names).difference(raw_bitstream_names)]
        if missing_files:
            print(f"Missing reference files: {missing_files}")
            for missing_file in missing_files:
                print(f"Skipping test vector {missing_file}, as the reference file is missing.")

        raw_bitstream_names = [name for name in compressed_bitstream_names if name not in missing_files]

        # Match and store entries of raw_bitstream_links that contain entries of raw_bitstream_names as substrings
        raw_bitstream_links = [
            link for link in raw_bitstream_links if any(name in link for name in raw_bitstream_names)
        ]

        with urllib.request.urlopen(self.url_reference_vectors_checksums) as resp:
            data = str(resp.read())
            hparser.feed(data)
        raw_bitstream_md5_links = [url for url in hparser.links if url.endswith(tuple(MD5_EXTS))]

        raw_bitstream_md5_names = [
            os.path.splitext(os.path.splitext(os.path.basename(x))[0].split('_f')[0])[0] for x in
            raw_bitstream_md5_links
        ]

        missing_checksum_files = [x for x in set(compressed_bitstream_names).difference(raw_bitstream_md5_names)]
        if missing_checksum_files:
            print(f"Missing reference checksum files: {missing_checksum_files}")
            for missing_checksum in missing_checksum_files:
                print(f"Skipping checksum for {missing_checksum}, as the reference file is missing.")

        raw_bitstream_md5_names = [name for name in compressed_bitstream_names if name not in missing_checksum_files]

        # Match and store entries of raw_bitstream_md5_links that contain entries of raw_bitstream_md5_names
        # as substrings
        raw_bitstream_md5_links = [
            link for link in raw_bitstream_md5_links if any(name in link for name in raw_bitstream_md5_names)
        ]

        for source_url in compressed_bitstream_links:
            input_filename = os.path.basename(source_url)
            test_vector_name = os.path.splitext(input_filename)[0]
            test_vector = TestVector(
                test_vector_name, source_url, "__skip__", input_filename, OutputFormat.UNKNOWN, ""
            )
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

        # Download test suite output reference and md5 checksum files
        self._download_raw_output_references_and_checksums(jobs, test_suite, raw_bitstream_links,
                                                           raw_bitstream_md5_links)

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

            # Read or calculate checksum of expected raw output
            if test_vector.name not in missing_checksum_files:
                self._fill_checksum_aac(test_vector, dest_dir)

        test_suite.to_json_file(output_filepath)
        print("Generate new test suite: " + test_suite.name + ".json")

    @staticmethod
    def _fill_checksum_aac(test_vector, dest_dir):
        base_name = test_vector.name
        raw_file = None
        ext = None

        for ext in RAW_EXTS:
            exact_file = os.path.join(dest_dir, base_name + ext)
            if os.path.exists(exact_file):
                raw_file = exact_file
                break

        if not raw_file:
            for ext in RAW_EXTS:
                fallback_file = os.path.join(dest_dir, base_name + '_f00' + ext)
                if os.path.exists(fallback_file):
                    raw_file = fallback_file
                    break

        if not raw_file:
            raise Exception(
                f"Neither {base_name + ext} nor {base_name + '_f00' + ext} found with extensions {RAW_EXTS} in {dest_dir}"
            )

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
        "MPEG2_AAC-ADTS",
        "MPEG2_AAC-ADTS",
        Codec.AAC,
        "ISO IEC 13818-4 MPEG2 AAC ADTS test suite",
        URL_MPEG2_ADTS,
        URL_MPEG2_WAV_REFS,
        URL_MPEG2_WAV_REFS_MD5,
        True,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG2_AAC-ADIF",
        "MPEG2_AAC-ADIF",
        Codec.AAC,
        "ISO IEC 13818-4 MPEG2 AAC ADIF test suite",
        URL_MPEG2_ADIF,
        URL_MPEG2_WAV_REFS,
        URL_MPEG2_WAV_REFS_MD5,
        False,
    )
    generator.generate(not args.skip_download, args.jobs)

    generator = AACGenerator(
        "MPEG4_AAC-ADIF",
        "MPEG4_AAC-ADIF",
        Codec.AAC,
        "ISO IEC 14496-26 MPEG4 AAC ADIF test suite",
        URL_MPEG4_ADIF,
        URL_MPEG4_WAV_REFS,
        URL_MPEG4_WAV_REFS_MD5,
        False,
    )
    generator.generate(not args.skip_download, args.jobs)
