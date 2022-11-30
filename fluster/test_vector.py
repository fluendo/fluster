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
from typing import List, Dict, Type, Any
from fluster.codec import OutputFormat


class TestVectorResult(Enum):
    """Test Result"""

    NOT_RUN = "Not Run"
    SUCCESS = "Success"
    FAIL = "Fail"
    TIMEOUT = "Timeout"
    ERROR = "Error"

    """
    This is only used in reference runs to indicate that
    the decoder for this test vector run succesfully
    """
    REFERENCE = "Reference run"


class TestVector:
    """Test vector"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        name: str,
        source: str,
        source_checksum: str,
        input_file: str,
        output_format: OutputFormat,
        result: str,
    ):
        # JSON members
        self.name = name
        self.source = source
        self.source_checksum = source_checksum
        self.input_file = input_file
        self.output_format = output_format
        self.result = result

        # Not included in JSON
        self.test_result = TestVectorResult.NOT_RUN
        self.errors: List[List[str]] = []

    @classmethod
    def from_json(cls: Type["TestVector"], data: Any) -> Any:
        """Deserialize an instance of TestVector from a json file"""
        if "output_format" in data:
            data["output_format"] = OutputFormat(data["output_format"])
        else:
            data["output_format"] = OutputFormat.NONE
        return (data["name"], cls(**data))

    def data_to_serialize(self) -> Dict[str, object]:
        """Return the data to be serialized"""
        data = self.__dict__.copy()
        data.pop("test_result")
        data.pop("errors")
        data["output_format"] = str(self.output_format.value)
        return data

    def __str__(self) -> str:
        ret = (
            f"        {self.name}\n"
            f"            Source: {self.source}\n"
            f"            Input: {self.input_file}\n"
            f"            Result: {self.result}"
        )
        return ret
