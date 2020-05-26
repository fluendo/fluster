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
import unittest


from fluxion.test_vector import TestVector
from fluxion.codec import Codec
from fluxion.decoder import Decoder
from fluxion.test import Test
from fluxion import utils


class TestSuite:
    '''Test suite class'''

    def __init__(self, filename: str, resources_dir: str, name: str, codec: Codec, description: str,
                 test_vectors: list):
        # Not included in JSON
        self.filename = filename
        self.resources_dir = resources_dir

        # JSON members
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = test_vectors

    @classmethod
    def from_json_file(cls, filename: str, resources_dir: str):
        '''Creates a TestSuite instance from a file'''
        with open(filename) as json_file:
            data = json.load(json_file)
            data['test_vectors'] = list(
                map(TestVector.from_json, data["test_vectors"]))
            data['codec'] = Codec(data['codec'])
            return cls(filename, resources_dir, **data)

    def to_json_file(self, filename: str):
        '''Serialize the test suite to a file'''
        with open(filename, 'w') as json_file:
            data = self.__dict__.copy()
            data.pop('resources_dir')
            data.pop('filename')
            data['codec'] = str(self.codec.value)
            data['test_vectors'] = [tv.__dict__ for tv in self.test_vectors]
            json.dump(data, json_file, indent=4)

    def download(self, out_dir: str, verify: bool, extract_all: bool = False, keep_file: bool = False):
        '''Download the test suite'''
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        print("Downloading test suite {}".format(self.name))
        for test_vector in self.test_vectors:
            dest_dir = os.path.join(out_dir, self.name, test_vector.name)
            dest_path = os.path.join(
                dest_dir, os.path.basename(test_vector.source))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            file_downloaded = os.path.exists(dest_path)
            if file_downloaded and verify:
                if test_vector.source_checksum != utils.file_checksum(dest_path):
                    file_downloaded = False
            if not file_downloaded:
                print(
                    "\tDownloading test vector {} from {}".format(test_vector.name, test_vector.source))
                utils.download(test_vector.source, dest_dir)
            if utils.is_extractable(dest_path):
                print(
                    "\tExtracting test vector {} to {}".format(test_vector.name, dest_dir))
                utils.extract(
                    dest_path, dest_dir, file=test_vector.input if not extract_all else None)
                if not keep_file:
                    os.remove(dest_path)

    def run(self, decoder: Decoder, failfast: bool, quiet: bool, results_dir: str, reference: bool = False,
            test_vectors: list = None):
        '''Run the test suite'''
        print('*' * 100 + '\n')
        string = f'Running test suite {self.name} with decoder {decoder.name}'
        string += f' and test vectors {", ".join(test_vectors)}\n' if test_vectors else '\n'
        print(string)
        print('*' * 100 + '\n')
        suite = self._gen_testing_suite(
            decoder, results_dir, reference, test_vectors=test_vectors)
        runner = unittest.TextTestRunner(
            failfast=failfast, verbosity=1 if quiet else 2)
        runner.run(suite)
        if reference:
            self.to_json_file(self.filename)

    def _gen_testing_suite(self, decoder: Decoder, results_dir: str, reference: bool, test_vectors: list = None):
        suite = unittest.TestSuite()
        for test_vector in self.test_vectors:
            if test_vectors:
                if test_vector.name.lower() not in test_vectors:
                    continue
            suite.addTest(
                Test(decoder, self, test_vector, results_dir, reference))

        return suite

    def __str__(self):
        return f'\n{self.name}\n' \
            f'    Codec: {self.codec}\n' \
            f'    Description: {self.description}\n' \
            f'    Test vectors: {len(self.test_vectors)}'
