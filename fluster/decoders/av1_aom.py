# Fluster - testing framework for decoders conformance
# Copyright (C) 2021, Collabora.
#  Author: Daniel Almeida <daniel.almeida@collabora.com>
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


@register_decoder
class AV1AOMDecoder(Decoder):
    """libaom AV1 reference decoder implementation"""

    name = "libaom-AV1"
    description = "libaom AV1 reference decoder"
    binary = "aomdec"
    codec = Codec.AV1

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
        # pylint: disable=unused-argument
        run_command(
            [self.binary, fmt, input_filepath, "-o", output_filepath],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)
