#!/usr/bin/env python3

# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
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

"""Generates the MPEG-H 3D Audio (ISO/IEC 23008-9, edition 3) conformance test suite.

ISO publishes the conformance data as one zip with the compressed bitstreams (`compressedMhas/`) and the reference
decoded output (`referencesWav/`). Each reference .wav is one conformance case: the bitstream it was decoded from is
named in its file name, and the decoder settings used to obtain it are encoded after a double underscore:

    C103_3_FD_D-Drc-1-Gr-0-1__Lou-24_Eff-6.wav
    \\_____________________/  \\____________/
        bitstream name       decoder settings

so one bitstream can appear in several test vectors with different settings. The cases captured at an intermediate
conformance point of the decoder ("Cpo-<x>" setting) are skipped, a decoder can not be asked for them.

The conformance criterion of the standard is a tolerance based comparison (RMS / LSB), not bit exactness, hence the
suite uses the "sample" test method: the output of a decoder is compared with the one of the reference decoder.

    gen_mpegh.py --zip-file MPEG-H_3D_audio_conformanceData.zip     # all the vectors
    fluster.py reference ISO-MPEGH-3DA MPEGH_3D_AUDIO-ED3           # fills the result of the decodable ones
    gen_mpegh.py --zip-file ... --results-from <suite>.json         # keeps only the vectors with a result
"""

import argparse
import json
import os
import sys
import zipfile
from typing import Dict, List, Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVector

ZIP_URL = "https://standards.iso.org/iso-iec/23008/-9/ed-3/en/MPEG-H_3D_audio_conformanceData.zip"
SUITE_NAME = "MPEGH_3D_AUDIO-ED3"
SUITE_DESCRIPTION = "ISO/IEC 23008-9 MPEG-H 3D Audio conformance bitstreams (edition 3)"

BITSTREAMS_DIR = "compressedMhas/"
REFERENCES_DIR = "referencesWav/"
BITSTREAM_EXT = ".mhas"
REFERENCE_EXT = ".wav"

# Decoder settings encoded in the reference file names -> optional_params keys
SETTINGS_KEYS = {
    "Eff": "drc_effect_type",
    "Pr": "preset_id",
    "Lay": "target_layout",
    "Lou": "target_loudness",
}
# The "-" in "Lou-24" is a separator, the value is a loudness of -24
NEGATIVE_SETTINGS = {"Lou"}


def parse_reference_name(reference_name: str) -> Tuple[str, Dict[str, int]]:
    """Split a reference file name into its bitstream name and decoder settings.

    "C2_3_FD_D-Drc-1__Lou-24_Eff-6.wav" -> ("C2_3_FD_D-Drc-1", {"target_loudness": -24, "drc_effect_type": 6})
    """
    bitstream, _, suffix = os.path.splitext(reference_name)[0].partition("__")
    settings: Dict[str, int] = {}
    for token in suffix.split("_") if suffix else []:
        key, dash, value = token.partition("-")
        if not dash or key not in SETTINGS_KEYS or not value.isdigit():
            raise ValueError(f"Unknown decoder setting '{token}' in {reference_name}")
        settings[SETTINGS_KEYS[key]] = -int(value) if key in NEGATIVE_SETTINGS else int(value)
    return bitstream, settings


def keep_decoded_vectors(test_suite: TestSuite, results_file: str) -> None:
    """Keep only the test vectors with a result in `results_file` (a suite JSON filled by `fluster.py reference`)
    and copy that result, the reference decoder can not decode the rest of them"""
    with open(results_file, encoding="utf-8") as results_json:
        results = {vector["name"]: vector.get("result", "") for vector in json.load(results_json)["test_vectors"]}
    dropped = [name for name in test_suite.test_vectors if not results.get(name)]
    for name in dropped:
        del test_suite.test_vectors[name]
    for name, test_vector in test_suite.test_vectors.items():
        test_vector.result = results[name]
    print(f"Dropped {len(dropped)} test vectors without result in {results_file}, {len(test_suite.test_vectors)} left")


class MPEGHGenerator:
    """Generates a test suite from the zip with the MPEG-H 3D Audio conformance bitstreams and reference files"""

    def __init__(self, zip_url: str, zip_file: str, output_dir: str) -> None:
        self.zip_url = zip_url
        self.zip_file = zip_file
        self.output_dir = output_dir

    def build_test_suite(self, names: List[str], checksum: str, resources_dir: str) -> TestSuite:
        """Create the test suite with one test vector per reference file found in the zip `names`"""
        bitstreams = {
            os.path.basename(name)[: -len(BITSTREAM_EXT)]
            for name in names
            if name.startswith(BITSTREAMS_DIR) and name.endswith(BITSTREAM_EXT)
        }
        references = sorted(
            os.path.basename(name) for name in names if name.startswith(REFERENCES_DIR) and name.endswith(REFERENCE_EXT)
        )
        if not bitstreams or not references:
            raise RuntimeError(f"No bitstreams or reference files found in the zip ({len(names)} entries)")

        test_suite = TestSuite(
            os.path.join(self.output_dir, SUITE_NAME + ".json"),
            resources_dir,
            SUITE_NAME,
            Codec.MPEGH_3DA,
            SUITE_DESCRIPTION,
            {},
            test_method=TestMethod.SAMPLE,
        )

        for reference in references:
            if "Cpo-" in reference:
                print(f"Skipping {reference}: reference captured at an intermediate conformance point")
                continue
            bitstream, settings = parse_reference_name(reference)
            if bitstream not in bitstreams:
                raise RuntimeError(f"Reference {reference} has no bitstream {bitstream}{BITSTREAM_EXT} in the zip")
            name = reference[: -len(REFERENCE_EXT)]
            test_suite.test_vectors[name] = TestVector(
                name,
                self.zip_url,
                checksum,
                BITSTREAMS_DIR + bitstream + BITSTREAM_EXT,
                OutputFormat.UNKNOWN,
                "",
                optional_params=settings or None,
            )
        return test_suite

    def generate(self, results_file: Optional[str] = None) -> None:
        """Generates the test suite from the local zip and saves it to a file"""
        with zipfile.ZipFile(self.zip_file) as zip_archive:
            bad_member = zip_archive.testzip()
            if bad_member:
                raise RuntimeError(f"{self.zip_file} is corrupt: bad member {bad_member}")
            names = zip_archive.namelist()
        # fluster verifies this checksum of the zip when it downloads the suite
        checksum = utils.file_checksum(self.zip_file)
        resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        test_suite = self.build_test_suite(names, checksum, resources_dir)
        if results_file:
            keep_decoded_vectors(test_suite, results_file)

        os.makedirs(self.output_dir, exist_ok=True)
        test_suite.to_json_file(test_suite.filename)
        print(f"Generated {test_suite.filename} with {len(test_suite.test_vectors)} test vectors (zip md5 {checksum})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--zip-file",
        required=True,
        help="local copy of the conformance data zip; its content is listed and its checksum computed",
    )
    parser.add_argument(
        "--zip-url",
        default=ZIP_URL,
        help="URL the zip is downloaded from (used as source of the test vectors)",
    )
    parser.add_argument(
        "--results-from",
        help="suite JSON filled by `fluster.py reference`: keep only its vectors with a result (the ones the "
        "reference decoder can decode) and copy that result",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_suites", "mpegh"),
        help="directory where the test suite JSON is written",
    )
    args = parser.parse_args()

    MPEGHGenerator(args.zip_url, args.zip_file, os.path.abspath(args.output_dir)).generate(args.results_from)
