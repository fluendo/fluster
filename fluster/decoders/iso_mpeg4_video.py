# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
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
import os
import subprocess
from typing import Tuple

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import normalize_binary_cmd, run_command


@register_decoder
class ISOMPEG4VDecoder(Decoder):
    """ISO MPEG4 Video reference decoder implementation"""

    name = "ISO-MPEG4-VIDEO"
    description = "ISO MPEG4 Video reference decoder"
    codec = Codec.MPEG4_VIDEO
    binary = "vm_dec"
    is_reference = True

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
    ) -> str:
        """Decodes input_filepath to output_filepath"""
        width, height = self._get_video_resolution(input_filepath, verbose)

        run_command(
            [self.binary, input_filepath, output_filepath, str(width), str(height)],
            timeout=timeout,
            verbose=verbose,
        )

        return output_filepath

    @staticmethod
    def _get_video_resolution(input_filepath: str, verbose: bool = False) -> Tuple[int, int]:
        """Get resolution using ffprobe"""
        if not os.path.exists(input_filepath):
            raise FileNotFoundError(f"Input file '{input_filepath}' does not exist")

        ffprobe = normalize_binary_cmd("ffprobe")
        command = [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            input_filepath,
        ]

        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
        result_lines = result.stdout.strip().splitlines()

        if len(result_lines) < 2:
            raise ValueError("ffprobe returned insufficient output")

        width = int(result_lines[0])
        height = int(result_lines[1])

        if verbose:
            print(f"Detected resolution: {width}x{height}")

        return width, height
