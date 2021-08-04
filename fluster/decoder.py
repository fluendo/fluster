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

from abc import ABC, abstractmethod
from functools import lru_cache
from shutil import which
from typing import Type

from fluster.codec import OutputFormat, Codec
from fluster.utils import normalize_binary_cmd

# pylint: disable=broad-except


class Decoder(ABC):
    """Base class for decoders"""

    name = ""
    codec = Codec.NONE
    hw_acceleration = False
    description = ""
    binary = ""

    def __init__(self) -> None:
        if self.binary:
            self.binary = normalize_binary_cmd(self.binary)

    @abstractmethod
    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
    ) -> str:
        """Decodes input_filepath in output_filepath"""
        raise Exception("Not implemented")

    @lru_cache(maxsize=None)
    def check(self, verbose: bool) -> bool:
        """Checks whether the decoder can be run"""
        if hasattr(self, "binary") and self.binary:
            try:
                path = which(self.binary)
                if verbose and not path:
                    print(f"Binary {self.binary} can't be found to be executed")

                return path is not None
            except Exception:
                return False
        return True

    def __str__(self) -> str:
        return f"    {self.name}: {self.description}"


DECODERS = []


def register_decoder(cls: Type[Decoder]) -> Type[Decoder]:
    """Register a new decoder implementation"""
    # pylint: disable=global-statement
    global DECODERS
    # pylint: enable=global-statement
    DECODERS.append(cls())
    DECODERS.sort(key=lambda dec: dec.name)
    return cls
