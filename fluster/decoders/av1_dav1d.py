# Fluster - testing framework for decoders conformance
# Copyright (C) 2023, Igalia S.L.
#  Author: Charlie Turner <cturner@igalia.com>
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
from typing import Any, Dict, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


@register_decoder
class AV1Dav1dDecoder(Decoder):
    """dav1d decoder implementation"""

    name = "dav1d-AV1"
    description = "dav1d AV1 decoder"
    binary = "dav1d"
    codec = Codec.AV1

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
        """Decodes input_filepath in output_filepath"""
        fmt = "yuv"
        run_command(
            [
                self.binary,
                "--alllayers",
                "0",
                "--muxer",
                fmt,
                "-i",
                input_filepath,
                "-o",
                output_filepath,
            ],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)
