# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
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

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from fluster.codec import OutputFormat, Profile
from fluster.decoder import Decoder


class Parser(Decoder):
    """Base class for parsers"""

    is_parser = True
    provider = "GStreamer"
    element = ""

    def __init__(self) -> None:
        super().__init__()
        if not self.name:
            self.name = self.element
        self.description = f"{self.provider} {self.codec.value} parser"

    @abstractmethod
    def parse(
        self,
        input_filepath: str,
        timeout: int,
        verbose: bool,
        profile: Optional[Profile] = None,
    ) -> str:
        """Parses input_filepath"""
        raise Exception("Not implemented")

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
        optional_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Runs the parser through the decoder test interface"""
        return self.parse(input_filepath, timeout, verbose)


PARSERS: List[Parser] = []


def register_parser(cls: Type[Parser]) -> Type[Parser]:
    """Register a new parser implementation"""
    PARSERS.append(cls())
    PARSERS.sort(key=lambda parser: parser.name)
    return cls
