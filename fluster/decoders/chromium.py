# Fluster - testing framework for decoders conformance
# Copyright (C) 2021, Fluendo, S.A.
#  Author: Manuel Jimeno Martínez <mjimeno@fluendo.com>, Fluendo, S.A.
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

from functools import lru_cache
from typing import Any, Dict, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder

try:
    from fluster_chromium import main  # type: ignore

    HAS_FLUSTER_CHROMIUM = True
except ImportError:
    HAS_FLUSTER_CHROMIUM = False


@register_decoder
class ChromiumH264(Decoder):
    """H264 class for Chromium decoder"""

    provider = "Chromium"
    codec = Codec.H264
    description = "This is an implementation for the Chromium decoder"

    def __init__(self) -> None:
        super().__init__()
        if not self.name:
            self.name = f"{self.provider}-{self.codec.value}"
        self.description = f"{self.provider} {self.codec.value} decoder for Chromium"

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
        return str(main(input_filepath))

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        if verbose and not HAS_FLUSTER_CHROMIUM:
            print("Decoder is not available, module fluster-chromium not installed")
        return HAS_FLUSTER_CHROMIUM
