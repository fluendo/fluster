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
from fluxion.fluxion import Fluxion


class Main:

    def __init__(self, test_suites_dir, decoders_dir):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.parser = self.create_parser()

    def run(self):
        args = self.parse_args()
        if hasattr(args, 'func'):
            fluxion = Fluxion(self.test_suites_dir, self.decoders_dir, verbose=args.verbose)
            args.func(args, fluxion)
        else:
            self.parser.print_help()

    def create_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose',
                            help='increase output verbosity', action='store_true')
        subparsers = parser.add_subparsers(title='subcommands')
        self.add_list_cmd(subparsers)
        self.add_run_cmd(subparsers)
        return parser

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose',
                            help='increase output verbosity', action='store_true')
        subparsers = parser.add_subparsers(title='subcommands')
        self.add_list_cmd(subparsers)
        self.add_run_cmd(subparsers)
        return parser.parse_args()

    def add_list_cmd(self, subparsers):
        list_parser = subparsers.add_parser(
            'list', aliases=['l'], help='show list of available test suites or decoders')
        list_parser.add_argument(
            '-ts', '--testsuites', help='show test suites', action='store_true')
        list_parser.add_argument(
            '-tv', '--testvectors', help='show test vectors of test suites', action='store_true')
        list_parser.add_argument(
            '-d', '--decoders', help='show decoders', action='store_true')
        list_parser.set_defaults(func=self.list_cmd)

    def add_run_cmd(self, subparsers):
        run_parser = subparsers.add_parser(
            'run', aliases=['r'], help='run test suites for decoders')
        run_parser.add_argument(
            '-ff', '--failfast', help='stop after first fail', action='store_true')
        run_parser.add_argument(
            '-q', '--quiet', help="don't show every test run", action='store_true')
        run_parser.add_argument(
            '-ts', '--testsuites', help='run only the specific test suites', nargs='+')
        run_parser.add_argument(
            '-d', '--decoders', help='run only the specific decoders', nargs='+')
        run_parser.set_defaults(func=self.run_cmd)

    def list_cmd(self, args, fluxion):
        if args.testsuites:
            fluxion.list_test_suites(show_test_vectors=args.testvectors)
        if args.decoders:
            fluxion.list_decoders()

    def run_cmd(self, args, fluxion):
        fluxion.run_test_suites(test_suites=args.testsuites,
                                decoders=args.decoders, failfast=args.failfast, quiet=args.quiet)
