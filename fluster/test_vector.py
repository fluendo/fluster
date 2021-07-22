# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from enum import Enum
from fluster.codec import PixelFormat


class TestVectorResult(Enum):
    """Test Result"""

    NOT_RUN = "NotRun"
    SUCCESS = "Success"
    FAILURE = "Failure"
    TIMEOUT = "Timeout"
    ERROR = "Error"


class TestVector:
    """Test vector"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        name: str,
        source: str,
        source_checksum: str,
        input_file: str,
        output_format: PixelFormat,
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
        self.errors = []

    @classmethod
    def from_json(cls, data: dict):
        """Deserialize an instance of TestVector from a json file"""
        if "output_format" in data:
            data["output_format"] = PixelFormat(data["output_format"])
        else:
            data["output_format"] = PixelFormat.YUV420P
        return (data["name"], cls(**data))

    def data_to_serialize(self):
        """Return the data to be serialized"""
        data = self.__dict__.copy()
        data.pop("test_result")
        data.pop("errors")
        data["output_format"] = str(self.output_format.value)
        return data

    def __str__(self):
        ret = (
            f"        {self.name}\n"
            f"            Source: {self.source}\n"
            f"            Input: {self.input_file}\n"
            f"            Result: {self.result}"
        )
        return ret
