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

TEST_SUITES_DIR = 'test_suites'
DECODERS_DIR = 'decoders'


def list_cmd(args, fluxion):
    if args.testsuites:
        fluxion.list_test_suites(show_test_vectors=args.testvectors)
    if args.decoders:
        fluxion.list_decoders()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity', action='store_true')
    subparsers = parser.add_subparsers(title='subcommands')

    list_parser = subparsers.add_parser(
        'list', aliases=['l'], help='show list of available test suites or decoders')
    list_parser.add_argument(
        '-ts', '--testsuites', help='show test suites', action='store_true')
    list_parser.add_argument(
        '-tv', '--testvectors', help='show test vectors of test suites', action='store_true')
    list_parser.add_argument(
        '-d', '--decoders', help='show decoders', action='store_true')
    list_parser.set_defaults(func=list_cmd)

    return parser.parse_args()


def main():
    args = parse_args()
    if hasattr(args, 'func'):
        fluxion = Fluxion(TEST_SUITES_DIR, DECODERS_DIR, verbose=args.verbose)
        args.func(args, fluxion)


if __name__ == "__main__":
    main()
