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

import copy
import fnmatch
import json
import os.path
from enum import Enum
from functools import lru_cache
from multiprocessing import Pool
from shutil import rmtree
from time import perf_counter
from typing import Dict, List, Optional, Set, Type, cast
from unittest.result import TestResult

from fluster import download_manager
from fluster.codec import Codec
from fluster.decoder import Decoder, get_reference_decoder_for_codec
from fluster.test import MD5ComparisonTest, PixelComparisonTest, ReferenceComparisonTest, SampleComparisonTest, Test
from fluster.test_vector import TestVector, TestVectorResult


class Context:
    """Context for TestSuite"""

    def __init__(
        self,
        jobs: int,
        decoder: Decoder,
        timeout: int,
        failfast: bool,
        quiet: bool,
        output_dir: str,
        reference: bool = False,
        test_vectors: Optional[List[str]] = None,
        skip_vectors: Optional[List[str]] = None,
        failing_test_vectors: Optional[List[str]] = None,
        keep_files: bool = False,
        verbose: bool = False,
        reference_decoder: Optional[Decoder] = None,
        test_vector_names: Optional[Set[str]] = None,
    ):
        self.jobs = jobs
        self.decoder = decoder
        self.timeout = timeout
        self.failfast = failfast
        self.quiet = quiet
        self.output_dir = output_dir
        self.reference = reference
        self.test_vectors = test_vectors
        self.skip_vectors = skip_vectors
        self.failing_test_vectors = failing_test_vectors
        self.keep_files = keep_files
        self.verbose = verbose
        self.reference_decoder = reference_decoder
        self.test_vector_names = test_vector_names


class TestMethod(Enum):
    """Test method types enum"""

    MD5 = "md5"
    PIXEL = "pixel"
    SAMPLE = "sample"


class TestSuite:
    """Test suite class"""

    TEST_SUITE_NAME = "TEST SUITE"
    DECODER_NAME = "DECODER"
    TEST_VECTOR_NAME = "TEST VECTOR"
    RESULT_NAME = "RESULT"

    def __init__(
        self,
        filename: str,
        resources_dir: str,
        name: str,
        codec: Codec,
        description: str,
        test_vectors: Dict[str, TestVector],
        failing_test_vectors: Optional[Dict[str, TestVector]] = None,
        test_method: TestMethod = TestMethod.MD5,
        negative_test: Optional[bool] = False,
    ):
        # JSON members
        # negative_test flag indicates that all test vectors of a test suite are expected to fail
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = test_vectors
        self.failing_test_vectors = failing_test_vectors
        self.test_method = test_method
        self.negative_test = negative_test

        # Not included in JSON
        self.filename = filename
        self.resources_dir = resources_dir
        self.test_vectors_success = 0
        self.test_vectors_not_run = 0
        self.test_vectors_not_supported = 0
        self.time_taken = 0.0

    def clone(self) -> "TestSuite":
        """Create a deep copy of the object"""
        return copy.deepcopy(self)

    @classmethod
    def from_json_file(cls: Type["TestSuite"], filename: str, resources_dir: str) -> "TestSuite":
        """Create a TestSuite instance from a file"""
        with open(filename, encoding="utf-8") as json_file:
            data = json.load(json_file)
            if "failing_test_vectors" in data:
                data["failing_test_vectors"] = dict(map(TestVector.from_json, data["failing_test_vectors"]))
            data["test_vectors"] = dict(map(TestVector.from_json, data["test_vectors"]))
            data["codec"] = Codec(data["codec"])
            if "test_method" in data:
                data["test_method"] = TestMethod(data["test_method"])
            # Remove runtime-only fields if present in malformed JSON
            data.pop("test_vectors_success", None)
            data.pop("test_vectors_not_run", None)
            data.pop("test_vectors_not_supported", None)
            data.pop("time_taken", None)
            return cls(filename, resources_dir, **data)

    def to_json_file(self, filename: str) -> None:
        """Serialize the test suite to a file"""
        with open(filename, "w", encoding="utf-8") as json_file:
            data = self.__dict__.copy()
            data.pop("resources_dir")
            data.pop("filename")
            data.pop("test_vectors_success")
            data.pop("test_vectors_not_run")
            data.pop("test_vectors_not_supported")
            data.pop("time_taken")
            if self.failing_test_vectors is None:
                data.pop("failing_test_vectors")
            else:
                data["failing_test_vectors"] = [
                    failing_test_vector.data_to_serialize()
                    for failing_test_vector in self.failing_test_vectors.values()
                ]
            data["codec"] = str(self.codec.value)
            data["test_vectors"] = [test_vector.data_to_serialize() for test_vector in self.test_vectors.values()]
            data["test_method"] = self.test_method.value if self.test_method else None
            if self.negative_test:
                data["negative_test"] = self.negative_test
            else:
                data.pop("negative_test")
            json.dump(data, json_file, indent=4)
            json_file.write("\n")

    def download_with_default_manager(self, jobs: int, *, extract_all: bool = False) -> None:
        """Download via a fresh DownloadManager configured for generator scripts.

        Verify off, keep archives, default retries — the common settings shared
        by the scripts/gen_*.py. Convenience wrapper so they don't each repeat
        the manager boilerplate."""
        cache_dir = os.path.join(self.resources_dir, ".cache")
        with download_manager.DownloadManager(
            cache_dir=cache_dir, verify=False, keep_file=True, retries=2, max_pool_workers=jobs
        ) as manager:
            manager.download_test_suite(self, jobs, self.resources_dir, extract_all=extract_all)

    @staticmethod
    def _rename_test(test: Test, module: str, qualname: str) -> None:
        test_cls = type(test)
        test_cls.__module__ = module
        test_cls.__qualname__ = qualname

    @staticmethod
    def _collect_results(test_result: TestResult) -> None:
        """Collect all TestResults with error to add them into the test vectors"""
        for res in test_result.failures:
            test_vector = cast(Test, res[0]).test_vector
            test_vector.errors.append([str(x) for x in res])
        for res in test_result.errors:
            test_vector = cast(Test, res[0]).test_vector
            test_vector.errors.append([str(x) for x in res])

    def _run_worker(self, test: Test) -> TestVector:
        """Run one unit test returning the TestVector"""
        # Save the original module and qualname to restore it before returning
        # the TestVector. Otherwise, Pickle will complain if the classes can't
        # be found in global scope. The trick here is that we change the names
        # momentarily just to obtain the error traces in str format
        test_cls = type(test)
        module_orig = test_cls.__module__
        qualname_orig = test_cls.__qualname__
        self._rename_test(test, test.decoder.name, test.test_suite.name)

        test_result = TestResult()
        test(test_result)

        self._collect_results(test_result)

        if self.negative_test and not test.skip:
            if test.test_vector.test_result == TestVectorResult.SUCCESS:
                test.test_vector.test_result = TestVectorResult.FAIL
            elif test.test_vector.test_result == TestVectorResult.FAIL:
                test.test_vector.test_result = TestVectorResult.SUCCESS

        self._rename_test(test, module_orig, qualname_orig)

        return test.test_vector

    @staticmethod
    def _get_max_length_list_name(_list: List[str], name: str) -> int:
        max_length = len(name)
        for elem in _list:
            length = len(elem)
            max_length = max(max_length, length)
        return max_length

    @lru_cache(maxsize=128)
    def _get_result_line(
        self,
        test_suite_text: str,
        decoder_text: str,
        test_vector_text: str,
        result_text: str,
        decoder_name: Optional[str] = None,
    ) -> str:
        decoder_name = decoder_text if not decoder_name else decoder_name
        tests_suite_max_len = self._get_max_length_list_name([self.name], TestSuite.TEST_SUITE_NAME)
        decoder_max_len = self._get_max_length_list_name([decoder_name], TestSuite.DECODER_NAME)
        test_vectors_max_len = self._get_max_length_list_name(
            list(self.test_vectors.keys()), TestSuite.TEST_VECTOR_NAME
        )

        return (
            f"[{test_suite_text:{tests_suite_max_len}}] ({decoder_text:{decoder_max_len}}) "
            f"{test_vector_text:{test_vectors_max_len}} ... {result_text}"
        )

    def run_test_suite_in_parallel(self, jobs: int, tests: List[Test], failfast: bool) -> None:
        """Run the test suite in parallel"""
        test_vector_results: List[TestVector] = []
        decoder = tests[0].decoder

        print(
            self._get_result_line(
                TestSuite.TEST_SUITE_NAME,
                TestSuite.DECODER_NAME,
                TestSuite.TEST_VECTOR_NAME,
                TestSuite.RESULT_NAME,
                decoder.name,
            )
            + f"\n{'-' * 70}"
        )
        with Pool(jobs) as pool:

            def _callback(test_result: TestVector) -> None:
                print(
                    self._get_result_line(
                        self.name,
                        decoder.name,
                        test_result.name,
                        test_result.test_result.value,
                    ),
                    flush=True,
                )
                test_vector_results.append(test_result)
                if failfast and test_result.errors and not self.negative_test:
                    pool.terminate()

            start = perf_counter()
            for test in tests:
                pool.apply_async(self._run_worker, (test,), callback=_callback)
            pool.close()
            pool.join()
        self.time_taken = perf_counter() - start
        print("\n")
        self.test_vectors_success = 0
        self.test_vectors_not_run = 0
        self.test_vectors_not_supported = 0
        for test_vector_res in test_vector_results:
            if test_vector_res.test_result == TestVectorResult.SUCCESS:
                self.test_vectors_success += 1
            elif test_vector_res.test_result == TestVectorResult.NOT_SUPPORTED:
                self.test_vectors_not_supported += 1
            elif test_vector_res.test_result == TestVectorResult.NOT_RUN:
                self.test_vectors_not_run += 1

            if test_vector_res.errors and not self.negative_test:
                for error in test_vector_res.errors:
                    # Use same format to report errors as TextTestRunner
                    print(f"{'=' * 71}\nFAIL: {error[0]}\n{'-' * 70}")
                    for line in error[1:]:
                        print(line)

            # Collect the test vector results and failures since they come
            # from a different process
            self.test_vectors[test_vector_res.name] = test_vector_res

        status_parts = [f"{self.test_vectors_success}/{len(tests)} tests successfully"]
        if self.test_vectors_not_run > 0:
            status_parts.append(f"{self.test_vectors_not_run} not run")
        if self.test_vectors_not_supported > 0:
            status_parts.append(f"{self.test_vectors_not_supported} not supported")
        status_parts.append(f"in {self.time_taken:.3f} secs")
        print(f"Ran {', '.join(status_parts)}")

    def run(self, ctx: Context) -> Optional["TestSuite"]:
        """
        Run the test suite.
        Returns a new copy of the test suite with the result of the test
        """

        if not ctx.decoder.check(ctx.verbose):
            print(f"Skipping decoder {ctx.decoder.name} because it cannot be run")
            return None

        if not os.path.exists(os.path.join(self.resources_dir, self.name)):
            print(
                f"Skipping test suite {self.name} because its resources are not available. "
                f"Please download it first, run `fluster.py download --help` for more information"
            )
            return None

        if self.test_method in (TestMethod.PIXEL, TestMethod.SAMPLE):
            ctx.reference_decoder = get_reference_decoder_for_codec(ctx.decoder.codec)
            if ctx.reference_decoder is None or not ctx.reference_decoder.check(ctx.verbose):
                print(f"Skipping test suite {self.name}: no reference decoder for codec {ctx.decoder.codec.name}")
                return None

        ctx.output_dir = os.path.join(ctx.output_dir, self.name)
        if os.path.exists(ctx.output_dir):
            rmtree(ctx.output_dir)
        os.makedirs(ctx.output_dir)

        if ctx.test_vectors:
            test_list = [name.lower() for name in self.test_vectors]
            ctx.test_vector_names = set()
            for pattern in ctx.test_vectors:
                ctx.test_vector_names.update(fnmatch.filter(test_list, pattern.lower()))

        test_suite = self.clone()
        tests = test_suite.generate_tests(ctx)
        if not tests:
            extra = ""
            if ctx.test_vectors:
                extra = "with names: " + ", ".join(ctx.test_vectors)
            print(f"No test vectors for suite {self.name} {extra}")
            return None

        print("*" * 100)
        string = f"Running test suite {self.name} with decoder {ctx.decoder.name}\n"
        if ctx.test_vectors:
            string += f"Test vectors {' '.join(ctx.test_vectors)}\n"
        if ctx.skip_vectors:
            string += f"Skipping test vectors {' '.join(ctx.skip_vectors)}\n"
        string += f"Using {ctx.jobs} parallel job(s)"
        print(string)
        print("*" * 100 + "\n")

        test_suite.run_test_suite_in_parallel(ctx.jobs, tests, ctx.failfast)

        if ctx.reference:
            test_suite.to_json_file(test_suite.filename)

        if not ctx.keep_files and os.path.isdir(ctx.output_dir):
            rmtree(ctx.output_dir)

        return test_suite

    def generate_tests(self, ctx: Context) -> List[Test]:
        """Generate the tests for a decoder"""
        tests: List[Test] = []
        test_vectors_run = {}

        reference_test_classes: Dict[TestMethod, Type[ReferenceComparisonTest]] = {
            TestMethod.PIXEL: PixelComparisonTest,
            TestMethod.SAMPLE: SampleComparisonTest,
        }

        for name, test_vector in self.test_vectors.items():
            skip = False
            name_lower = test_vector.name.lower()
            if ctx.test_vector_names is not None and name_lower not in ctx.test_vector_names:
                continue
            if ctx.skip_vectors and name_lower in ctx.skip_vectors:
                skip = True

            if self.test_method in reference_test_classes:
                assert ctx.reference_decoder is not None
                test_cls = reference_test_classes[self.test_method]
                tests.append(
                    test_cls(
                        ctx.decoder,
                        self,
                        test_vector,
                        skip,
                        ctx.output_dir,
                        ctx.reference,
                        ctx.timeout,
                        ctx.keep_files,
                        ctx.verbose,
                        ctx.reference_decoder,
                    )
                )
            else:
                tests.append(
                    MD5ComparisonTest(
                        ctx.decoder,
                        self,
                        test_vector,
                        skip,
                        ctx.output_dir,
                        ctx.reference,
                        ctx.timeout,
                        ctx.keep_files,
                        ctx.verbose,
                    )
                )
            test_vectors_run[name] = test_vector
        self.test_vectors = test_vectors_run
        return tests

    def __str__(self) -> str:
        return (
            f"\n{self.name}\n"
            f"    Codec: {self.codec.value}\n"
            f"    Description: {self.description}\n"
            f"    Test vectors: {len(self.test_vectors)}"
        )
