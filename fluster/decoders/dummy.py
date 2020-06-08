# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
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

import hashlib

from fluster.codec import Codec
from fluster.decoder import Decoder, register_decoder


@register_decoder
class Dummy(Decoder):
    '''Dummy decoder implementation'''
    name = "Dummy"
    codec = Codec.Dummy
    description = "This is a dummy implementation for the dummy codec"

    def decode(self, input_filepath: str, output_filepath: str, timeout: int, verbose: int):
        return hashlib.md5(input_filepath.encode('utf-8')).hexdigest()
