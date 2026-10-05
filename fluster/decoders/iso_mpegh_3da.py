# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
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

import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, NotSupportedError, register_decoder
from fluster.utils import file_checksum

# Bits per sample of the decoded WAV, fluster compares 16 bit WAV files
OUTPUT_BIT_DEPTH = 16

# Optional parameters of the test vectors -> command line options of the decoder
OPTIONS = {
    "preset_id": "-Pr",
    "target_layout": "-cicpOut",
    "target_loudness": "-targetLoudnessLevel",
    "drc_effect_type": "-drcEffectTypeRequest",
}


@register_decoder
class ISOMPEGH3DADecoder(Decoder):
    """ISO/IEC 23008-6 MPEG-H 3D Audio reference decoder implementation"""

    name = "ISO-MPEGH-3DA"
    description = "ISO MPEG-H 3D Audio reference decoder"
    codec = Codec.MPEGH_3DA
    binary = "3DAudioDecoder"
    is_reference = True

    @staticmethod
    def _options(optional_params: Optional[Dict[str, Any]]) -> List[str]:
        """Translate the optional parameters of a test vector to command line options"""
        options: List[str] = []
        for param, value in (optional_params or {}).items():
            if param not in OPTIONS:
                raise NotSupportedError(f"Unknown parameter {param} for {ISOMPEGH3DADecoder.name}")
            options += [OPTIONS[param], str(value)]
        return options

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
        command = [
            os.path.abspath(shutil.which(self.binary) or self.binary),
            "-if",
            os.path.abspath(input_filepath),
            "-of",
            "decoded.wav",
            "-bitdepth",
            str(OUTPUT_BIT_DEPTH),
            *self._options(optional_params),
        ]
        # The decoder writes its intermediate files with fixed names in the working directory, so every run gets its own
        with tempfile.TemporaryDirectory() as workdir:
            output = None if verbose else subprocess.DEVNULL
            subprocess.run(command, cwd=workdir, stdout=output, stderr=output, check=True, timeout=timeout)
            shutil.move(os.path.join(workdir, "decoded.wav"), output_filepath)
        # Some bitstreams are written with another bit depth whatever -bitdepth says, they can not be compared
        with open(output_filepath, "rb") as wav:
            header = wav.read(512)
        fmt = header.index(b"fmt ")  # the decoder writes a LIST chunk before it
        bit_depth = int.from_bytes(header[fmt + 22 : fmt + 24], "little")  # bits per sample
        if bit_depth != OUTPUT_BIT_DEPTH:
            raise NotSupportedError(f"{self.name} decoded {os.path.basename(input_filepath)} at {bit_depth} bits")
        return file_checksum(output_filepath)
