# Fluster - testing framework for decoders conformance
# Copyright (C) 2021, Fluendo, S.A.
# Author: Martín Cesarini <mcesarini@fluendo.com>, Fluendo, S.A.
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

import glob
import os

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


@register_decoder
class ISOAACDecoder(Decoder):
    """ISO MPEG4 AAC reference decoder implementation for error resilient test vectors"""

    name = "ISO-MPEG4-AAC-ER"
    description = "ISO MPEG4 AAC ER reference decoder"
    codec = Codec.AAC
    binary = "mp4audec"

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
        output_filepath += ".raw"
        run_command(
            [self.binary, "-o", output_filepath, input_filepath],
            timeout=timeout,
            verbose=verbose,
        )
        base_output = output_filepath[:-4]
        pcm_out_f00_file = f"{base_output}_f00.raw"

        if os.path.exists(pcm_out_f00_file):
            return file_checksum(pcm_out_f00_file)

        output_files = glob.glob(f"{base_output}_f[0-9][0-9].raw")

        for pcm_file in output_files:
            return file_checksum(pcm_file)

        return file_checksum(output_filepath)
