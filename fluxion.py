#!/usr/bin/env python3

import argparse

from fluxion.fluxion import Fluxion

TEST_SUITES_DIR = 'test_suites'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity', action='store_true')
    parser.add_argument('-l', '--list', help='show list of test suites', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.list:
        return

    fluxion = Fluxion(TEST_SUITES_DIR, verbose=args.verbose)

    if args.list:
        fluxion.list_test_suites(show_test_vectors=args.verbose)


if __name__ == "__main__":
    main()
