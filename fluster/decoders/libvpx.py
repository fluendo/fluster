# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
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

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


class VPXDecoder(Decoder):
    """Generic class for VPX reference decoder"""

    name = ""
    description = ""
    binary = "vpxdec"
    codec = Codec.NONE

    def __init__(self) -> None:
        super().__init__()
        self.name = f"libvpx-{self.codec.value}"
        self.description = f"{self.codec.value} reference decoder"

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
    ) -> str:
        """Decodes input_filepath in output_filepath"""
        fmt = None
        if output_format == OutputFormat.YUV420P:
            fmt = "--i420"
        else:
            fmt = "--rawvideo"

        run_command(
            [self.binary, fmt, input_filepath, "-o", output_filepath],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)


@register_decoder
class VP8Decoder(VPXDecoder):
    """VP8 reference decoder implementation"""

    codec = Codec.VP8


@register_decoder
class VP9Decoder(VPXDecoder):
    """VP9 reference decoder implementation"""

    codec = Codec.VP9
