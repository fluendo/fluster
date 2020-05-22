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
import unittest

from fluxion.test_suite import TestSuite
from fluxion.decoder import DECODERS
from fluxion.test import Test, test_decode


def lazy_init(call_func):
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


class Fluxion:
    def __init__(self, test_suites_dir, decoders_dir, verbose=False):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.verbose = verbose
        self.test_suites = []
        self.decoders = DECODERS

    def load_decoders(self):
        for root, _, files in os.walk(self.decoders_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.py':
                    if self.verbose:
                        print(f'Decoder found: {file}')
                    try:
                        exec(open(os.path.join(root, file)).read(), globals())
                    except Exception as e:
                        print(f'Error loading decoder {file}: {e}')

    def load_test_suites(self):
        for root, _, files in os.walk(self.test_suites_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.json':
                    if self.verbose:
                        print(f'Test suite found: {file}')
                    try:
                        ts = TestSuite.from_json_file(os.path.join(root, file))
                        self.test_suites.append(ts)
                    except Exception as e:
                        print(f'Error loading test suite {file}: {e}')

    @lazy_init(load_decoders)
    def list_decoders(self):
        print('\nList of available decoders:\n')
        decoders_dict = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for codec in decoders_dict.keys():
            print(f'{codec}')
            for decoder in decoders_dict[codec]:
                print(decoder)

    @lazy_init(load_test_suites)
    def list_test_suites(self, show_test_vectors=False):
        print('\nList of available test suites:')
        for ts in self.test_suites:
            print(ts)
            if show_test_vectors:
                for tv in ts.test_vectors:
                    print(tv)

    def build_test_suite(self, test_suites, decoders):
        suite = unittest.TestSuite()
        for dec in decoders:
            for ts in test_suites:
                if ts.codec == dec.codec:
                    for tv in ts.test_vectors:
                        test_name = ''
                        for c in f'{dec.name}_{ts.name}_{tv.name}':
                            if c.isalnum():
                                test_name += c
                            else:
                                test_name += '_'
                        test = Test()
                        setattr(test, test_name, test_decode(test, dec, tv))
                        test.set_name(test_name)
                        suite.addTest(test)

        return suite

    @lazy_init(load_test_suites)
    @lazy_init(load_decoders)
    def run_test_suites(self, test_suites=None, decoders=None, failfast=False, quiet=False):
        def find_names_in_collection(text, names, collection):
            ret = []
            for name in names:
                found = False
                for entry in collection:
                    if entry.name.lower() == name.lower():
                        ret.append(entry)
                        found = True
                        break
                if not found:
                    raise Exception(f'Error: {text} "{name}" not found')
            return ret

        try:
            run_test_suites = []
            if test_suites:
                run_test_suites = find_names_in_collection('Test suite',
                                                           test_suites, self.test_suites)
            else:
                run_test_suites = self.test_suites

            run_decoders = []
            if decoders:
                run_decoders = find_names_in_collection('Decoder',
                                                        decoders, self.decoders)
            else:
                run_decoders = self.decoders
        except Exception as e:
            print(f'Error: {e}')
            return

        ts_names = [ts.name for ts in run_test_suites]
        dec_names = [dec.name for dec in run_decoders]
        print(
            f'Running test suites\n'
            f'{", ".join(ts_names)}\n\n'
            f'With decoders\n'
            f'{", ".join(dec_names)}\n')

        suite = self.build_test_suite(run_test_suites, run_decoders)
        runner = unittest.TextTestRunner(
            failfast=failfast, verbosity=1 if quiet else 2)
        runner.run(suite)
