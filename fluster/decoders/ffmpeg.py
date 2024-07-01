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
from typing import Dict, Optional, Tuple
import subprocess
import re

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command, run_command_with_output


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


class FFmpegDecoder(Decoder):
    """Generic class for FFmpeg decoder"""

    binary = "ffmpeg"
    api = ""
    wrapper = False
    hw_download = False
    hw_download_mapping: Dict[OutputFormat, str] = {}
    init_hw_device = ""
    hw_output_format = ""
    thread_count = 1

    def __init__(self) -> None:
        super().__init__()
        self.name = f'FFmpeg-{self.codec.value}{"-" + self.api if self.api else ""}'
        self.description = f'FFmpeg {self.codec.value} {self.api if self.hw_acceleration else "SW"} decoder'
        self.ffmpeg_codec: Optional[str] = None
        self.ffmpeg_version: Optional[Tuple[int, ...]] = None
        self.use_md5_muxer: bool = False

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
        # pylint: disable=too-many-branches
        command = [self.binary, "-hide_banner", "-nostdin"]

        # Hardware acceleration
        if self.hw_acceleration:
            if self.init_hw_device:
                command.extend(["-init_hw_device", self.init_hw_device])
            if not self.wrapper:
                command.extend(["-hwaccel", self.api.lower()])
            if self.hw_output_format:
                command.extend(["-hwaccel_output_format", self.hw_output_format])

        # Number of threads
        if self.thread_count:
            command.extend(["-threads", str(self.thread_count)])

        # Codec
        if self.hw_acceleration and self.wrapper:
            command.extend(["-codec", self.api.lower()])
        elif self.ffmpeg_codec:
            command.extend(["-codec", self.ffmpeg_codec])

        # Input file
        command.extend(["-i", input_filepath])

        # Passthrough timestamp from the demuxer to the muxer
        if self.ffmpeg_version and self.ffmpeg_version < (5, 1):
            command.extend(["-vsync", "passthrough"])
        else:
            command.extend(["-fps_mode", "passthrough"])

        # Hardware download
        download = ""
        if self.hw_acceleration and self.hw_download:
            if output_format not in self.hw_download_mapping:
                raise Exception(
                    f"No matching ffmpeg pixel format found for {output_format}"
                )
            download = f"hwdownload,format={self.hw_download_mapping[output_format]},"

        # Output format filter
        command.extend(["-filter", f"{download}format=pix_fmts={output_format.value}"])

        # MD5 muxer
        if self.use_md5_muxer and not keep_files:
            command.extend(["-f", "md5", "-"])
            output = run_command_with_output(command, timeout=timeout, verbose=verbose)
            md5sum = re.search(r"MD5=([0-9a-fA-F]+)\s*", output)
            if not md5sum:
                raise Exception("No MD5 found in the program trace.")
            return md5sum.group(1).lower()

        # Output file
        command.extend(["-f", "rawvideo", output_filepath])
        run_command(command, timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Checks whether the decoder can be run"""
        if not super().check(verbose):
            return False

        # Check if codec is supported
        codec_mapping = {
            Codec.H264: "h264",
            Codec.H265: "hevc",
            Codec.VP8: "vp8",
            Codec.VP9: "vp9",
            Codec.AV1: "av1",
        }
        if self.codec not in codec_mapping:
            return False
        self.ffmpeg_codec = codec_mapping[self.codec]

        # Get ffmpeg version
        output = _run_ffmpeg_command(self.binary, "-version", verbose=verbose)
        version = re.search(r" version n?(\d+)\.(\d+)(?:\.(\d+))?", output)
        self.ffmpeg_version = tuple(map(int, version.groups())) if version else None

        # Check if codec can be used
        output = _run_ffmpeg_command(self.binary, "-codecs", verbose=verbose)
        codec = re.escape(self.ffmpeg_codec)
        if re.search(rf"\s+{codec}\s+", output) is None:
            return False

        # Check if MD5 muxer can be used
        output = _run_ffmpeg_command(self.binary, "-formats", verbose=verbose)
        muxer = re.escape("md5")
        self.use_md5_muxer = re.search(rf"E\s+{muxer}\s+", output) is not None

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
    init_hw_device = "vulkan"
    hw_output_format = "vulkan"
    hw_download = True
    hw_download_mapping = {
        OutputFormat.YUV420P: "nv12",
        OutputFormat.YUV422P: "nv12",
        OutputFormat.YUV420P10LE: "p010",
        OutputFormat.YUV422P10LE: "p012",
    }


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
