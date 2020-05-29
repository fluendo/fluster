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

import os
import os.path
from functools import lru_cache
import sys

# Import decoders that will auto-register
# pylint: disable=wildcard-import, unused-wildcard-import
from fluster.decoders import *
# pylint: enable=wildcard-import, unused-wildcard-import

from fluster.test_suite import TestSuite
from fluster.decoder import DECODERS

# pylint: disable=broad-except


class Fluster:
    '''Main class for fluster'''

    def __init__(self, test_suites_dir: str, decoders_dir: str, resources_dir: str,
                 results_dir: str, verbose: bool = False):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.resources_dir = resources_dir
        self.results_dir = results_dir
        self.verbose = verbose
        self.test_suites = []
        self.decoders = DECODERS

    @lru_cache(maxsize=None)
    def _load_test_suites(self):
        for root, _, files in os.walk(self.test_suites_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.json':
                    if self.verbose:
                        print(f'Test suite found: {file}')
                    try:
                        test_suite = TestSuite.from_json_file(
                            os.path.join(root, file), self.resources_dir)
                        self.test_suites.append(test_suite)
                    except Exception as ex:
                        print(f'Error loading test suite {file}: {ex}')

    def list_decoders(self, check_run: bool = False):
        '''List all the available decoders'''
        print('\nList of available decoders:\n')
        decoders_dict = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for codec in decoders_dict:
            print(f'{codec}'.split('.')[1])
            for decoder in decoders_dict[codec]:
                string = f'{decoder}'
                if check_run:
                    string += ' ✔️' if decoder.check_run() else ' ❌'
                print(string)

    def list_test_suites(self, show_test_vectors: bool = False, test_suites: list = None):
        '''List all test suites'''
        self._load_test_suites()
        print('\nList of available test suites:')
        if test_suites:
            test_suites = [x.lower() for x in test_suites]
        for test_suite in self.test_suites:
            if test_suites:
                if test_suite.name.lower() not in test_suites:
                    continue
            print(test_suite)
            if show_test_vectors:
                for test_vector in test_suite.test_vectors:
                    print(test_vector)

    def run_test_suites(self, jobs: int, timeout: int, test_suites: list = None, decoders: list = None,
                        test_vectors: list = None, failfast: bool = False, quiet: bool = False,
                        reference: bool = False, summary: bool = False, keep_files: bool = False):
        '''Run a group of test suites'''
        # pylint: disable=too-many-branches,too-many-locals
        self._load_test_suites()
        run_test_suites = []

        # Convert all test suites and decoders to lowercase to make the filter greedy
        if test_suites:
            test_suites = [x.lower() for x in test_suites]
        if decoders:
            decoders = [x.lower() for x in decoders]
        if test_vectors:
            test_vectors = [x.lower() for x in test_vectors]

        if test_suites:
            run_test_suites = [
                test_suite for test_suite in self.test_suites if test_suite.name.lower() in test_suites]
            if not run_test_suites:
                raise Exception(
                    "No test suite found matching {}".format(test_suites))
        else:
            run_test_suites = self.test_suites

        run_decoders = []
        if decoders:
            run_decoders = [
                dec for dec in self.decoders if dec.name.lower() in decoders]
            if not run_decoders:
                raise Exception(
                    "No decoders found matching {}".format(decoders))
        else:
            run_decoders = self.decoders

        dec_names = [dec.name for dec in run_decoders]

        if reference and (not run_decoders or len(run_decoders) > 1):
            raise Exception(
                f'Only one decoder can be the reference. Given: {", ".join(dec_names)}')

        if reference:
            print('Reference mode')

        error = False
        for test_suite in run_test_suites:
            results = []
            for decoder in run_decoders:
                if decoder.codec != test_suite.codec:
                    continue
                test_suite_res = test_suite.run(jobs, decoder, timeout, failfast, quiet,
                                                self.results_dir, reference, test_vectors, keep_files)

                if test_suite_res:
                    results.append((decoder, test_suite_res))
                    success = True
                    for test_vector in test_suite_res.test_vectors:
                        if test_vector.errors:
                            success = False
                            break

                    if not success:
                        if failfast:
                            sys.exit(1)
                        error = True

            if summary and results:
                self._generate_summary(results)
        if error:
            sys.exit(1)

    def _generate_summary(self, results: tuple):
        test_suite_name = results[0][1].name
        decoder_names = [decoder.name for decoder, _ in results]
        print(
            f'Generating summary for test suite {test_suite_name} and decoders {", ".join(decoder_names)}:\n')
        output = '|Test|'
        for decoder, _ in results:
            output += f'{decoder.name}|'
        output += f'\n|-|{"-|" * len(results)}'
        for test_vector in results[0][1].test_vectors:
            output += f'\n|{test_vector.name}|'
            for result in results:
                for tvector in result[1].test_vectors:
                    if tvector.name == test_vector.name:
                        output += '✔️|' if not tvector.errors else '❌|'
                        break
        print(output)

    def download_test_suites(self, test_suites: list, jobs: int, keep_file: bool):
        '''Download a group of test suites'''
        self._load_test_suites()
        if not test_suites:
            test_suites = self.test_suites
        else:
            test_suites = [
                t for t in self.test_suites if t.name in test_suites]
        for test_suite in test_suites:
            test_suite.download(jobs, self.resources_dir,
                                verify=True, keep_file=keep_file)
