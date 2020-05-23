# fluxion - testing framework for codecs
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

from abc import ABC, abstractmethod


class Decoder(ABC):
    '''Base class for decoders'''
    name = None
    codec = None
    description = None

    @abstractmethod
    def decode(self, input_filepath: str, output_filepath: str):
        '''Decodes input_filepath in output_filepath'''
        raise Exception('Not implemented')

    def __str__(self):
        return f'    {self.name}: {self.description}'


DECODERS = []


def register_decoder(clazz):
    '''Register a new decoder implementation'''
    global DECODERS
    DECODERS.append(clazz())
