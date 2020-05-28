# fluster - testing framework for codecs
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
from fluster.codec import Codec
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum


@register_decoder
class H265JCTVTDecoder(Decoder):
    '''JCT-VT H.265 / HEVC reference decoder implementation'''
    name = "JCT-VT-H265"
    description = "JCT-VT H.265 / HEVC reference decoder"
    codec = Codec.H265
    binary = 'TAppDecoder'

    def decode(self, input_filepath: str, output_filepath: str, timeout: int):
        '''Decodes input_filepath in output_filepath'''
        subprocess.run([self.binary, '-b', input_filepath,
                        '-o', output_filepath], stdout=subprocess.DEVNULL, check=True)
        return file_checksum(output_filepath)
