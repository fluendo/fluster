# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import shlex
import subprocess
from functools import lru_cache

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command, normalize_binary_cmd

PIPELINE_TPL = '{} filesrc location={} ! {} ! {} ! {} location={}'


@lru_cache(maxsize=None)
def gst_element_exists(element: str) -> bool:
    '''Check if an element exists in current GStreamer installation'''
    inspect_exe = normalize_binary_cmd('gst-inspect-1.0')

    try:
        subprocess.run(
            [inspect_exe, '--exists', element], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return False


def output_format_to_gst(output_format: OutputFormat) -> str:
    """Return GStreamer pixel format"""
    mapping = {OutputFormat.YUV420P: "I420", OutputFormat.YUV420P10LE: "I420_10LE"}
    if output_format not in mapping:
        raise Exception(f"No matching output format found in GStreamer for {output_format}")
    return mapping[output_format]


class GStreamer(Decoder):
    '''Base class for GStreamer decoders'''
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
            self.name = f'{self.provider}-{self.codec.value}-{self.api}-Gst{self.gst_api}'
        self.description = f'{self.provider} {self.codec.value} {self.api} decoder for GStreamer {self.gst_api}'
        self.cmd = normalize_binary_cmd(self.cmd)

        if not gst_element_exists(self.sink):
            self.sink = 'filesink'

    def gen_pipeline(self, input_filepath: str, output_filepath: str, output_format: OutputFormat) -> str:
        '''Generate the GStreamer pipeline used to decode the test vector'''
        # pylint: disable=unused-argument
        return PIPELINE_TPL.format(self.cmd, input_filepath, self.decoder_bin, self.caps, self.sink, output_filepath)

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
    ) -> str:
        '''Decode the test vector and do the checksum'''
        pipeline = self.gen_pipeline(
            input_filepath, output_filepath, output_format)
        run_command(shlex.split(pipeline), timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=None)
    def check(self, verbose: bool) -> bool:
        '''Check if GStreamer decoder is valid (better than gst-inspect)'''
        # pylint: disable=broad-except
        try:
            if hasattr(self, 'check_decoder_bin'):
                decoder_bin = getattr(self, 'check_decoder_bin')
            else:
                decoder_bin = self.decoder_bin
            binary = normalize_binary_cmd(f'gst-launch-{self.gst_api}')
            pipeline = f'{binary} appsrc num-buffers=0 ! {decoder_bin} ! fakesink'
            run_command(shlex.split(pipeline), verbose=verbose)
        except Exception:
            return False
        return True


class GStreamer10Video(GStreamer):
    '''Base class for GStreamer 1.x video decoders'''
    cmd = 'gst-launch-1.0'
    caps = 'video/x-raw'
    gst_api = '1.0'
    sink = 'videocodectestsink'
    provider = 'GStreamer'

    def gen_pipeline(self, input_filepath: str, output_filepath: str, output_format: OutputFormat) -> str:
        caps = f'{self.caps} ! videoconvert dither=none ! video/x-raw,format={output_format_to_gst(output_format)}'
        return PIPELINE_TPL.format(self.cmd, input_filepath, self.decoder_bin, caps, self.sink, output_filepath)


class GStreamer10Audio(GStreamer):
    '''Base class for GStreamer 1.x audio decoders'''
    cmd = 'gst-launch-1.0'
    caps = 'audio/x-raw'
    gst_api = '1.0'
    sink = 'filesink'
    provider = 'GStreamer'


class GStreamer010Video(GStreamer):
    '''Base class for GStreamer 0.10 video decoders'''
    cmd = 'gst-launch-0.10'
    caps = 'video/x-raw-yuv'
    gst_api = '0.10'
    sink = 'videocodectestsink'
    provider = 'GStreamer'


@register_decoder
class GStreamerLibavH264(GStreamer10Video):
    '''GStreamer H.264 Libav decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! avdec_h264 '
    api = 'Libav'
    hw_acceleration = False


@register_decoder
class GStreamerLibavH265(GStreamer10Video):
    '''GStreamer H.265 Libav decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! avdec_h265 '
    api = 'Libav'
    hw_acceleration = False


@register_decoder
class GStreamerLibavVP8(GStreamer10Video):
    '''GStreamer VP8 Libav decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! avdec_vp8 '
    api = 'Libav'
    sink = 'filesink'
    hw_acceleration = False


@register_decoder
class GStreamerLibavVP9(GStreamer10Video):
    '''GStreamer VP9 Libav decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' avdec_vp9'
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'Libav'
    hw_acceleration = False


@register_decoder
class GStreamerVaapiH265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! vaapih265dec '
    api = 'VAAPI'
    hw_acceleration = True


@register_decoder
class GStreamerVaH265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 VA decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! vah265dec '
    api = 'VA'
    hw_acceleration = True


@register_decoder
class GStreamerMsdkH265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 Intel MSDK decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! msdkh265dec '
    api = 'MSDK'
    hw_acceleration = True


@register_decoder
class GStreamerNvdecH265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 NVDEC decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! nvh265dec '
    api = 'NVDEC'
    hw_acceleration = True


@register_decoder
class GStreamerD3d11H265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 D3D11 decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! d3d11h265dec '
    api = 'D3D11'
    hw_acceleration = True


@register_decoder
class GStreamerV4l2CodecsH265Gst10Decoder(GStreamer10Video):
    '''GStreamer H.265 V4L2 stateless decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! v4l2slh265dec '
    api = 'V4L2SL'
    hw_acceleration = True


@register_decoder
class GStreamerVaapiH264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! vaapih264dec '
    api = 'VAAPI'
    hw_acceleration = True


@register_decoder
class GStreamerVaH264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 VA decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! vah264dec '
    api = 'VA'
    hw_acceleration = True


@register_decoder
class GStreamerMsdkH264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 Intel MSDK decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! msdkh264dec '
    api = 'MSDK'
    hw_acceleration = True


@register_decoder
class GStreamerNvdecH264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 NVDEC decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! nvh264dec '
    api = 'NVDEC'
    hw_acceleration = True


@register_decoder
class GStreamerD3d11H264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 D3D11 decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! d3d11h264dec '
    api = 'D3D11'
    hw_acceleration = True


@register_decoder
class GStreamerV4l2CodecsH264Gst10Decoder(GStreamer10Video):
    '''GStreamer H.264 V4L2 stateless decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! v4l2slh264dec '
    api = 'V4L2SL'
    hw_acceleration = True


@register_decoder
class GStreamerV4l2CodecsVP8Gst10Decoder(GStreamer10Video):
    '''GStreamer VP8 V4L2 stateless decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! v4l2slvp8dec '
    api = 'V4L2SL'
    hw_acceleration = True


@register_decoder
class GStreamerLibvpxVP8(GStreamer10Video):
    '''GStreamer VP8 Libvpx decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! vp8dec '
    api = 'libvpx'
    sink = 'filesink'
    hw_acceleration = False


@register_decoder
class GStreamerVaapiVP8Gst10Decoder(GStreamer10Video):
    '''GStreamer VP8 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! vaapivp8dec '
    api = 'VAAPI'
    hw_acceleration = True


@register_decoder
class GStreamerVaVP8Gst10Decoder(GStreamer10Video):
    '''GStreamer VP8 VA decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! vavp8dec '
    api = 'VA'
    hw_acceleration = True


@register_decoder
class GStreamerD3d11VP8Gst10Decoder(GStreamer10Video):
    '''GStreamer VP8 D3D11 decoder implementation for GStreamer 1.0'''
    codec = Codec.VP8
    decoder_bin = ' ivfparse ! d3d11vp8dec '
    api = 'D3D11'
    hw_acceleration = True


@register_decoder
class GStreamerV4l2CodecsVP9Gst10Decoder(GStreamer10Video):
    '''GStreamer VP9 V4L2 stateless decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' v4l2slvp9dec '
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'V4L2SL'
    hw_acceleration = True


@register_decoder
class GStreamerLibvpxVP9(GStreamer10Video):
    '''GStreamer VP9 Libvpx decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' vp9dec  '
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'libvpx'
    hw_acceleration = False


@register_decoder
class GStreamerVaapiVP9Gst10Decoder(GStreamer10Video):
    '''GStreamer VP9 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' vaapivp9dec '
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'VAAPI'
    hw_acceleration = True


@register_decoder
class GStreamerVaVP9Gst10Decoder(GStreamer10Video):
    '''GStreamer VP9 VA decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' vavp9dec '
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'VA'
    hw_acceleration = True


@register_decoder
class GStreamerD3d11VP9Gst10Decoder(GStreamer10Video):
    '''GStreamer VP9 D3D11 decoder implementation for GStreamer 1.0'''
    codec = Codec.VP9
    check_decoder_bin = ' d3d11vp9dec '
    decoder_bin = f' parsebin ! {check_decoder_bin}'
    api = 'D3D11'
    hw_acceleration = True


@register_decoder
class FluendoH265Gst10Decoder(GStreamer10Video):
    '''Fluendo H.265 software decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluh265dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH265Gst010Decoder(GStreamer010Video):
    '''Fluendo H.265 software decoder implementation for GStreamer 0.10'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluh265dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH264Gst10Decoder(GStreamer10Video):
    '''Fluendo H.264 software decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! fluh264dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH264Gst010Decoder(GStreamer010Video):
    '''Fluendo H.264 software decoder implementation for GStreamer 0.10'''
    codec = Codec.H264
    decoder_bin = ' fluh264dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH264VAGst10Decoder(GStreamer10Video):
    '''Fluendo H.264 hardware decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! fluvadec '
    provider = 'Fluendo'
    api = 'HW'
    hw_acceleration = True


class FluendoH265VAGst10DecoderBase(GStreamer10Video):
    '''Fluendo H.265 hardware decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin_tmpl =\
        ' h265parse !'\
        ' video/x-h265,stream-format={stream_format},alignment={alignment} !'\
        ' fluvadec '
    provider = 'Fluendo'
    api = 'HW'
    hw_acceleration = True
    stream_format: str = ""
    alignment: str = ""

    def __init__(self) -> None:
        super().__init__()
        self.name = self._translator(self.name)
        self.description = self._translator(self.description)
        self.decoder_bin = self.decoder_bin_tmpl.format(
            stream_format=self.stream_format, alignment=self.alignment)

    def _translator(self, target_val: str) -> str:
        new_val = f'{self.codec.value}-{self.stream_format}-{self.alignment}'
        return target_val.replace(self.codec.value, new_val)


@register_decoder
class FluendoH265ByteStreamAuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (byte-stream/au) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'byte-stream'
    alignment = 'au'


@register_decoder
class FluendoH265ByteStreamNalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (byte-stream/nal) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'byte-stream'
    alignment = 'nal'


@register_decoder
class FluendoH265Hev1AuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (hev1/au) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'hev1'
    alignment = 'au'


@register_decoder
class FluendoH265Hvc1AuVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (hvc1/au) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'hvc1'
    alignment = 'au'


@register_decoder
class FluendoH265Hev1NalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (hev1/nal) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'hev1'
    alignment = 'nal'


@register_decoder
class FluendoH265Hvc1NalVAGst10Decoder(FluendoH265VAGst10DecoderBase):
    '''
    Fluendo H.265 (hvc1/nal) hardware decoder implementation for GStreamer 1.0
    '''
    stream_format = 'hvc1'
    alignment = 'nal'


@register_decoder
class FluendoFluVAH265DecGst10Decoder(GStreamer10Video):
    '''Fluendo H.265 separated plugin hardware decoder for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluvah265dec '
    provider = 'Fluendo'
    api = 'HW'
    hw_acceleration = True
    name = f'{provider}-{codec.value}-{api}-vah265dec-Gst1.0'


@register_decoder
class FluendoFluVAH264DecGst10Decoder(GStreamer10Video):
    '''Fluendo H.264 separated plugin hardware decoder for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! fluvah264dec '
    provider = 'Fluendo'
    api = 'HW'
    hw_acceleration = True
    name = f'{provider}-{codec.value}-{api}-vah264dec-Gst1.0'


@register_decoder
class FluendoFluAACDecGst10Decoder(GStreamer10Audio):
    '''Fluendo AAC plugin decoder for GStreamer 1.0'''
    def __init__(self) -> None:
        self.codec = Codec.AAC
        self.decoder_bin = 'fluaacdec trim=0'
        self.provider = 'Fluendo'
        self.api = 'SW'
        self.caps = self.caps + ',format=S16LE'
        super().__init__()
