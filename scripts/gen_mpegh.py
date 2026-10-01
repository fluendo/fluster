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

"""Generates the MPEG-H 3D Audio (ISO/IEC 23008-9) conformance test suite.

Edition 1 publishes the compressed bitstreams (.mhas) and the reference
decoded output (.wav) as plain files. Each reference .wav is one conformance
case: the bitstream it was decoded from is named in its file name, and the
decoder settings used to obtain it are encoded after a double underscore:

    C103_3_FD_D-Drc-1-Gr-0-1__Lou-24_Eff-6_Pr-1.wav
    \\_____________________/  \\____________________/
        bitstream name         decoder settings

so one bitstream can appear in several test vectors with different settings.
Edition 3 (and edition 2, with identical content) only publishes one zip with the
`compressedMhas/` and `referencesWav/` folders, with the same file naming; it is
used with --edition 3 and the zip downloaded locally (--zip-file).

The reference decoder (mpeghdec, Baseline profile level 4) can not decode every bitstream of the
conformance set (e.g. HOA content). The suite is generated with every vector, `fluster.py reference`
fills the `result` of the ones it decodes and --results-from keeps only those:

    gen_mpegh.py ...                                       # all the vectors
    fluster.py reference Fraunhofer-mpeghdec <suite>       # fills the result of the decodable ones
    gen_mpegh.py ... --results-from <suite>.json           # keeps only the vectors with a result
The "Cpo" setting (conformance point not at the final output) is not stored: the
reference .wav of those vectors is an intermediate point of the decoder chain.
The conformance criterion of the standard is a tolerance based comparison
(RMS / LSB), not bit exactness, hence the suite uses the "sample" test method.
"""

import argparse
import json
import multiprocessing
import os
import re
import sys
import urllib.request
import zipfile
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urljoin, urlparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVector

BASE_URL = "https://standards.iso.org/iso-iec/23008/-9/"
ED1_MHAS_URL = BASE_URL + "ed-1/en/compressedMhas/"

BITSTREAM_EXT = ".mhas"
REFERENCE_EXT = ".wav"

SUITE_NAME = "MPEGH_3D_AUDIO-ED1"
SUITE_DESCRIPTION = "ISO/IEC 23008-9 MPEG-H 3D Audio conformance bitstreams (edition 1)"

ED3_ZIP_URL = BASE_URL + "ed-3/en/MPEG-H_3D_audio_conformanceData.zip"
ED3_SUITE_NAME = "MPEGH_3D_AUDIO-ED3"
ED3_SUITE_DESCRIPTION = "ISO/IEC 23008-9 MPEG-H 3D Audio conformance bitstreams (edition 3)"
ZIP_BITSTREAMS_DIR = "compressedMhas/"
ZIP_REFERENCES_DIR = "referencesWav/"

# Decoder settings encoded in the reference file names -> optional_params keys.
# "Cpo" (conformance point) is validated but not stored: it only says that the reference .wav was
# captured at an intermediate point of the decoder, it is not a setting a decoder can be given.
IGNORED_SETTINGS = {"Cpo"}
SETTINGS_KEYS = {
    "Eff": "drc_effect_type",
    "Pr": "preset_id",
    "Lay": "target_layout",
    "Lou": "target_loudness",
}
# The "-" in "Lou-24" is a separator, the value is a loudness of -24
NEGATIVE_SETTINGS = {"Lou"}


class HREFParser(HTMLParser):
    """Collects the href of every anchor of an HTML index page"""

    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def list_index(source: str, extension: str) -> List[str]:
    """Return the sorted file names with the given extension found in an index.

    `source` is the URL of an HTML directory index, the path of a local directory,
    or the path of a local file with a copy of an index (HTML or plain text, one
    entry per line).
    """
    if os.path.isdir(source):
        return sorted(name for name in os.listdir(source) if name.endswith(extension))

    if urlparse(source).scheme in ("http", "https"):
        with urllib.request.urlopen(source) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    else:
        with open(source, encoding="utf-8", errors="replace") as index_file:
            content = index_file.read()

    names = set()
    if "<a " in content.lower():
        parser = HREFParser()
        parser.feed(content)
        for link in parser.links:
            name = os.path.basename(unquote(urlparse(urljoin(source, link)).path))
            if name.endswith(extension):
                names.add(name)
    else:
        names.update(re.findall(r"[\w][\w.\-]*" + re.escape(extension), content))
    return sorted(names)


def parse_reference_name(reference_name: str) -> Tuple[str, Dict[str, int]]:
    """Split a reference file name into its bitstream name and decoder settings.

    "C2_3_FD_D-Drc-1__Lou-24_Eff-6.wav" -> ("C2_3_FD_D-Drc-1",
                                           {"target_loudness": -24, "drc_effect_type": 6})
    """
    stem = reference_name[: -len(REFERENCE_EXT)] if reference_name.endswith(REFERENCE_EXT) else reference_name
    bitstream, separator, suffix = stem.partition("__")
    settings: Dict[str, int] = {}
    if separator:
        for token in suffix.split("_"):
            key, dash, value = token.partition("-")
            if not dash or (key not in SETTINGS_KEYS and key not in IGNORED_SETTINGS) or not value.isdigit():
                raise ValueError(f"Unknown decoder setting '{token}' in {reference_name}")
            if key in IGNORED_SETTINGS:
                continue
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
    """Generates a test suite from the MPEG-H 3D Audio conformance bitstreams"""

    def __init__(self, bitstreams_url: str, bitstreams_index: str, reference_index: str, output_dir: str) -> None:
        self.bitstreams_url = bitstreams_url
        self.bitstreams_index = bitstreams_index
        self.reference_index = reference_index
        self.output_dir = output_dir

    def build_test_suite(self, resources_dir: str) -> TestSuite:
        """Create the test suite with one test vector per reference file"""
        bitstreams = {os.path.splitext(name)[0] for name in list_index(self.bitstreams_index, BITSTREAM_EXT)}
        references = list_index(self.reference_index, REFERENCE_EXT)
        if not bitstreams or not references:
            raise RuntimeError("No bitstreams or reference files found in the given indexes")

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
            bitstream, settings = parse_reference_name(reference)
            if bitstream not in bitstreams:
                raise RuntimeError(f"Reference {reference} has no bitstream {bitstream}{BITSTREAM_EXT} in the index")
            input_file = bitstream + BITSTREAM_EXT
            name = reference[: -len(REFERENCE_EXT)]
            test_suite.test_vectors[name] = TestVector(
                name,
                urljoin(self.bitstreams_url, input_file),
                "__skip__",
                input_file,
                OutputFormat.UNKNOWN,
                "",
                optional_params=settings or None,
            )

        unused = sorted(bitstreams - {parse_reference_name(ref)[0] for ref in references})
        if unused:
            print(f"WARNING: bitstreams without reference file, not included in the suite: {unused}")
        return test_suite

    def generate(
        self, download: bool, jobs: int, bitstreams_dir: Optional[str] = None, results_file: Optional[str] = None
    ) -> None:
        """Generates the test suite and saves it to a file.

        The checksums of the bitstreams are computed from `bitstreams_dir` when given
        (nothing is downloaded), otherwise from the files downloaded into scripts/resources.
        """
        resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        test_suite = self.build_test_suite(resources_dir)

        if download and not bitstreams_dir:
            print(f"Downloading {len(test_suite.test_vectors)} test vectors from {self.bitstreams_url}")
            test_suite.download(
                jobs=jobs,
                out_dir=test_suite.resources_dir,
                verify=False,
                extract_all=True,
                keep_file=True,
            )

        # Several test vectors share the same bitstream, compute each checksum once
        checksums: Dict[str, str] = {}
        for test_vector in test_suite.test_vectors.values():
            if bitstreams_dir:
                bitstream_path = os.path.join(bitstreams_dir, test_vector.input_file)
            else:
                bitstream_path = os.path.join(
                    test_suite.resources_dir, test_suite.name, test_vector.name, os.path.basename(test_vector.source)
                )
            if not os.path.isfile(bitstream_path):
                raise FileNotFoundError(f"Bitstream {test_vector.input_file} not found in {bitstream_path}")
            if bitstream_path not in checksums:
                checksums[bitstream_path] = utils.file_checksum(bitstream_path)
            test_vector.source_checksum = checksums[bitstream_path]

        if results_file:
            keep_decoded_vectors(test_suite, results_file)
        os.makedirs(self.output_dir, exist_ok=True)
        test_suite.to_json_file(test_suite.filename)
        print(f"Generated {test_suite.filename} with {len(test_suite.test_vectors)} test vectors")


class MPEGHZipGenerator:
    """Generates a test suite from a single zip with the bitstreams and the reference files (edition 3)"""

    def __init__(self, zip_url: str, zip_file: str, output_dir: str) -> None:
        self.zip_url = zip_url
        self.zip_file = zip_file
        self.output_dir = output_dir

    def build_test_suite(self, names: List[str], checksum: str, resources_dir: str) -> TestSuite:
        """Create the test suite with one test vector per reference file found in the zip `names`"""
        bitstreams = {
            os.path.basename(name)[: -len(BITSTREAM_EXT)]
            for name in names
            if name.startswith(ZIP_BITSTREAMS_DIR) and name.endswith(BITSTREAM_EXT)
        }
        references = sorted(
            os.path.basename(name)
            for name in names
            if name.startswith(ZIP_REFERENCES_DIR) and name.endswith(REFERENCE_EXT)
        )
        if not bitstreams or not references:
            raise RuntimeError(f"No bitstreams or reference files found in the zip ({len(names)} entries)")

        test_suite = TestSuite(
            os.path.join(self.output_dir, ED3_SUITE_NAME + ".json"),
            resources_dir,
            ED3_SUITE_NAME,
            Codec.MPEGH_3DA,
            ED3_SUITE_DESCRIPTION,
            {},
            test_method=TestMethod.SAMPLE,
        )

        for reference in references:
            bitstream, settings = parse_reference_name(reference)
            if bitstream not in bitstreams:
                raise RuntimeError(f"Reference {reference} has no bitstream {bitstream}{BITSTREAM_EXT} in the zip")
            name = reference[: -len(REFERENCE_EXT)]
            test_suite.test_vectors[name] = TestVector(
                name,
                self.zip_url,
                checksum,
                ZIP_BITSTREAMS_DIR + bitstream + BITSTREAM_EXT,
                OutputFormat.UNKNOWN,
                "",
                optional_params=settings or None,
            )

        unused = sorted(bitstreams - {parse_reference_name(ref)[0] for ref in references})
        if unused:
            print(f"WARNING: bitstreams without reference file, not included in the suite: {unused}")
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
        "--edition",
        type=int,
        choices=(1, 3),
        default=1,
        help="edition to generate: 1 (separate files, needs --reference-index) or 3 (single zip, needs --zip-file)",
    )
    parser.add_argument(
        "--reference-index",
        help="edition 1: URL of the directory index with the reference .wav files, or a local copy of it",
    )
    parser.add_argument(
        "--zip-file",
        help="edition 3: local copy of the conformance data zip; its content is listed and its checksum computed",
    )
    parser.add_argument(
        "--zip-url",
        default=ED3_ZIP_URL,
        help="edition 3: URL the zip is downloaded from (used as source of the test vectors)",
    )
    parser.add_argument(
        "--bitstreams-index",
        default=ED1_MHAS_URL,
        help="URL of the directory index with the .mhas bitstreams, or a local copy of it",
    )
    parser.add_argument(
        "--bitstreams-url",
        default=ED1_MHAS_URL,
        help="base URL the bitstreams are downloaded from (used as source of the test vectors)",
    )
    parser.add_argument(
        "--bitstreams-dir",
        help="local directory with the .mhas bitstreams already downloaded: used to list them and to compute "
        "their checksums, nothing is downloaded",
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
    parser.add_argument(
        "--skip-download",
        help="do not download the bitstreams, use the ones already in scripts/resources",
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

    if args.edition == 3:
        if not args.zip_file:
            parser.error("--edition 3 requires --zip-file")
        MPEGHZipGenerator(args.zip_url, args.zip_file, os.path.abspath(args.output_dir)).generate(args.results_from)
        sys.exit(0)
    if not args.reference_index:
        parser.error("--edition 1 requires --reference-index")

    MPEGHGenerator(
        args.bitstreams_url,
        args.bitstreams_dir or args.bitstreams_index,
        args.reference_index,
        os.path.abspath(args.output_dir),
    ).generate(not args.skip_download, args.jobs, args.bitstreams_dir, args.results_from)
