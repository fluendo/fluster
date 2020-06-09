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

from functools import lru_cache
import shlex
import subprocess

from fluster.codec import Codec, PixelFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command

FFMPEG_TPL = '{} -i {} -vf format=pix_fmts={} {}'


class FFmpegDecoder(Decoder):
    '''Generic class for FFmpeg decoder'''
    binary = 'ffmpeg'
    description = None
    cmd = None
    api = None

    def __init__(self):
        self.cmd = self.binary
        if self.hw_acceleration:
            self.cmd += f' -hwaccel {self.api.lower()}'
        self.name = f'FFmpeg-{self.codec.value}{"-" + self.api if self.api else ""}'
        self.description = f'FFmpeg {self.codec.value} {self.api if self.hw_acceleration else "SW"} decoder'

    def decode(self, input_filepath: str, output_filepath: str, output_format: PixelFormat, timeout: int,
               verbose: bool):
        '''Decodes input_filepath in output_filepath'''
        cmd = shlex.split(FFMPEG_TPL.format(
            self.cmd, input_filepath, str(output_format.value), output_filepath))
        run_command(cmd, timeout=timeout, verbose=verbose)
        return file_checksum(output_filepath)

    @lru_cache(maxsize=None)
    def check(self):
        '''Checks whether the decoder can be run'''
        # pylint: disable=broad-except
        if self.hw_acceleration:
            try:
                output = subprocess.check_output(
                    [self.binary, '-hwaccels'], stderr=subprocess.DEVNULL).decode('utf-8')
                return f'\n{self.api.lower()}\n' in output
            except Exception:
                return False
        else:
            return super().check()


@register_decoder
class FFmpegH264Decoder(FFmpegDecoder):
    '''FFmpeg SW decoder for H.264'''
    codec = Codec.H264


@register_decoder
class FFmpegH265Decoder(FFmpegDecoder):
    '''FFmpeg SW decoder for H.265'''
    codec = Codec.H265


class FFmpegVaapiDecoder(FFmpegDecoder):
    '''Generic class for FFmpeg VAAPI decoder'''
    hw_acceleration = True
    api = 'VAAPI'


@register_decoder
class FFmpegH264VaapiDecoder(FFmpegVaapiDecoder):
    '''FFmpeg VAAPI decoder for H.264'''
    codec = Codec.H264


@register_decoder
class FFmpegH265VaapiDecoder(FFmpegVaapiDecoder):
    '''FFmpeg VAAPI decoder for H.265'''
    codec = Codec.H265
