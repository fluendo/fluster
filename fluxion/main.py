#!/usr/bin/env python3

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

import argparse
import os

from fluxion.fluxion import Fluxion


class Main:
    '''Main class for Fluxion'''

    def __init__(self, test_suites_dir, decoders_dir, resources_dir, results_dir):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.resources_dir = resources_dir
        self.results_dir = results_dir
        self.parser = self._create_parser()

        # Prepend to the PATH the decoders_dir so that we can run them
        # without having to set the env for every single command
        os.environ['PATH'] = decoders_dir + ':' + os.environ['PATH']

    def run(self):
        '''Runs Fluxion'''
        args = self.parser.parse_args()
        if hasattr(args, 'func'):
            fluxion = Fluxion(self.test_suites_dir,
                              self.decoders_dir,
                              self.resources_dir,
                              self.results_dir,
                              verbose=args.verbose)
            args.func(args, fluxion)
        else:
            self.parser.print_help()

    def _create_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose',
                            help='increase output verbosity', action='store_true')
        subparsers = parser.add_subparsers(title='subcommands')
        self._add_list_cmd(subparsers)
        self._add_run_cmd(subparsers)
        self._add_download_cmd(subparsers)
        self._add_reference_cmd(subparsers)
        return parser

    def _add_list_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'list', aliases=['l'], help='show list of available test suites or decoders')
        subparser.add_argument(
            '-ts', '--testsuites', help='show only the test suites given', nargs='+')
        subparser.add_argument(
            '-tv', '--testvectors', help='show test vectors of test suites', action='store_true')
        subparser.add_argument(
            '-c', '--check',
            help='check which decoders can be run successfully. Reports \U00002714 or \U00002715', action='store_true')
        subparser.set_defaults(func=self._list_cmd)

    def _add_run_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'run', aliases=['r'], help='run test suites for decoders')
        subparser.add_argument(
            '-ff', '--failfast', help='stop after first fail', action='store_true')
        subparser.add_argument(
            '-q', '--quiet', help="don't show every test run", action='store_true')
        subparser.add_argument(
            '-ts', '--testsuites', help='run only the specific test suites', nargs='+')
        subparser.add_argument(
            '-tv', '--testvectors', help='run only the specific test vectors', nargs='+')
        subparser.add_argument(
            '-d', '--decoders', help='run only the specific decoders', nargs='+')
        subparser.set_defaults(func=self._run_cmd)

    def _add_download_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'download', aliases=['d'], help='downloads test suites resources')
        subparser.add_argument(
            '-k', '--keep', help="keep downloaded file after extracting", action='store_true', default=False)
        subparser.add_argument(
            'testsuites', help='list of testsuites to download', nargs='*')
        subparser.set_defaults(func=self._download_cmd)

    def _add_reference_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'reference', aliases=['d'], help='use a specific decoder as the reference for the test suites given')
        subparser.add_argument(
            'decoder', help='decoder to run', nargs=1)
        subparser.add_argument(
            'testsuites', help='list of testsuites to run the decoder with', nargs='+')
        subparser.add_argument(
            '-q', '--quiet', help="don't show every test run", action='store_true')
        subparser.set_defaults(func=self._reference_cmd)

    def _list_cmd(self, args, fluxion):
        fluxion.list_test_suites(
            show_test_vectors=args.testvectors, test_suites=args.testsuites)
        fluxion.list_decoders(check_run=args.check)

    def _run_cmd(self, args, fluxion):
        fluxion.run_test_suites(test_suites=args.testsuites,
                                decoders=args.decoders,
                                test_vectors=args.testvectors,
                                failfast=args.failfast,
                                quiet=args.quiet)

    def _download_cmd(self, args, fluxion):
        fluxion.download_test_suites(
            test_suites=args.testsuites, keep_file=args.keep)

    def _reference_cmd(self, args, fluxion):
        fluxion.run_test_suites(test_suites=args.testsuites,
                                decoders=args.decoder,
                                quiet=args.quiet,
                                reference=True)
