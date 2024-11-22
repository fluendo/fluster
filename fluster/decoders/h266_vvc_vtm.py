# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Ruben Gonzalez <rgonzalezs@fluendo.com>, Fluendo, S.A.
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
class H266VVCVTMDecoder(Decoder):
    """VVdeC H.266/VVC reference decoder implementation"""

    name = "VVCSoftware_VTM-H266"
    description = "VVCSoftware_VTM H.266/VVC reference decoder"
    codec = Codec.H266
    binary = "DecoderApp"

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
        # pylint: disable=unused-argument
        run_command(
            [self.binary, "-b", input_filepath, "-o", output_filepath],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)
