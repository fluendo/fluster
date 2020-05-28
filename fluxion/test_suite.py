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
from multiprocessing import Pool
from unittest.result import TestResult
from time import perf_counter

from fluxion.test_vector import TestVector
from fluxion.codec import Codec
from fluxion.decoder import Decoder
from fluxion.test import Test
from fluxion import utils


class DownloadWork:
    '''Context to pass to each download worker'''
    # pylint: disable=too-few-public-methods

    def __init__(self, out_dir: str, verify: bool, extract_all: bool, keep_file: bool,
                 test_suite_name: str, test_vector: TestVector):
        self.out_dir = out_dir
        self.verify = verify
        self.extract_all = extract_all
        self.keep_file = keep_file
        self.test_suite_name = test_suite_name
        self.test_vector = test_vector


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

    def _download_worker(self, context: DownloadWork):
        '''Download and extract a test vector'''
        test_vector = context.test_vector
        dest_dir = os.path.join(
            context.out_dir, context.test_suite_name, test_vector.name)
        dest_path = os.path.join(
            dest_dir, os.path.basename(test_vector.source))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        file_downloaded = os.path.exists(dest_path)
        if file_downloaded and context.verify:
            if test_vector.source_checksum != utils.file_checksum(dest_path):
                file_downloaded = False
        print(f'\tDownloading test vector {test_vector.name} from {dest_dir}')
        utils.download(test_vector.source, dest_dir)
        if utils.is_extractable(dest_path):
            print(
                f'\tExtracting test vector {test_vector.name} to {dest_dir}')
            utils.extract(
                dest_path, dest_dir, file=test_vector.input_file if not context.extract_all else None)
            if not context.keep_file:
                os.remove(dest_path)

    def download(self, jobs: int, out_dir: str, verify: bool, extract_all: bool = False, keep_file: bool = False):
        '''Download the test suite'''
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        print(f'Downloading test suite {self.name} using {jobs} parallel jobs')
        download_tasks = []
        for test_vector in self.test_vectors:
            download_tasks.append(
                DownloadWork(out_dir, verify, extract_all, keep_file, self.name, test_vector))

        with Pool(jobs) as pool:
            pool.map(self._download_worker, download_tasks, chunksize=1)

        print('All downloads finished')

    def _run_worker(self, test: Test):
        '''Run one unit test returning the test_vector and the result'''
        test_result = TestResult()
        test(test_result)
        line = '.'
        if not test_result.wasSuccessful():
            line = 'x'
        print(line, end='', flush=True)
        return (test.test_vector, test_result.failures)

    def _run_test_suite_sequentially(self, tests: list, failfast: bool, quiet: bool):
        suite = unittest.TestSuite()
        suite.addTests(tests)
        runner = unittest.TextTestRunner(
            failfast=failfast, verbosity=1 if quiet else 2)
        res = runner.run(suite)
        return res.wasSuccessful()

    def _run_test_suite_in_parallel(self, jobs: int, tests: list):
        with Pool(jobs) as pool:
            start = perf_counter()
            test_results = pool.map(self._run_worker, tests)
            print('\n')
            end = perf_counter()
            success = 0
            for test_vector, result in test_results:
                if result:
                    for failure in result:
                        for line in failure:
                            print(line)
                else:
                    success += 1
                for tvector in self.test_vectors:
                    if tvector.name == test_vector.name:
                        tvector.result = test_vector.result
                        break
            print(
                f'Ran {success}/{len(test_results)} tests successfully in {end-start:.3f} secs')
            return success == len(test_results)

    def run(self, jobs: int, decoder: Decoder, failfast: bool, quiet: bool, results_dir: str, reference: bool = False,
            test_vectors: list = None):
        '''Run the test suite'''
        # pylint: disable=too-many-locals

        # decoders using hardware acceleration cannot be easily parallelized
        # reliably and may case issues. Thus, we execute them sequentially
        if decoder.hw_acceleration and jobs > 1:
            jobs = 1
            print(
                f'Decoder {decoder.name} uses hardware acceleration, using 1 job automatically')

        print('*' * 100 + '\n')
        string = f'Running test suite {self.name} with decoder {decoder.name}'
        if test_vectors:
            string += f' and test vectors {", ".join(test_vectors)}'
        string += f' using {jobs} parallel jobs'
        print(string)
        print('*' * 100 + '\n')
        if not decoder.check_run():
            print(f'Skipping decoder {decoder.name} because it cannot be run')
            return True
        tests = self._gen_tests(
            decoder, results_dir, reference, test_vectors=test_vectors)

        test_success = False
        if jobs == 1:
            test_success = self._run_test_suite_sequentially(
                tests, failfast, quiet)
        else:
            test_success = self._run_test_suite_in_parallel(jobs, tests)
        if reference:
            self.to_json_file(self.filename)

        return test_success

    def _gen_tests(self, decoder: Decoder, results_dir: str, reference: bool, test_vectors: list = None):
        tests = []
        for test_vector in self.test_vectors:
            if test_vectors:
                if test_vector.name.lower() not in test_vectors:
                    continue
            tests.append(
                Test(decoder, self, test_vector, results_dir, reference))
        return tests

    def __str__(self):
        return f'\n{self.name}\n' \
            f'    Codec: {self.codec}\n' \
            f'    Description: {self.description}\n' \
            f'    Test vectors: {len(self.test_vectors)}'
