# Fluster - testing framework for decoders conformance
# Copyright (C) 2023, The ChromiumOS Authors.
#  Author: Alexandre Courbot <acourbot@chromium.org>
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


class CrosCodecsDecoder(Decoder):
    '''Generic class for cros-codecs decoder'''

    binary = 'ccdec'

    def __init__(self) -> None:
        super().__init__()
        self.name = f"ccdec-{self.codec.value}"
        self.description = f"{self.codec.value} cros-codecs decoder"

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

        formats = {
            OutputFormat.YUV420P: "i420",
            OutputFormat.YUV422P: "i422",
            OutputFormat.YUV420P10LE: "i010",
            OutputFormat.YUV420P12LE: "i012",
            OutputFormat.YUV422P10LE: "i210",
            OutputFormat.YUV422P12LE: "i212",
            OutputFormat.YUV444P: "i444",
            OutputFormat.YUV444P10LE: "i410",
            OutputFormat.YUV444P12LE: "i412",
        }

        output_fmt = ''
        try:
            output_fmt = formats[output_format]
        except KeyError as exception:
            raise Exception(
                f"Unsupported output format {output_format}") from exception

        if self.codec == Codec.H264:
            input_fmt = "h264"
        elif self.codec == Codec.H265:
            input_fmt = "h265"
        elif self.codec == Codec.VP8:
            input_fmt = "vp8"
        elif self.codec == Codec.VP9:
            input_fmt = "vp9"
        else:
            raise Exception(f"Unsupported input codec {self.codec}")

        run_command(
            [self.binary, input_filepath, "--output", output_filepath,
                "--input-format", input_fmt, "--output-format", output_fmt],
            timeout=timeout,
            verbose=verbose,
        )

        return file_checksum(output_filepath)


@register_decoder
class CrosCodecsH264Decoder(CrosCodecsDecoder):
    '''cros-codecs decoder for H.264'''
    codec = Codec.H264
    hw_acceleration = True
    api = 'VAAPI'


@register_decoder
class CrosCodecsH265Decoder(CrosCodecsDecoder):
    '''cros-codecs decoder for H.265'''
    codec = Codec.H265
    hw_acceleration = True
    api = 'VAAPI'


@register_decoder
class CrosCodecsVp8Decoder(CrosCodecsDecoder):
    '''cros-codecs decoder for VP8'''
    codec = Codec.VP8
    hw_acceleration = True
    api = 'VAAPI'


@register_decoder
class CrosCodecsVP9Decoder(CrosCodecsDecoder):
    '''cros-codecs decoder for VP9'''
    codec = Codec.VP9
    hw_acceleration = True
    api = 'VAAPI'
