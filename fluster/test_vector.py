# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
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

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from fluster.codec import OutputFormat, Profile


class TestVectorResult(Enum):
    """Test Result"""

    NOT_RUN = "Not Run"
    SUCCESS = "Success"
    FAIL = "Fail"
    TIMEOUT = "Timeout"
    ERROR = "Error"
    REFERENCE = "Reference run"  # used in reference runs to indicate the decoder for this test vector was succesful


class TestVector:
    """Test vector"""

    def __init__(
        self,
        name: str,
        source: str,
        source_checksum: str,
        input_file: str,
        output_format: OutputFormat,
        result: str,
        profile: Optional[Profile] = None,
        optional_params: Optional[Dict[str, Any]] = None,
    ):
        # JSON members
        self.name = name
        self.source = source
        self.source_checksum = source_checksum
        self.input_file = input_file
        self.profile = profile
        self.optional_params = optional_params
        self.output_format = output_format
        self.result = result

        # Not included in JSON
        self.test_result = TestVectorResult.NOT_RUN
        self.test_time = 0.0
        self.errors: List[List[str]] = []

    @classmethod
    def from_json(cls: Type["TestVector"], data: Any) -> Any:
        """Deserialize an instance of TestVector from a json file"""
        if "output_format" in data:
            data["output_format"] = OutputFormat(data["output_format"])
        else:
            data["output_format"] = OutputFormat.NONE

        # We only define profile if the paramter is found in .json of test suite
        if "profile" in data:
            data["profile"] = Profile(data["profile"])

        return (data["name"], cls(**data))

    def data_to_serialize(self) -> Dict[str, object]:
        """Return the data to be serialized"""
        data = self.__dict__.copy()
        data.pop("test_result")
        data.pop("errors")
        data.pop("test_time")
        data["output_format"] = str(self.output_format.value)
        if self.profile is not None:
            data["profile"] = str(self.profile.value)
        else:
            data.pop("profile")
        if self.optional_params is not None:
            data["optional_params"] = self.optional_params
        else:
            data.pop("optional_params")

        return data

    def __str__(self) -> str:
        ret = (
            f"        {self.name}\n"
            f"            Source: {self.source}\n"
            f"            Input: {self.input_file}\n"
            f"            Profile: {self.profile}\n"
            f"            Options: {self.optional_params}\n"
            f"            Result: {self.result}"
        )
        return ret
