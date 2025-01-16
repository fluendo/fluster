# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

import os
import unittest
from subprocess import TimeoutExpired
from time import perf_counter
from typing import Any

from fluster.decoder import Decoder
from fluster.test_vector import TestVector, TestVectorResult
from fluster.utils import normalize_path


class Test(unittest.TestCase):
    """Test suite for decoder tests"""

    def __init__(
        self,
        decoder: Decoder,
        test_suite: Any,  # can't use TestSuite type because of circular dependency
        test_vector: TestVector,
        skip: bool,
        output_dir: str,
        reference: bool,
        timeout: int,
        keep_files: bool,
        verbose: bool,
    ):
        self.decoder = decoder
        self.test_suite = test_suite
        self.test_vector = test_vector
        self.skip = skip
        self.resources_dir = self.test_suite.resources_dir
        self.output_dir = output_dir
        self.reference = reference
        self.timeout = timeout
        self.keep_files = keep_files
        self.verbose = verbose
        setattr(self, test_vector.name, self._test)
        super().__init__(test_vector.name)

    def _test(self) -> None:
        if self.skip:
            self.test_suite.test_vectors[
                self.test_vector.name
            ].test_result = TestVectorResult.NOT_RUN
            return

        output_filepath = os.path.join(self.output_dir, self.test_vector.name + ".out")

        input_filepath = os.path.join(
            self.resources_dir,
            self.test_suite.name,
            (self.test_vector.name if not self.test_suite.is_single_archive else ""),
            self.test_vector.input_file,
        )
        output_filepath = normalize_path(output_filepath)
        input_filepath = normalize_path(input_filepath)

        try:
            start = perf_counter()
            result = self.decoder.decode(
                input_filepath,
                output_filepath,
                self.test_vector.output_format,
                self.timeout,
                self.verbose,
                self.keep_files,
            )
            self.test_suite.test_vectors[self.test_vector.name].test_time = (
                perf_counter() - start
            )
        except TimeoutExpired:
            self.test_suite.test_vectors[
                self.test_vector.name
            ].test_result = TestVectorResult.TIMEOUT
            self.test_suite.test_vectors[self.test_vector.name].test_time = (
                perf_counter() - start
            )
            raise
        except Exception:
            self.test_suite.test_vectors[
                self.test_vector.name
            ].test_result = TestVectorResult.ERROR
            self.test_suite.test_vectors[self.test_vector.name].test_time = (
                perf_counter() - start
            )
            raise

        if (
            not self.keep_files
            and os.path.exists(output_filepath)
            and os.path.isfile(output_filepath)
        ):
            os.remove(output_filepath)

        if not self.reference:
            self.test_suite.test_vectors[
                self.test_vector.name
            ].test_result = TestVectorResult.FAIL
            if self.test_vector.result.lower() == result.lower():
                self.test_suite.test_vectors[
                    self.test_vector.name
                ].test_result = TestVectorResult.SUCCESS
            self.assertEqual(
                self.test_vector.result.lower(),
                result.lower(),
                self.test_vector.name,
            )
        else:
            self.test_suite.test_vectors[
                self.test_vector.name
            ].test_result = TestVectorResult.REFERENCE
            self.test_suite.test_vectors[self.test_vector.name].result = result
