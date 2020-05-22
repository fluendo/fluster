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

import unittest

from fluxion.decoder import Decoder
from fluxion.test_vector import TestVector


class Test(unittest.TestCase):

    def __init__(self, decoder, test_suite, test_vector):
        test_name = ''
        for c in f'{decoder.name}_{test_suite.name}_{test_vector.name}':
            if c.isalnum():
                test_name += c
            else:
                test_name += '_'
        setattr(self, test_name, self._gen_test_func(decoder, test_vector))
        super().__init__(test_name)

    def _gen_test_func(self, decoder, test_vector):
        def test():
            result = decoder.decode(test_vector.input)
            self.assertEqual(test_vector.result, result)
        return test