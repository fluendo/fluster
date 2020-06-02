# fluster - testing framework for codecs
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
    '''Test vector'''

    def __init__(self, name: str, source: str, source_checksum: str, input_file: str,
                 result: str, result_frames=None):
        self.name = name
        self.source = source
        self.source_checksum = source_checksum
        self.input_file = input_file
        self.result = result
        self.result_frames = result_frames
        self.errors = []

    @classmethod
    def from_json(cls, data: dict):
        '''Deserialize an instance of TestVector from a json file'''
        return (data['name'], cls(**data))

    def data_to_serialize(self):
        '''Return the data to be serialized'''
        data = self.__dict__.copy()
        data.pop('errors')
        return data

    def __str__(self):
        ret = f'        {self.name}\n' \
            f'            Source: {self.source}\n' \
            f'            Input: {self.input_file}\n' \
            f'            Result: {self.result}'
        if self.result_frames:
            ret += f'\n            Result frames: {", ".join(self.result_frames)}'
        return ret
