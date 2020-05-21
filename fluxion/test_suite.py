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

class TestSuite:
    NAME = 'name'
    CODEC = 'codec'
    DESCRIPTION = 'description'
    TEST_VECTORS = 'test_vectors'

    def __init__(self, name, codec, description):
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = []

    def add_test_vector(self, test_vector):
        self.test_vectors.append(test_vector)

    def __str__(self):
        return f'\n{self.name}\n' \
            f'  Codec: {self.codec}\n' \
            f'  Description: {self.description}\n' \
            f'  Test vectors: {len(self.test_vectors)}'
