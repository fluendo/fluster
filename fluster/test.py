# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.

import os
import unittest
from abc import abstractmethod
from subprocess import TimeoutExpired
from time import perf_counter
from typing import Any

from fluster.decoder import Decoder
from fluster.test_vector import TestVector, TestVectorResult
from fluster.utils import compare_byte_wise_files, normalize_path


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
        self._keep_files_during_test = False
        self.test_vector_result = self.test_suite.test_vectors[self.test_vector.name]

        # Set up the test method
        setattr(self, test_vector.name, self._test_wrapper)
        super().__init__(test_vector.name)

        # Initialize file paths
        self._initialize_file_paths()

    def _initialize_file_paths(self) -> None:
        """Initialize input and output file paths."""
        self.output_filepath = normalize_path(os.path.join(self.output_dir, self.test_vector.name + ".out"))

        input_dir = os.path.join(self.resources_dir, self.test_suite.name)

        if not self.test_suite.is_single_archive:
            input_dir = os.path.join(input_dir, self.test_vector.name)

        self.input_filepath = normalize_path(os.path.join(input_dir, self.test_vector.input_file))

    def _execute_decode(self) -> str:
        """Execute the decoder and return the result."""
        keep_files_for_decode = self._keep_files_during_test or self.keep_files

        return self.decoder.decode(
            self.input_filepath,
            self.output_filepath,
            self.test_vector.output_format,
            self.timeout,
            self.verbose,
            keep_files_for_decode,
        )

    def _cleanup_if_needed(self) -> None:
        """Clean up output files if keep_files is False."""
        if not self.keep_files and os.path.exists(self.output_filepath):
            os.remove(self.output_filepath)

    def _test_wrapper(self) -> None:
        try:
            self._test()
        finally:
            self._cleanup_if_needed()

    def _test(self) -> None:
        """Execute the test and process results."""
        if self.skip:
            self.test_vector_result.test_result = TestVectorResult.NOT_RUN
            return

        start = perf_counter()

        try:
            result = self._execute_decode()
            self.test_vector_result.test_time = perf_counter() - start
        except TimeoutExpired:
            self.test_vector_result.test_result = TestVectorResult.TIMEOUT
            self.test_vector_result.test_time = perf_counter() - start
            raise
        except Exception:
            self.test_vector_result.test_result = TestVectorResult.ERROR
            self.test_vector_result.test_time = perf_counter() - start
            raise

        if self.reference:
            self.test_vector_result.test_result = TestVectorResult.REFERENCE
            self.test_vector_result.result = result
        else:
            try:
                self.compare_result(result)
                self.test_vector_result.test_result = TestVectorResult.SUCCESS
            except Exception:
                self.test_vector_result.test_result = TestVectorResult.FAIL
                raise

    @abstractmethod
    def compare_result(self, result: str) -> None:
        """Compare the test result with the expected value.

        Args:
            result: The result string from the decoder
        """


class MD5ComparisonTest(Test):
    """Test class for MD5 comparison"""

    def compare_result(self, result: str) -> None:
        """Compare MD5 hash results."""
        expected = self.test_vector.result.lower()
        actual = result.lower()

        self.assertEqual(expected, actual, self.test_vector.name)


class PixelComparisonTest(Test):
    """Test class for pixel comparison"""

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
        reference_decoder: Decoder,
    ):
        super().__init__(
            decoder,
            test_suite,
            test_vector,
            skip,
            output_dir,
            reference,
            timeout,
            keep_files,
            verbose,
        )
        self._keep_files_during_test = True
        self.reference_decoder = reference_decoder
        self.reference_filepath = normalize_path(os.path.join(self.output_dir, self.test_vector.name + "_ref.yuv"))

    def _decode_reference(self) -> str:
        """Decode the reference file."""
        keep_files_for_decode = self._keep_files_during_test or self.keep_files

        return self.reference_decoder.decode(
            self.input_filepath,
            self.reference_filepath,
            self.test_vector.output_format,
            self.timeout,
            self.verbose,
            keep_files_for_decode,
        )

    def _cleanup_if_needed(self) -> None:
        super()._cleanup_if_needed()
        for filepath in [self.reference_filepath, self.reference_filepath + ".yuv"]:
            if not self.keep_files and os.path.exists(filepath):
                os.remove(filepath)

    def compare_result(self, result: str) -> None:
        """Compare decoded output with reference decoder output pixel-wise."""
        reference_result = self._decode_reference()

        actual_reference_file = reference_result
        if not os.path.exists(reference_result):
            actual_reference_file = (
                self.reference_filepath + ".yuv"
                if os.path.exists(self.reference_filepath + ".yuv")
                else self.reference_filepath
            )

        comparison_result = compare_byte_wise_files(
            actual_reference_file, self.output_filepath, keep_files=self.keep_files
        )

        self.assertEqual(0, comparison_result, self.test_vector.name)
