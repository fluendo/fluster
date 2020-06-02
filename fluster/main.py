#!/usr/bin/env python3

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

import argparse
import os
import multiprocessing

from fluster.fluster import Fluster, Context


class Main:
    '''Main class for Fluster'''

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
        '''Runs Fluster'''
        args = self.parser.parse_args()
        if hasattr(args, 'func'):
            fluster = Fluster(self.test_suites_dir,
                              self.decoders_dir,
                              self.resources_dir,
                              self.results_dir,
                              verbose=args.verbose)
            args.func(args, fluster)
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
            help='check which decoders can be run successfully. Reports ✔️ or ❌', action='store_true')
        subparser.set_defaults(func=self._list_cmd)

    def _add_run_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'run', aliases=['r'], help='run test suites for decoders')
        subparser.add_argument(
            '-j', '--jobs', help='number of parallel jobs to use. 1x logical cores by default.'
            '0 means all logical cores',
            type=int, default=multiprocessing.cpu_count())
        subparser.add_argument('-t', '--timeout', help='timeout in secs for each decoding. Defaults to 5 secs',
                               type=int, default=5)
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
        subparser.add_argument(
            '-s', '--summary', help='generate a summary in Markdown format for each test suite', action='store_true')
        subparser.add_argument(
            '-k', '--keep', help="keep output files generated during the test", action='store_true')
        subparser.set_defaults(func=self._run_cmd)

    def _add_reference_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'reference', aliases=['r'], help='use a specific decoder as the reference for the test suites given')
        subparser.add_argument(
            '-j', '--jobs', help='number of parallel jobs to use. 1x logical cores by default.'
            '0 means all logical cores',
            type=int, default=multiprocessing.cpu_count())
        subparser.add_argument('-t', '--timeout', help='timeout in secs for each decoding. Defaults to 5 secs',
                               type=int, default=5)
        subparser.add_argument(
            'decoder', help='decoder to run', nargs=1)
        subparser.add_argument(
            'testsuites', help='list of testsuites to run the decoder with', nargs='+')
        subparser.add_argument(
            '-q', '--quiet', help="don't show every test run", action='store_true')
        subparser.set_defaults(func=self._reference_cmd)

    def _add_download_cmd(self, subparsers):
        subparser = subparsers.add_parser(
            'download', aliases=['d'], help='downloads test suites resources')
        subparser.add_argument(
            '-j', '--jobs', help='number of parallel jobs to use. 2x logical cores by default.'
            '0 means all logical cores',
            type=int, default=2 * multiprocessing.cpu_count())
        subparser.add_argument(
            '-k', '--keep', help="keep downloaded file after extracting", action='store_true')
        subparser.add_argument(
            'testsuites', help='list of testsuites to download', nargs='*')
        subparser.set_defaults(func=self._download_cmd)

    def _list_cmd(self, args, fluster):
        fluster.list_test_suites(
            show_test_vectors=args.testvectors, test_suites=args.testsuites)
        fluster.list_decoders(check_run=args.check)

    def _run_cmd(self, args, fluster):
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        if args.jobs > 1 and args.failfast:
            print(f'Error: failfast is not compatible with running {args.jobs} parallel jobs.'
                  ' Please use -j1 if you want to use failfast')
            return
        context = Context(jobs=args.jobs,
                          test_suites=args.testsuites,
                          timeout=args.timeout,
                          decoders=args.decoders,
                          test_vectors=args.testvectors,
                          failfast=args.failfast,
                          quiet=args.quiet,
                          summary=args.summary,
                          keep_files=args.keep)
        fluster.run_test_suites(context)

    def _reference_cmd(self, args, fluster):
        context = Context(jobs=args.jobs,
                          timeout=args.timeout,
                          test_suites=args.testsuites,
                          decoders=args.decoder,
                          quiet=args.quiet,
                          reference=True)
        fluster.run_test_suites(context)

    def _download_cmd(self, args, fluster):
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        fluster.download_test_suites(
            test_suites=args.testsuites, jobs=args.jobs, keep_file=args.keep)
