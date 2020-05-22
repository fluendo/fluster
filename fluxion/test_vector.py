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


class TestVector:
    NAME = 'name'
    SOURCE = 'source'
    INPUT = 'input'
    RESULT = 'result'
    RESULT_FRAMES = 'result_frames'

    def __init__(self, name, source, input, result, result_frames=None):
        self.name = name
        self.source = source
        self.input = input
        self.result = result
        self.result_frames = result_frames

    def __str__(self):
        ret = f'        {self.name}\n' \
            f'            Source: {self.source}\n' \
            f'            Input: {self.input}\n' \
            f'            Result: {self.result}'
        if self.result_frames:
            ret += f'\n            Result frames: {", ".join(self.result_frames)}'
        return ret
