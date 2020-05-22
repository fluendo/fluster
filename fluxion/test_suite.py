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

import os.path
import json

from fluxion.test_vector import TestVector


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

    @staticmethod
    def from_json_file(filename):
        with open(filename) as f:
            content = json.load(f)
            test_suite = TestSuite(
                content[TestSuite.NAME], content[TestSuite.CODEC], content[TestSuite.DESCRIPTION])
            for tv in content[TestSuite.TEST_VECTORS]:
                result_frames = None if not TestVector.RESULT_FRAMES in tv else tv[
                    TestVector.RESULT_FRAMES]
                test_suite.add_test_vector(TestVector(
                    tv[TestVector.NAME], tv[TestVector.SOURCE], tv[TestVector.INPUT], tv[TestVector.RESULT], result_frames))
            return test_suite

    def __str__(self):
        return f'\n{self.name}\n' \
            f'    Codec: {self.codec}\n' \
            f'    Description: {self.description}\n' \
            f'    Test vectors: {len(self.test_vectors)}'
