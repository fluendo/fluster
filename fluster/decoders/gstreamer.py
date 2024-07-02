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

# pylint: disable=too-many-lines

import shlex
import subprocess
from functools import lru_cache
from typing import Optional, List

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import (
    file_checksum,
    run_command,
    run_command_with_output,
    normalize_binary_cmd,
)

PIPELINE_TPL = "{} --no-fault filesrc location={} ! {} ! {} ! {} ! {} {}"


@lru_cache(maxsize=None)
def gst_element_exists(element: str) -> bool:
    """Check if an element exists in current GStreamer installation"""
    inspect_exe = normalize_binary_cmd("gst-inspect-1.0")

    try:
        subprocess.run(
            [inspect_exe, "--exists", element],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return False


def output_format_to_gst(output_format: OutputFormat) -> str:
    """Return GStreamer pixel format"""
    mapping = {
        OutputFormat.GRAY: "GRAY8",
        OutputFormat.GRAY16LE: "GRAY16_LE",
        OutputFormat.YUV420P: "I420",
        OutputFormat.YUV422P: "Y42B",
        OutputFormat.YUV420P10LE: "I420_10LE",
        OutputFormat.YUV422P10LE: "I422_10LE",
        OutputFormat.YUV420P12LE: "I420_12LE",
        OutputFormat.YUV422P12LE: "I422_12LE",
        OutputFormat.YUV444P: "Y444",
        OutputFormat.YUV444P10LE: "Y444_10LE",
        OutputFormat.YUV444P12LE: "Y444_12LE",
    }
    if output_format not in mapping:
        raise Exception(
            f"No matching output format found in GStreamer for {output_format}"
        )
    return mapping[output_format]


class GStreamer(Decoder):
    """Base class for GStreamer decoders"""

    decoder_bin = ""
    cmd = ""
    caps = ""
    gst_api = ""
    api = ""
    provider = ""
    sink = ""

    def __init__(self) -> None:
        super().__init__()
        if not self.name:
            self.name = (
                f"{self.provider}-{self.codec.value}-{self.api}-Gst{self.gst_api}"
            )
        self.description = f"{self.provider} {self.codec.value} {self.api} decoder for GStreamer {self.gst_api}"
        self.cmd = normalize_binary_cmd(self.cmd)

        if not gst_element_exists(self.sink):
            self.sink = "filesink"

    def gen_pipeline(
        self,
        input_filepath: str,
        output_filepath: Optional[str],
        output_format: OutputFormat,
    ) -> str:
        """Generate the GStreamer pipeline used to decode the test vector"""
        # pylint: disable=unused-argument
        output = f"location={output_filepath}" if output_filepath else ""
        return PIPELINE_TPL.format(
            self.cmd, input_filepath, self.decoder_bin, self.caps, self.sink, output
        )

    def parse_videocodectestsink_md5sum(self, data: List[str]) -> str:
        """Parse the MD5 sum out of commandline output produced when using
        videocodectestsink."""
        for line in data:
            pattern = (
                "conformance/checksum, checksum-type=(string)MD5, checksum=(string)"
            )
            sum_start = line.find(pattern)
            # pylint: disable=no-else-continue
            if sum_start <= 0:
                # Skip to the next iteration if sum_start is less than or equal to 0
                continue
            else:
                sum_start += len(pattern)
                sum_end = line[sum_start:].find(";")
                # pylint: disable=no-else-continue
                if sum_end <= 0:
                    # Skip to the next iteration if sum_end is less than or equal to 0
                    continue
                else:
                    sum_end += sum_start
                    return line[sum_start:sum_end]

        raise Exception("No MD5 found in the program trace.")

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
    ) -> str:
        """Decode the test vector and do the checksum"""
        # When using videocodectestsink we can avoid writing files to disk
        # completely, or avoid a full raw file read in order to compute the MD5
        # SUM.
        if self.sink == "videocodectestsink":
            output_param = output_filepath if keep_files else None
            pipeline = self.gen_pipeline(input_filepath, output_param, output_format)
            command = shlex.split(pipeline)
            command.append("-m")
            data = run_command_with_output(
                command, timeout=timeout, verbose=verbose
            ).splitlines()
            return self.parse_videocodectestsink_md5sum(data)

        pipeline = self.gen_pipeline(input_filepath, output_filepath, output_format)
        run_command(shlex.split(pipeline), timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Check if GStreamer decoder is valid (better than gst-inspect)"""
        # pylint: disable=broad-except
        try:
            binary = normalize_binary_cmd(f"gst-launch-{self.gst_api}")
            pipeline = f"{binary} --no-fault appsrc num-buffers=0 ! {self.decoder_bin} ! fakesink"
            run_command(shlex.split(pipeline), verbose=verbose)
        except Exception:
            return False
        return True


class GStreamer10Video(GStreamer):
    """Base class for GStreamer 1.x video decoders"""

    cmd = "gst-launch-1.0"
    caps = "video/x-raw"
    gst_api = "1.0"
    sink = "videocodectestsink"
    provider = "GStreamer"

    def gen_pipeline(
        self,
        input_filepath: str,
        output_filepath: Optional[str],
        output_format: OutputFormat,
    ) -> str:
        caps = f"{self.caps} ! videoconvert dither=none ! video/x-raw,format={output_format_to_gst(output_format)}"
        output = f"location={output_filepath}" if output_filepath else ""
        return PIPELINE_TPL.format(
            self.cmd,
            input_filepath,
            "parsebin",
            self.decoder_bin,
            caps,
            self.sink,
            output,
        )


class GStreamer10Audio(GStreamer):
    """Base class for GStreamer 1.x audio decoders"""

    cmd = "gst-launch-1.0"
    caps = "audio/x-raw"
    gst_api = "1.0"
    sink = "filesink"
    provider = "GStreamer"


class GStreamer010Video(GStreamer):
    """Base class for GStreamer 0.10 video decoders"""

    cmd = "gst-launch-0.10"
    caps = "video/x-raw-yuv"
    gst_api = "0.10"
    sink = "videocodectestsink"
    provider = "GStreamer"


@register_decoder
class GStreamerLibavH264(GStreamer10Video):
    """GStreamer H.264 Libav decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " avdec_h264 "
    api = "Libav"


@register_decoder
class GStreamerLibavH265(GStreamer10Video):
    """GStreamer H.265 Libav decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " avdec_h265 "
    api = "Libav"


@register_decoder
class GStreamerLibavVP8(GStreamer10Video):
    """GStreamer VP8 Libav decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " avdec_vp8 "
    api = "Libav"


@register_decoder
class GStreamerLibavVP9(GStreamer10Video):
    """GStreamer VP9 Libav decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " avdec_vp9"
    api = "Libav"


@register_decoder
class GStreamerVaapiH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 VAAPI decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " vaapih265dec "
    api = "VAAPI"


@register_decoder
class GStreamerVaH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 VA decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " vah265dec "
    api = "VA"


@register_decoder
class GStreamerMsdkH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 Intel MSDK decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " msdkh265dec "
    api = "MSDK"


@register_decoder
class GStreamerNvdecH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 NVDEC decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " nvh265dec "
    api = "NVDEC"


@register_decoder
class GStreamerNvdecSLH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 NVDEC stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " nvh265sldec "
    api = "NVDECSL"


@register_decoder
class GStreamerD3d11H265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 D3D11 decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " d3d11h265dec "
    api = "D3D11"


@register_decoder
class GStreamerD3d12H265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 D3D12 decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " d3d12h265dec "
    api = "D3D12"


@register_decoder
class GStreamerV4l2CodecsH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 V4L2 stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " v4l2slh265dec "
    api = "V4L2SL"


@register_decoder
class GStreamerV4l2H265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 V4L2 stateful decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " v4l2h265dec "
    api = "V4L2"


@register_decoder
class GStreamerVaapiH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 VAAPI decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " vaapih264dec "
    api = "VAAPI"


@register_decoder
class GStreamerVaH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 VA decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " vah264dec "
    api = "VA"


@register_decoder
class GStreamerMsdkH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 Intel MSDK decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " msdkh264dec "
    api = "MSDK"


@register_decoder
class GStreamerNvdecH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 NVDEC decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " nvh264dec "
    api = "NVDEC"


@register_decoder
class GStreamerNvdecSLH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 NVDEC stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " nvh264sldec "
    api = "NVDECSL"


@register_decoder
class GStreamerD3d11H264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 D3D11 decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " d3d11h264dec "
    api = "D3D11"


@register_decoder
class GStreamerD3d12H264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 D3D12 decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " d3d12h264dec "
    api = "D3D12"


@register_decoder
class GStreamerV4l2CodecsH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 V4L2 stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " v4l2slh264dec "
    api = "V4L2SL"


@register_decoder
class GStreamerV4l2H264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 V4L2 stateful decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " v4l2h264dec "
    api = "V4L2"


@register_decoder
class GStreamerVulkanH264Gst10Decoder(GStreamer10Video):
    """GStreamer H.264 Vulkan stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " vulkanh264dec ! vulkandownload "
    api = "Vulkan"


@register_decoder
class GStreamerVulkanH265Gst10Decoder(GStreamer10Video):
    """GStreamer H.265 Vulkan stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " vulkanh265dec ! vulkandownload "
    api = "Vulkan"


@register_decoder
class GStreamerV4l2CodecsVP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 V4L2 stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " v4l2slvp8dec "
    api = "V4L2SL"


@register_decoder
class GStreamerV4l2VP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 V4L2 stateful decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " v4l2vp8dec "
    api = "V4L2"


@register_decoder
class GStreamerLibvpxVP8(GStreamer10Video):
    """GStreamer VP8 Libvpx decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " vp8dec "
    api = "libvpx"


@register_decoder
class GStreamerVaapiVP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 VAAPI decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " vaapivp8dec "
    api = "VAAPI"


@register_decoder
class GStreamerVaVP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 VA decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " vavp8dec "
    api = "VA"


@register_decoder
class GStreamerD3d11VP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 D3D11 decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " d3d11vp8dec "
    api = "D3D11"


@register_decoder
class GStreamerNvdecVP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 NVDEC decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " nvvp8dec "
    api = "NVDEC"


@register_decoder
class GStreamerNvdecSLVP8Gst10Decoder(GStreamer10Video):
    """GStreamer VP8 NVDEC stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.VP8
    decoder_bin = " nvvp8sldec "
    api = "NVDECSL"


@register_decoder
class GStreamerV4l2CodecsVP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 V4L2 stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " v4l2slvp9dec "
    api = "V4L2SL"


@register_decoder
class GStreamerV4l2VP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 V4L2 stateful decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " v4l2vp9dec "
    api = "V4L2"


@register_decoder
class GStreamerVaAV1Gst10Decoder(GStreamer10Video):
    """GStreamer AV1 VA decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " vaav1dec "
    api = "VA"


@register_decoder
class GStreamerV4l2CodecsAV1Gst10Decoder(GStreamer10Video):
    """GStreamer AV1 V4L2 stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " v4l2slav1dec "
    api = "V4L2SL"


@register_decoder
class GStreamerD3d11AV1Gst10Decoder(GStreamer10Video):
    """GStreamer AV1 D3D11 decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " d3d11av1dec "
    api = "D3D11"


@register_decoder
class GStreamerD3d12AV1Gst10Decoder(GStreamer10Video):
    """GStreamer AV1 D3D12 decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " d3d12av1dec "
    api = "D3D12"


@register_decoder
class GStreamerLibvpxVP9(GStreamer10Video):
    """GStreamer VP9 Libvpx decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " vp9dec  "
    api = "libvpx"


@register_decoder
class GStreamerVaapiVP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 VAAPI decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " vaapivp9dec "
    api = "VAAPI"


@register_decoder
class GStreamerVaapiAV1Gst10Decoder(GStreamer10Video):
    """GStreamer AV1 VAAPI decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " vaapiav1dec "
    api = "VAAPI"


@register_decoder
class GStreamerDav1dAV1Decoder(GStreamer10Video):
    """GStreamer AV1 dav1d decoder implementation for GStreamer 1.0"""

    codec = Codec.AV1
    decoder_bin = " dav1ddec "
    api = "dav1d"


@register_decoder
class GStreamerVaVP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 VA decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " vavp9dec "
    api = "VA"


@register_decoder
class GStreamerD3d11VP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 D3D11 decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " d3d11vp9dec "
    api = "D3D11"


@register_decoder
class GStreamerD3d12VP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 D3D12 decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " d3d12vp9dec "
    api = "D3D12"


@register_decoder
class GStreamerNvdecVP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 NVDEC decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " nvvp9dec "
    api = "NVDEC"


@register_decoder
class GStreamerNvdecSLVP9Gst10Decoder(GStreamer10Video):
    """GStreamer VP9 NVDEC stateless decoder implementation for GStreamer 1.0"""

    codec = Codec.VP9
    decoder_bin = " nvvp9sldec "
    api = "NVDECSL"


@register_decoder
class GStreamerVVdeCH266Decoder(GStreamer10Video):
    """GStreamer H.266/VVC VVdeC decoder implementation for GStreamer 1.0"""

    codec = Codec.H266
    decoder_bin = " vvdec "
    api = "VVdeC"


@register_decoder
class FluendoH265Gst10Decoder(GStreamer10Video):
    """Fluendo H.265 software decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " fluh265dec "
    provider = "Fluendo"
    api = "SW"


@register_decoder
class FluendoH265Gst010Decoder(GStreamer010Video):
    """Fluendo H.265 software decoder implementation for GStreamer 0.10"""

    codec = Codec.H265
    decoder_bin = " fluh265dec "
    provider = "Fluendo"
    api = "SW"


@register_decoder
class FluendoH264Gst10Decoder(GStreamer10Video):
    """Fluendo H.264 software decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " fluh264dec "
    provider = "Fluendo"
    api = "SW"


@register_decoder
class FluendoH264Gst010Decoder(GStreamer010Video):
    """Fluendo H.264 software decoder implementation for GStreamer 0.10"""

    codec = Codec.H264
    decoder_bin = " fluh264dec "
    provider = "Fluendo"
    api = "SW"


@register_decoder
class FluendoH264VAGst10Decoder(GStreamer10Video):
    """Fluendo H.264 hardware decoder implementation for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " fluhwvadec "
    provider = "Fluendo"
    api = "HW"


class FluendoH265VAGst10DecoderBase(GStreamer10Video):
    """Fluendo H.265 hardware decoder implementation for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin_tmpl = (
        " video/x-h265,stream-format={stream_format},alignment={alignment} !"
        " fluhwvadec "
    )
    provider = "Fluendo"
    api = "HW"
    stream_format: str = ""
    alignment: str = ""

    def __init__(self) -> None:
        super().__init__()
        self.name = self._translator(self.name)
        self.description = self._translator(self.description)
        self.decoder_bin = self.decoder_bin_tmpl.format(
            stream_format=self.stream_format, alignment=self.alignment
        )

    def _translator(self, target_val: str) -> str:
        new_val = f"{self.codec.value}-{self.stream_format}-{self.alignment}"
        return target_val.replace(self.codec.value, new_val)


@register_decoder
class FluendoH265ByteStreamAuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (byte-stream/au) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "byte-stream"
    alignment = "au"


@register_decoder
class FluendoH265ByteStreamNalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (byte-stream/nal) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "byte-stream"
    alignment = "nal"


@register_decoder
class FluendoH265Hev1AuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (hev1/au) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "hev1"
    alignment = "au"


@register_decoder
class FluendoH265Hvc1AuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (hvc1/au) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "hvc1"
    alignment = "au"


@register_decoder
class FluendoH265Hev1NalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (hev1/nal) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "hev1"
    alignment = "nal"


@register_decoder
class FluendoH265Hvc1NalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    """
    Fluendo H.265 (hvc1/nal) hardware decoder implementation for GStreamer 1.0
    """

    stream_format = "hvc1"
    alignment = "nal"


@register_decoder
class FluendoFluVAH265DecGst10Decoder(GStreamer10Video):
    """Fluendo H.265 separated plugin hardware decoder for GStreamer 1.0"""

    codec = Codec.H265
    decoder_bin = " fluhwvah265dec "
    provider = "Fluendo"
    api = "HW"
    name = f"{provider}-{codec.value}-{api}-hwvah265dec-Gst1.0"


@register_decoder
class FluendoFluVAH264DecGst10Decoder(GStreamer10Video):
    """Fluendo H.264 separated plugin hardware decoder for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = " fluhwvah264dec "
    provider = "Fluendo"
    api = "HW"
    name = f"{provider}-{codec.value}-{api}-hwvah264dec-Gst1.0"


@register_decoder
class FluendoFluAACDecGst10Decoder(GStreamer10Audio):
    """Fluendo AAC plugin decoder for GStreamer 1.0"""

    def __init__(self) -> None:
        self.codec = Codec.AAC
        self.decoder_bin = "fluaacdec trim=0"
        self.provider = "Fluendo"
        self.api = "SW"
        self.caps = self.caps + ",format=S16LE"
        super().__init__()


@register_decoder
class FluendoFluLCEVCVAH264DecGst10Decoder(GStreamer10Video):
    """LCEVC-H264 decoder for GStreamer 1.0"""

    codec = Codec.H264
    decoder_bin = "flulcevchwvah264dec"
    provider = "Fluendo"
    api = "HW"
    name = f"{provider}-{codec.value}-{api}-lcevchwvah264dec-Gst1.0"


class FluendoFluHWVAH264DecBase(GStreamer10Video):
    """Fluendo base class for fluhwva{backend}h264dec elements"""

    provider = "Fluendo"
    api = "INVALID"
    codec = Codec.H264
    decoder_bin_tmpl = " fluhwva{backend}h264dec "

    def __init__(self) -> None:
        self.decoder_bin = self.decoder_bin_tmpl.format(backend=self.api.lower())
        super().__init__()


class FluendoFluHWVAH265DecBase(GStreamer10Video):
    """Fluendo base class for fluhwva{backend}h265dec elements"""

    provider = "Fluendo"
    api = "INVALID"
    codec = Codec.H265
    decoder_bin_tmpl = " fluhwva{backend}h265dec "

    def __init__(self) -> None:
        self.decoder_bin = self.decoder_bin_tmpl.format(backend=self.api.lower())
        super().__init__()


# fluhwva{backend}h264dec


@register_decoder
class FluendoFluHWVAVAAPIH264dec(FluendoFluHWVAH264DecBase):
    """fluhwvavaapih264dec"""

    api = "VAAPI"


@register_decoder
class FluendoFluHWVAVDPAUH264dec(FluendoFluHWVAH264DecBase):
    """fluhwvavdpauh264dec"""

    api = "VDPAU"


@register_decoder
class FluendoFluHWVADXVA2H264dec(FluendoFluHWVAH264DecBase):
    """fluhwvadxva2h264dec"""

    api = "DXVA2"


@register_decoder
class FluendoFluHWVAVDAH264dec(FluendoFluHWVAH264DecBase):
    """fluhwvavdah264dec"""

    api = "VDA"


@register_decoder
class FluendoFluHWVAVTH264dec(FluendoFluHWVAH264DecBase):
    """fluhwvavth264dec"""

    api = "VT"


# fluhwva{backend}h265dec


@register_decoder
class FluendoFluHWVAVAAPIH265dec(FluendoFluHWVAH265DecBase):
    """fluhwvavaapih265dec"""

    api = "VAAPI"


@register_decoder
class FluendoFluHWVAVDPAUH265dec(FluendoFluHWVAH265DecBase):
    """fluhwvavdpauh265dec"""

    api = "VDPAU"


@register_decoder
class FluendoFluHWVADXVA2H265dec(FluendoFluHWVAH265DecBase):
    """fluhwvadxva2h265dec"""

    api = "DXVA2"


@register_decoder
class FluendoFluHWVAVDAH265dec(FluendoFluHWVAH265DecBase):
    """fluhwvavdah265dec"""

    api = "VDA"


@register_decoder
class FluendoFluHWVAVTH265dec(FluendoFluHWVAH265DecBase):
    """fluhwvavth265dec"""

    api = "VT"
