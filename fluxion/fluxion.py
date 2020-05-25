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

import os
import os.path
import functools

from fluxion.test_suite import TestSuite
from fluxion.decoder import DECODERS
from fluxion.decoders import *


def lazy_init(call_func):
    '''Initialize lazily a function'''
    def decorator_lazy_init(func):
        @functools.wraps(func)
        def func_wrapper(self, *args, **kwargs):
            if not call_func:
                raise Exception(
                    'A function needs to be given to the lazy_init decorator')
            flag_name = call_func.__name__ + '_already_called'
            if not hasattr(self, flag_name):
                self.flag_name = False
            if not self.flag_name:
                call_func(self)
            self.flag_name = True
            func(self, *args, **kwargs)
        return func_wrapper
    return decorator_lazy_init

# pylint: disable=broad-except


class Fluxion:
    '''Main class for Fluxion'''

    def __init__(self, test_suites_dir: str, decoders_dir: str, resources_dir: str,
                 results_dir: str, verbose: bool = False):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.resources_dir = resources_dir
        self.results_dir = results_dir
        self.verbose = verbose
        self.test_suites = []
        self.decoders = DECODERS

    def _load_test_suites(self):
        for root, _, files in os.walk(self.test_suites_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.json':
                    if self.verbose:
                        print(f'Test suite found: {file}')
                    try:
                        test_suite = TestSuite.from_json_file(
                            os.path.join(root, file))
                        self.test_suites.append(test_suite)
                    except Exception as ex:
                        print(f'Error loading test suite {file}: {ex}')

    def list_decoders(self):
        '''List all the available decoders'''
        print('\nList of available decoders:\n')
        decoders_dict = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for codec in decoders_dict:
            print(f'{codec}')
            for decoder in decoders_dict[codec]:
                print(decoder)

    @lazy_init(_load_test_suites)
    def list_test_suites(self, show_test_vectors=False):
        '''List all test suites'''
        print('\nList of available test suites:')
        for test_suite in self.test_suites:
            print(test_suite)
            if show_test_vectors:
                for test_vector in test_suite.test_vectors:
                    print(test_vector)

    @lazy_init(_load_test_suites)
    def run_test_suites(self, test_suites=None, decoders=None, failfast=False, quiet=False, reference=False):
        '''Run a group of test suites'''
        run_test_suites = []
        if test_suites:
            run_test_suites = [
                test_suite for test_suite in self.test_suites if test_suite.name in test_suites]
            if not run_test_suites:
                raise Exception(
                    "No test suite found matching {}".format(test_suites))
        else:
            run_test_suites = self.test_suites

        run_decoders = []
        if decoders:
            run_decoders = [
                dec for dec in self.decoders if dec.name in decoders]
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

        for test_suite in run_test_suites:
            for decoder in run_decoders:
                if decoder.codec != test_suite.codec:
                    continue
                test_suite.run(decoder, failfast, quiet,
                               self.results_dir, reference)

    @lazy_init(_load_test_suites)
    def download_test_suites(self, test_suites):
        '''Download a group of test suites'''
        if not test_suites:
            test_suites = self.test_suites
        else:
            test_suites = [
                t for t in self.test_suites if t.name in test_suites]
        for test_suite in test_suites:
            test_suite.download(self.resources_dir, True)
