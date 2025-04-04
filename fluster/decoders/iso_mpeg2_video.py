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
import tempfile

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


@register_decoder
class ISOMPEG2VDecoder(Decoder):
    """ISO MPEG2 Video reference decoder implementation"""

    name = "ISO-MPEG2-VIDEO"
    description = "ISO MPEG2 Video reference decoder"
    codec = Codec.MPEG2_VIDEO
    binary = "mpeg2decode"
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
        """Decodes input_filepath in output_filepath"""
        with tempfile.TemporaryDirectory() as temp_dir:
            run_command(
                [self.binary, "-b", input_filepath, "-f", "-r", "-o0", os.path.join(temp_dir, "rec%d")],
                timeout=timeout,
                verbose=verbose,
            )
            self._merge_yuv_files(temp_dir, output_filepath)
            checksum = file_checksum(output_filepath)

        if not keep_files:
            os.remove(output_filepath)

        return checksum

    @staticmethod
    def _merge_yuv_files(input_dir: str, output_filepath: str) -> None:
        """Merge YUV frames into an only raw .yuv file for mpeg2 video test suite"""
        num_frames = len(glob.glob(os.path.join(input_dir, "rec*.Y")))

        if num_frames == 0:
            raise ValueError("No frames were decoded")

        with open(output_filepath, "wb") as output_file:
            for frame_num in range(num_frames):
                frame_name = f"rec{frame_num}"
                y_file = os.path.join(input_dir, f"{frame_name}.Y")
                u_file = os.path.join(input_dir, f"{frame_name}.U")
                v_file = os.path.join(input_dir, f"{frame_name}.V")

                if not (os.path.exists(y_file) and os.path.exists(u_file) and os.path.exists(v_file)):
                    print(f"Warning: Files for frame {frame_name} not found in {input_dir}")
                    continue

                chunk_size = 1024
                for plane_file in [y_file, u_file, v_file]:
                    with open(plane_file, "rb") as file:
                        chunk = file.read(chunk_size)
                        while chunk:
                            output_file.write(chunk)
                            chunk = file.read(chunk_size)
