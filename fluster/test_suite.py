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

import os.path
import json
import unittest
import copy
from multiprocessing import Pool
from unittest.result import TestResult
from time import perf_counter
from shutil import rmtree

from fluster.test_vector import TestVector
from fluster.codec import Codec
from fluster.decoder import Decoder
from fluster.test import Test
from fluster import utils


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


class Context:
    '''Context for TestSuite'''
    # pylint: disable=too-few-public-methods, too-many-instance-attributes

    def __init__(self, jobs: int, decoder: Decoder, timeout: int, failfast: bool, quiet: bool, results_dir: str,
                 reference: bool = False, test_vectors: list = None, keep_files: bool = False):
        self.jobs = jobs
        self.decoder = decoder
        self.timeout = timeout
        self.failfast = failfast
        self.quiet = quiet
        self.results_dir = results_dir
        self.reference = reference
        self.test_vectors = test_vectors
        self.keep_files = keep_files


class TestSuite:
    '''Test suite class'''

    def __init__(self, filename: str, resources_dir: str, name: str, codec: Codec, description: str,
                 test_vectors: dict):
        # Not included in JSON
        self.filename = filename
        self.resources_dir = resources_dir
        self.test_vectors_success = 0

        # JSON members
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = test_vectors

    def clone(self):
        '''Create a deep copy of the object'''
        return copy.deepcopy(self)

    @classmethod
    def from_json_file(cls, filename: str, resources_dir: str):
        '''Create a TestSuite instance from a file'''
        with open(filename) as json_file:
            data = json.load(json_file)
            data['test_vectors'] = dict(
                map(TestVector.from_json, data["test_vectors"]))
            data['codec'] = Codec(data['codec'])
            return cls(filename, resources_dir, **data)

    def to_json_file(self, filename: str):
        '''Serialize the test suite to a file'''
        with open(filename, 'w') as json_file:
            data = self.__dict__.copy()
            data.pop('resources_dir')
            data.pop('filename')
            data.pop('test_vectors_success')
            data['codec'] = str(self.codec.value)
            data['test_vectors'] = [tv.data_to_serialize()
                                    for tv in self.test_vectors.values()]
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
        for test_vector in self.test_vectors.values():
            download_tasks.append(
                DownloadWork(out_dir, verify, extract_all, keep_file, self.name, test_vector))

        with Pool(jobs) as pool:
            pool.map(self._download_worker, download_tasks, chunksize=1)

        print('All downloads finished')

    def _run_worker(self, test: Test):
        '''Run one unit test returning the TestVector'''
        test_result = TestResult()
        test(test_result)
        line = '.'
        if test_result.failures:
            line = 'F'
        elif test_result.errors:
            line = 'E'
        print(line, end='', flush=True)
        if test_result.failures:
            test.test_vector.errors += test_result.failures
        if test_result.errors:
            test.test_vector.errors += test_result.errors
        return test.test_vector

    def run_test_suite_sequentially(self, tests: list, failfast: bool, quiet: bool):
        '''Run the test suite sequentially'''

        # Set the names of the tests to a more human-friendly name: Decoder.TestSuite
        for test in tests:
            test_cls = type(test)
            test_cls.__module__ = test.decoder.name
            test_cls.__qualname__ = test.test_suite.name

        suite = unittest.TestSuite()
        suite.addTests(tests)
        runner = unittest.TextTestRunner(
            failfast=failfast, verbosity=1 if quiet else 2)
        res = runner.run(suite)

        # Collect all TestResults with error to add them into the test vectors
        for test_result in res.failures:
            test_vector = test_result[0].test_vector
            test_vector.errors.append(test_result[1])
        for test_result in res.errors:
            test_vector = test_result[0].test_vector
            test_vector.errors.append(test_result[1])

        self.test_vectors_success = 0
        for test_vector in self.test_vectors.values():
            if not test_vector.errors:
                self.test_vectors_success += 1

    def run_test_suite_in_parallel(self, jobs: int, tests: list):
        '''Run the test suite in parallel'''
        with Pool(jobs) as pool:
            start = perf_counter()
            test_results = pool.map(self._run_worker, tests)
            print('\n')
            end = perf_counter()
            self.test_vectors_success = 0
            for test_vector_res in test_results:
                if test_vector_res.errors:
                    for error in test_vector_res.errors:
                        for line in error:
                            print(line)
                else:
                    self.test_vectors_success += 1

                # Collect the test vector results and failures since they come
                # from a different process
                self.test_vectors[test_vector_res.name] = test_vector_res
            print(
                f'Ran {self.test_vectors_success}/{len(test_results)} tests successfully in {end-start:.3f} secs')

    def run(self, ctx: Context):
        '''
        Run the test suite.
        Returns a new copy of the test suite with the result of the test
        '''
        # pylint: disable=too-many-locals

        if not ctx.decoder.check():
            print(
                f'Skipping decoder {ctx.decoder.name} because it cannot be run')
            return None

        ctx.results_dir = os.path.join(
            ctx.results_dir, self.name, 'test_results')
        if os.path.exists(ctx.results_dir):
            rmtree(ctx.results_dir)
        os.makedirs(ctx.results_dir)

        test_suite = self.clone()
        tests = test_suite.generate_tests(ctx)
        if not tests:
            return None

        # decoders using hardware acceleration cannot be easily parallelized
        # reliably and may case issues. Thus, we execute them sequentially
        if ctx.decoder.hw_acceleration and ctx.jobs > 1:
            ctx.jobs = 1
            print(
                f'Decoder {ctx.decoder.name} uses hardware acceleration, using 1 job automatically')

        print('*' * 100)
        string = f'Running test suite {self.name} with decoder {ctx.decoder.name}\n'
        if ctx.test_vectors:
            string += f'Test vectors {" ".join(ctx.test_vectors)}\n'
        string += f'Using {ctx.jobs} parallel job(s)'
        print(string)
        print('*' * 100 + '\n')

        if ctx.jobs == 1:
            test_suite.run_test_suite_sequentially(
                tests, ctx.failfast, ctx.quiet)
        else:
            test_suite.run_test_suite_in_parallel(ctx.jobs, tests)

        if ctx.reference:
            test_suite.to_json_file(test_suite.filename)

        if not ctx.keep_files and os.path.isdir(ctx.results_dir):
            rmtree(ctx.results_dir)

        return test_suite

    def generate_tests(self, ctx: Context):
        '''Generate the tests for a decoder'''
        tests = []
        test_vectors_run = dict()
        for name, test_vector in self.test_vectors.items():
            if ctx.test_vectors:
                if test_vector.name.lower() not in ctx.test_vectors:
                    continue
            tests.append(
                Test(ctx.decoder, self, test_vector, ctx.results_dir, ctx.reference, ctx.timeout, ctx.keep_files))
            test_vectors_run[name] = test_vector
        self.test_vectors = test_vectors_run
        return tests

    def __str__(self):
        return f'\n{self.name}\n' \
            f'    Codec: {self.codec.value}\n' \
            f'    Description: {self.description}\n' \
            f'    Test vectors: {len(self.test_vectors)}'
