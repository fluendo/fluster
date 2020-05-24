# fluxion - testing framework for codecs
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
import subprocess
import shlex
from fluxion.codec import Codec
from fluxion.decoder import Decoder, register_decoder
from fluxion.utils import file_checksum

PIPELINE_TPL = "{} filesrc location={} ! {} ! {} ! filesink location={}"


class GStreamer(Decoder):
    '''Base class for GStreamer decoders'''
    decoder_element = None
    cmd = None
    caps = None

    def decode(self, input_filepath: str, output_filepath: str):
        pipeline = PIPELINE_TPL.format(self.cmd, input_filepath,
                                       self.decoder_element, self.caps, output_filepath)
        subprocess.run(shlex.split(pipeline),
                       stdout=subprocess.DEVNULL, check=True)
        return file_checksum(output_filepath)


class GStreamer10(GStreamer):
    '''Base class for GStreamer 1.x decoders'''
    decoder_element = None
    cmd = 'gst-launch-1.0'
    caps = 'video/x-raw'


class GStreamer010(GStreamer):
    '''Base class for GStreamer 0.10 decoders'''
    decoder_element = None
    cmd = 'gst-launch-0.10'
    caps = 'video/x-raw-yuv'


@register_decoder
class FluendoH265Gst10Decoder(GStreamer10):
    '''Fluendo H.265 software decoder implementation for GStreamer 1.0'''
    name = 'Fluendo-H265-SW-Gst10'
    description = "Fluendo H.265 software decoder for GStreamer 1.0"
    codec = Codec.H265
    decoder_element = ' h265parse ! fluh265dec '


@register_decoder
class FluendoH265Gst010Decoder(GStreamer010):
    '''Fluendo H.265 software decoder implementation for GStreamer 0.10'''
    name = 'Fluendo-H265-SW-Gst010'
    description = "Fluendo H.265 software decoder for GStreamer 0.10"
    codec = Codec.H265
    decoder_element = ' h265parse ! fluh265dec '


@register_decoder
class CommunityVaapiH265Gst10Decoder(GStreamer10):
    '''Community H.265 VAAPI decoder implementation for GStreamer 1.0'''
    name = 'GStreamer-H265-VAAPI-Gst10'
    description = "Community H.265 VAAPI decoder implementation for GStreamer 1.0"
    codec = Codec.H265
    decoder_element = ' h265parse ! vaapih265dec '
    caps = 'video/x-raw,format=I420'
