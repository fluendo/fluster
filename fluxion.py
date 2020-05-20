#!/usr/bin/env python3

import argparse

from fluxion.fluxion import Fluxion

TEST_SUITES_DIR = 'test_suites'


def list_cmd(args, fluxion):
    fluxion.list_test_suites(show_test_vectors=args.detail)


def decoders_cmd(args, fluxion):
    fluxion.list_decoders()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity', action='store_true')
    subparsers = parser.add_subparsers(title='subcommands')

    list_parser = subparsers.add_parser(
        'list', aliases=['l'], help='show list of available test suites')
    list_parser.add_argument(
        '-d', '--detail', help='show details of test suites', action='store_true')
    list_parser.set_defaults(func=list_cmd)

    decoders_parser = subparsers.add_parser(
        'decoders', aliases=['d'], help='show list of available decoders')
    decoders_parser.set_defaults(func=decoders_cmd)

    return parser.parse_args()


def main():
    args = parse_args()
    fluxion = Fluxion(TEST_SUITES_DIR, verbose=args.verbose)
    if hasattr(args, 'func'):
        args.func(args, fluxion)


if __name__ == "__main__":
    main()
