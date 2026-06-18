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
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from fluster import utils
from fluster.codec import Codec, OutputFormat
from fluster.test_suite import TestSuite
from fluster.test_vector import TestVector

SOURCE_URL = "https://ott.dolby.com/OnDelKits/EC-3_Online_Delivery_Kit_1.6/Test_Signals/elementary_streams/Audio.zip"
BITSTREAM_EXT = ".ec3"

# channels-layout values for flueac3prodec:
#   0 = Auto (default, used for JOC/Atmos streams)
#   2 = ChannelsLayout-2.0 (stereo)
#   7 = ChannelsLayout-3.2 (5.1)
CHANNELS_LAYOUT = {"2ch": 2, "6ch": 7, "514ch": 0, "default": 0}


def get_channels_layout(filename: str) -> int:
    """Return the channels-layout value based on the stream filename."""
    return next((val for key, val in CHANNELS_LAYOUT.items() if key in filename), 0)


class EAC3Generator:
    """Generates a Fluster test suite from the Dolby EC-3 Online Delivery Kit."""

    def __init__(self) -> None:
        self.suite_name = "EAC3_ELEMENTARY_STREAMS"
        self.codec = Codec.EAC3
        self.description = "Dolby EC-3 Online Delivery Kit 1.6 elementary stream test suite."

    def generate(self, download: bool) -> None:
        """Generates the test suite and saves it to a JSON file."""
        script_dir = Path(__file__).resolve().parent
        resources_dir = script_dir / "resources"
        zip_path = resources_dir / "EAC3_Audio.zip"
        extract_dir = resources_dir / self.suite_name

        if download:
            resources_dir.mkdir(exist_ok=True)
            print(f"Downloading {SOURCE_URL}")
            urllib.request.urlretrieve(SOURCE_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

        source_checksum = utils.file_checksum(str(zip_path)) if zip_path.exists() else "__skip__"

        audio_dir = extract_dir / "Audio"
        search_dir = audio_dir if audio_dir.is_dir() else extract_dir

        test_suite = TestSuite(
            f"{self.suite_name}.json", str(resources_dir), self.suite_name, self.codec, self.description, {}
        )

        for filepath in sorted(search_dir.glob(f"*{BITSTREAM_EXT}")):
            input_file = str(filepath.relative_to(extract_dir))
            test_suite.test_vectors[filepath.name] = TestVector(
                name=filepath.name,
                source=SOURCE_URL,
                source_checksum=source_checksum,
                input_file=input_file,
                output_format=OutputFormat.UNKNOWN,
                result="",
                optional_params={"channels_layout": get_channels_layout(filepath.name)},
            )

        test_suite.to_json_file(str(script_dir / f"{self.suite_name}.json"))
        print(f"Generated {self.suite_name}.json with {len(test_suite.test_vectors)} test vectors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading and extracting the ZIP file")
    args = parser.parse_args()

    EAC3Generator().generate(not args.skip_download)
