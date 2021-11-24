import os
import argparse
import xml.etree.ElementTree as ET
import sys
import multiprocessing
import urllib.request

# pylint: disable=wrong-import-position
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster.test_suite import TestSuite, TestVector
from fluster.codec import Codec, OutputFormat
from fluster import utils
from fluster.decoders import av1_aom

# pylint: enable=wrong-import-position

# Sourced from test/test_data_download_worker.cmake
AV1_URL = "https://storage.googleapis.com/aom-test-data"

# Sourced from test/test_vector_test.cc
BITSTREAM_EXTS = (
    ".ivf",
    ".webm",
    ".mkv"
)


class AOMGenerator:
    """Generates a test suite from the conformance bitstreams"""

    def __init__(
        self,
        name: str,
        suite_name: str,
        codec: Codec,
        description: str,
        site: str,
    ):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description
        self.site = site
        self.decoder = av1_aom.AV1AOMDecoder()

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

        print(f"Download list of bitstreams from {self.site + self.name}")
        opener = urllib.request.build_opener()
        root = ET.parse(opener.open(self.site)).getroot()
        opener.close()

        for entry in root.findall("{*}Contents"):
            if "Contents" not in entry.tag:
                continue
            fname = entry.find("{*}Key").text
            name = fname[:-4]
            if fname[-4:] not in BITSTREAM_EXTS or "invalid" in fname:
                continue

            file_url = f"{AV1_URL}/{entry.find('{*}Key').text}"
            test_vector = TestVector(
                name, file_url, "__skip__", fname, OutputFormat.YUV420P, "")
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
            dest_path = os.path.join(
                dest_dir, os.path.basename(test_vector.source))
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
            # Run the libaom av1 decoder to get the checksum as the .md5 files are per-frame
            test_vector.result = self.decoder.decode(
                dest_path, out420, test_vector.output_format, 30, False)
            os.remove(out420)

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
    generator = AOMGenerator(
        "libaom-AV1",
        "AV1-TEST-VECTORS",
        Codec.AV1,
        "AV1 Test Vector Catalogue from https://storage.googleapis.com/aom-test-data",
        AV1_URL,
    )
    generator.generate(not args.skip_download, args.jobs)
