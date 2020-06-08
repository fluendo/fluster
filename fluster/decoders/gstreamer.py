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
from functools import lru_cache

from fluster.codec import Codec
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command

PIPELINE_TPL = '{} filesrc location={} ! {} ! {} ! filesink location={}'


class GStreamer(Decoder):
    '''Base class for GStreamer decoders'''
    decoder_bin = None
    cmd = None
    caps = None
    gst_api = None
    api = None
    provider = None

    def __init__(self):
        super().__init__()
        self.name = f'{self.provider}-{self.codec.value}-{self.api}-Gst{self.gst_api}'
        self.description = f'{self.provider} {self.codec.value} {self.api} decoder for GStreamer {self.gst_api}'

    def decode(self, input_filepath: str, output_filepath: str, timeout: int, verbose: bool):
        pipeline = PIPELINE_TPL.format(self.cmd, input_filepath,
                                       self.decoder_bin, self.caps, output_filepath)
        run_command(shlex.split(pipeline), timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=None)
    def check(self):
        # pylint: disable=broad-except
        try:
            pipeline = f'gst-launch-{self.gst_api} appsrc num-buffers=0 ! {self.decoder_bin} ! fakesink'
            run_command(shlex.split(pipeline))
        except Exception:
            return False
        return True


class GStreamer10(GStreamer):
    '''Base class for GStreamer 1.x decoders'''
    cmd = 'gst-launch-1.0'
    caps = 'video/x-raw'
    gst_api = '1.0'
    provider = 'GStreamer'


class GStreamer010(GStreamer):
    '''Base class for GStreamer 0.10 decoders'''
    cmd = 'gst-launch-0.10'
    caps = 'video/x-raw-yuv'
    gst_api = '0.10'
    provider = 'GStreamer'


@register_decoder
class GStreamerVaapiH265Gst10Decoder(GStreamer10):
    '''GStreamer H.265 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! vaapih265dec '
    caps = 'video/x-raw,format=I420'
    api = 'VA-API'
    hw_acceleration = True


@register_decoder
class GStreamerVaapiH264Gst10Decoder(GStreamer10):
    '''GStreamer H.264 VAAPI decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! vaapih264dec '
    caps = 'video/x-raw,format=I420'
    api = 'VA-API'
    hw_acceleration = True


@register_decoder
class FluendoH265Gst10Decoder(GStreamer10):
    '''Fluendo H.265 software decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluh265dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH265Gst010Decoder(GStreamer010):
    '''Fluendo H.265 software decoder implementation for GStreamer 0.10'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluh265dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH264Gst10Decoder(GStreamer10):
    '''Fluendo H.264 software decoder implementation for GStreamer 1.0'''
    codec = Codec.H264
    decoder_bin = ' h264parse ! fluh264dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH264Gst010Decoder(GStreamer010):
    '''Fluendo H.264 software decoder implementation for GStreamer 0.10'''
    codec = Codec.H264
    decoder_bin = ' fluh264dec '
    provider = 'Fluendo'
    api = 'SW'


@register_decoder
class FluendoH265VAGst10Decoder(GStreamer10):
    '''Fluendo H.265 hardware decoder implementation for GStreamer 1.0'''
    codec = Codec.H265
    decoder_bin = ' h265parse ! fluvadec '
    provider = 'Fluendo'
    api = 'HW'
    hw_acceleration = True
