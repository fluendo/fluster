#!/usr/bin/env python3

from fluxion.fluxion import Fluxion

TEST_SUITES_DIR = 'test_suites'


def main():
    print('Fluxion!')
    fluxion = Fluxion(TEST_SUITES_DIR, verbose=True)


if __name__ == "__main__":
    main()
