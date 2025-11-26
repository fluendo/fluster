# Fluster - testing framework for decoders conformance
# Copyright (C) 2024, Fluendo, S.A.
#  Author: Rubén Sánchez <rsanchez@fluendo.com>, Fluendo, S.A.
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
from typing import Any, Dict, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


@register_decoder
class ISOAACDecoder(Decoder):
    """ISO MPEG2 AAC reference decoder implementation"""

    name = "ISO-MPEG2-AAC"
    description = "ISO MPEG2 AAC reference decoder"
    codec = Codec.AAC
    binary = "aacdec_mc"
    is_reference = True

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
        # Addition of .pcm as extension is a must. If it is something else, e.g. ".out" the decoder will output a
        # ".wav", which is undesirable.
        output_filepath += ".pcm"
        run_command(
            [self.binary, input_filepath, output_filepath],
            timeout=timeout,
            verbose=verbose,
        )

        base_output = output_filepath[:-4]
        pcm_out_f00_file = f"{base_output}_f00.pcm"

        if os.path.exists(pcm_out_f00_file):
            return file_checksum(pcm_out_f00_file)

        output_files = glob.glob(f"{base_output}_f[0-9][0-9].pcm")

        for pcm_file in output_files:
            return file_checksum(pcm_file)

        return file_checksum(output_filepath)
