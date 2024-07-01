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

from functools import lru_cache
from typing import Optional, Tuple
import shlex
import subprocess
import re

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command, run_command_with_output

FFMPEG_TPL = "{} -nostdin -i {} {} -vf {}format=pix_fmts={} -f rawvideo {}"


@lru_cache(maxsize=128)
def _run_ffmpeg_command(
    binary: str,
    *args: str,
    verbose: bool = False,
) -> str:
    """Runs a ffmpeg command and returns the output or an empty string"""
    try:
        return run_command_with_output(
            [binary, "-hide_banner", *args],
            verbose=verbose,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def output_format_to_ffformat(output_format: OutputFormat) -> str:
    """Return GStreamer pixel format"""
    mapping = {
        OutputFormat.YUV420P: "nv12",
        OutputFormat.YUV422P: "nv12",  # vulkan
        OutputFormat.YUV420P10LE: "p010",
        OutputFormat.YUV422P10LE: "p012",
    }
    if output_format not in mapping:
        raise Exception(
            f"No matching output format found in FFmpeg for {output_format}"
        )
    return mapping[output_format]


class FFmpegDecoder(Decoder):
    """Generic class for FFmpeg decoder"""

    binary = "ffmpeg"
    api = ""
    wrapper = False
    hw_download = False
    init_device = ""

    def __init__(self) -> None:
        super().__init__()
        self.name = f'FFmpeg-{self.codec.value}{"-" + self.api if self.api else ""}'
        self.description = f'FFmpeg {self.codec.value} {self.api if self.hw_acceleration else "SW"} decoder'
        self.ffmpeg_version: Optional[Tuple[int, ...]] = None

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
        cmd = self.binary
        if self.hw_acceleration:
            if self.init_device:
                cmd += f' -init_hw_device "{self.init_device}" -hwaccel_output_format {self.api.lower()}'
            if self.wrapper:
                cmd += f" -c:v {self.api.lower()}"
            else:
                cmd += f" -hwaccel {self.api.lower()}"
        passthrough = "-fps_mode passthrough"
        if self.ffmpeg_version and self.ffmpeg_version < (5, 1):
            passthrough = "-vsync passthrough"
        download = ""
        if self.hw_acceleration and self.hw_download:
            download = f"hwdownload,format={output_format_to_ffformat(output_format)},"
        command = shlex.split(
            FFMPEG_TPL.format(
                cmd,
                input_filepath,
                passthrough,
                download,
                str(output_format.value),
                output_filepath,
            )
        )
        run_command(command, timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Checks whether the decoder can be run"""
        if not super().check(verbose):
            return False

        # Get ffmpeg version
        output = _run_ffmpeg_command(self.binary, "-version", verbose=verbose)
        version = re.search(r" version n?(\d+)\.(\d+)(?:\.(\d+))?", output)
        self.ffmpeg_version = tuple(map(int, version.groups())) if version else None

        if not self.hw_acceleration:
            return True

        # Check if hw decoder or hwaccel is supported
        command = "-decoders" if self.wrapper else "-hwaccels"
        output = _run_ffmpeg_command(self.binary, command, verbose=verbose)
        api = re.escape(self.api.lower())
        return re.search(rf"\s+{api}\s+", output) is not None


@register_decoder
class FFmpegH264Decoder(FFmpegDecoder):
    """FFmpeg SW decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265Decoder(FFmpegDecoder):
    """FFmpeg SW decoder for H.265"""

    codec = Codec.H265


@register_decoder
class FFmpegVP8Decoder(FFmpegDecoder):
    """FFmpeg SW decoder for VP8"""

    codec = Codec.VP8


@register_decoder
class FFmpegVP9Decoder(FFmpegDecoder):
    """FFmpeg SW decoder for VP9"""

    codec = Codec.VP9


class FFmpegVaapiDecoder(FFmpegDecoder):
    """Generic class for FFmpeg VAAPI decoder"""

    hw_acceleration = True
    api = "VAAPI"


@register_decoder
class FFmpegH264VaapiDecoder(FFmpegVaapiDecoder):
    """FFmpeg VAAPI decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265VaapiDecoder(FFmpegVaapiDecoder):
    """FFmpeg VAAPI decoder for H.265"""

    codec = Codec.H265


@register_decoder
class FFmpegVP8VaapiDecoder(FFmpegVaapiDecoder):
    """FFmpeg VAAPI decoder for VP8"""

    codec = Codec.VP8


@register_decoder
class FFmpegVP9VaapiDecoder(FFmpegVaapiDecoder):
    """FFmpeg VAAPI decoder for VP9"""

    codec = Codec.VP9


@register_decoder
class FFmpegAV1VaapiDecoder(FFmpegVaapiDecoder):
    """FFmpeg VAAPI decoder for AV1"""

    codec = Codec.AV1


class FFmpegVdpauDecoder(FFmpegDecoder):
    """Generic class for FFmpeg VDPAU decoder"""

    hw_acceleration = True
    api = "VDPAU"


@register_decoder
class FFmpegH264VdpauDecoder(FFmpegVdpauDecoder):
    """FFmpeg VDPAU decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265VdpauDecoder(FFmpegVdpauDecoder):
    """FFmpeg VDPAU decoder for H.265"""

    codec = Codec.H265


@register_decoder
class FFmpegAV1VdpauDecoder(FFmpegVdpauDecoder):
    """FFmpeg VDPAU decoder for AV1"""

    codec = Codec.AV1


class FFmpegDxva2Decoder(FFmpegDecoder):
    """Generic class for FFmpeg DXVA2 decoder"""

    hw_acceleration = True
    api = "DXVA2"


@register_decoder
class FFmpegH264Dxva2Decoder(FFmpegDxva2Decoder):
    """FFmpeg DXVA2 decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265Dxva2Decoder(FFmpegDxva2Decoder):
    """FFmpeg DXVA2 decoder for H.265"""

    codec = Codec.H265


class FFmpegD3d11vaDecoder(FFmpegDecoder):
    """Generic class for FFmpeg D3D11VA decoder"""

    hw_acceleration = True
    api = "D3D11VA"


@register_decoder
class FFmpegH264D3d11vaDecoder(FFmpegD3d11vaDecoder):
    """FFmpeg D3D11VA decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265D3d11vaDecoder(FFmpegD3d11vaDecoder):
    """FFmpeg D3D11VA decoder for H.265"""

    codec = Codec.H265


@register_decoder
class FFmpegVP8V4L2m2mDecoder(FFmpegDecoder):
    """FFmpeg V4L2m2m decoder for VP8"""

    codec = Codec.VP8
    hw_acceleration = True
    api = "vp8_v4l2m2m"
    wrapper = True


@register_decoder
class FFmpegVP9V4L2m2mDecoder(FFmpegDecoder):
    """FFmpeg V4L2m2m decoder for VP9"""

    codec = Codec.VP9
    hw_acceleration = True
    api = "vp9_v4l2m2m"
    wrapper = True


@register_decoder
class FFmpegH264V4L2m2mDecoder(FFmpegDecoder):
    """FFmpeg V4L2m2m decoder for H264"""

    codec = Codec.H264
    hw_acceleration = True
    api = "h264_v4l2m2m"
    wrapper = True


class FFmpegVulkanDecoder(FFmpegDecoder):
    """Generic class for FFmpeg Vulkan decoder"""

    hw_acceleration = True
    api = "Vulkan"
    init_device = "vulkan"
    hw_download = True


@register_decoder
class FFmpegH264VulkanDecoder(FFmpegVulkanDecoder):
    """FFmpeg Vulkan decoder for H.264"""

    codec = Codec.H264


@register_decoder
class FFmpegH265VulkanDecoder(FFmpegVulkanDecoder):
    """FFmpeg Vulkan decoder for H.265"""

    codec = Codec.H265


@register_decoder
class FFmpegAV1VulkanDecoder(FFmpegVulkanDecoder):
    """FFmpeg Vulkan decoder for AV1"""

    codec = Codec.AV1
