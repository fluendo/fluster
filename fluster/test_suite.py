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

from functools import lru_cache
import os.path
import json
import copy
import sys
from multiprocessing import Pool
from unittest.result import TestResult
from time import perf_counter
from shutil import rmtree
from typing import cast, List, Dict, Optional, Type, Any


from fluster.test_vector import TestVector
from fluster.codec import Codec
from fluster.decoder import Decoder
from fluster.test import Test
from fluster import utils


class DownloadWork:
    """Context to pass to each download worker"""

    def __init__(
        self,
        out_dir: str,
        verify: bool,
        extract_all: bool,
        keep_file: bool,
        test_suite_name: str,
        test_vector: TestVector,
    ):
        self.out_dir = out_dir
        self.verify = verify
        self.extract_all = extract_all
        self.keep_file = keep_file
        self.test_suite_name = test_suite_name
        self.test_vector = test_vector


class Context:
    """Context for TestSuite"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        jobs: int,
        decoder: Decoder,
        timeout: int,
        failfast: bool,
        quiet: bool,
        results_dir: str,
        reference: bool = False,
        test_vectors: Optional[List[str]] = None,
        skip_vectors: Optional[List[str]] = None,
        failing_test_vectors: Optional[List[str]] = None,
        keep_files: bool = False,
        verbose: bool = False,
    ):
        self.jobs = jobs
        self.decoder = decoder
        self.timeout = timeout
        self.failfast = failfast
        self.quiet = quiet
        self.results_dir = results_dir
        self.reference = reference
        self.test_vectors = test_vectors
        self.skip_vectors = skip_vectors
        self.failing_test_vectors = failing_test_vectors
        self.keep_files = keep_files
        self.verbose = verbose


class TestSuite:
    """Test suite class"""

    # pylint: disable=too-many-instance-attributes

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
    ):
        # JSON members
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = test_vectors
        self.failing_test_vectors = failing_test_vectors

        # Not included in JSON
        self.filename = filename
        self.resources_dir = resources_dir
        self.test_vectors_success = 0
        self.time_taken = 0.0

    def clone(self) -> "TestSuite":
        """Create a deep copy of the object"""
        return copy.deepcopy(self)

    @classmethod
    def from_json_file(
        cls: Type["TestSuite"], filename: str, resources_dir: str
    ) -> "TestSuite":
        """Create a TestSuite instance from a file"""
        with open(filename, encoding="utf-8") as json_file:
            data = json.load(json_file)
            if "failing_test_vectors" in data:
                data["failing_test_vectors"] = dict(
                    map(TestVector.from_json, data["failing_test_vectors"])
                )
            data["test_vectors"] = dict(map(TestVector.from_json, data["test_vectors"]))
            data["codec"] = Codec(data["codec"])
            return cls(filename, resources_dir, **data)

    def to_json_file(self, filename: str) -> None:
        """Serialize the test suite to a file"""
        with open(filename, "w", encoding="utf-8") as json_file:
            data = self.__dict__.copy()
            data.pop("resources_dir")
            data.pop("filename")
            data.pop("test_vectors_success")
            data.pop("time_taken")
            if self.failing_test_vectors is None:
                data.pop("failing_test_vectors")
            else:
                data["failing_test_vectors"] = [
                    failing_test_vector.data_to_serialize()
                    for failing_test_vector in self.failing_test_vectors.values()
                ]
            data["codec"] = str(self.codec.value)
            data["test_vectors"] = [
                test_vector.data_to_serialize()
                for test_vector in self.test_vectors.values()
            ]
            json.dump(data, json_file, indent=4)

    def _download_worker(self, ctx: DownloadWork) -> None:
        """Download and extract a test vector"""
        test_vector = ctx.test_vector
        dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name, test_vector.name)
        dest_path = os.path.join(dest_dir, os.path.basename(test_vector.source))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        if (
            ctx.verify
            and os.path.exists(dest_path)
            and test_vector.source_checksum == utils.file_checksum(dest_path)
        ):
            # Remove file only in case the input file was extractable.
            # Otherwise, we'd be removing the original file we want to work
            # with every even time we execute the download subcommand.
            if utils.is_extractable(dest_path) and not ctx.keep_file:
                os.remove(dest_path)
            return
        print(f"\tDownloading test vector {test_vector.name} from {dest_dir}")
        # Catch the exception that download may throw to make sure pickle can serialize it properly
        # This avoids:
        # Error sending result: '<multiprocessing.pool.ExceptionWithTraceback object at 0x7fd7811ecee0>'.
        # Reason: 'TypeError("cannot pickle '_io.BufferedReader' object")'
        try:
            utils.download(test_vector.source, dest_dir)
        except Exception as ex:
            raise Exception(str(ex)) from ex
        if test_vector.source_checksum != "__skip__":
            checksum = utils.file_checksum(dest_path)
            if test_vector.source_checksum != checksum:
                raise Exception(
                    f"Checksum error for test vector '{test_vector.name}': '{checksum}' instead of "
                    f"'{test_vector.source_checksum}'"
                )

        if utils.is_extractable(dest_path):
            print(f"\tExtracting test vector {test_vector.name} to {dest_dir}")
            utils.extract(
                dest_path,
                dest_dir,
                file=test_vector.input_file if not ctx.extract_all else None,
            )
            if not ctx.keep_file:
                os.remove(dest_path)

    def download(
        self,
        jobs: int,
        out_dir: str,
        verify: bool,
        extract_all: bool = False,
        keep_file: bool = False,
    ) -> None:
        """Download the test suite"""
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        print(f"Downloading test suite {self.name} using {jobs} parallel jobs")

        with Pool(jobs) as pool:

            def _callback_error(err: Any) -> None:
                print(f"\nError downloading -> {err}\n")
                pool.terminate()

            downloads = []
            for test_vector in self.test_vectors.values():
                dwork = DownloadWork(
                    out_dir,
                    verify,
                    extract_all,
                    keep_file,
                    self.name,
                    test_vector,
                )
                downloads.append(
                    pool.apply_async(
                        self._download_worker,
                        args=(dwork,),
                        error_callback=_callback_error,
                    )
                )
            pool.close()
            pool.join()

        for job in downloads:
            if not job.successful():
                sys.exit("Some download failed")

        print("All downloads finished")

    def _rename_test(self, test: Test, module: str, qualname: str) -> None:
        test_cls = type(test)
        test_cls.__module__ = module
        test_cls.__qualname__ = qualname

    def _collect_results(self, test_result: TestResult) -> None:
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
        self._rename_test(test, module_orig, qualname_orig)

        return test.test_vector

    def _get_max_length_list_name(self, _list: List[str], name: str) -> int:
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
        tests_suite_max_len = self._get_max_length_list_name(
            [self.name], TestSuite.TEST_SUITE_NAME
        )
        decoder_max_len = self._get_max_length_list_name(
            [decoder_name], TestSuite.DECODER_NAME
        )
        test_vectors_max_len = self._get_max_length_list_name(
            list(self.test_vectors.keys()), TestSuite.TEST_VECTOR_NAME
        )

        return (
            f"[{test_suite_text:{tests_suite_max_len}}] ({decoder_text:{decoder_max_len}}) "
            f"{test_vector_text:{test_vectors_max_len}} ... {result_text}"
        )

    def run_test_suite_in_parallel(
        self, jobs: int, tests: List[Test], failfast: bool
    ) -> None:
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
            + f'\n{"-" * 70}'
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
                if failfast and test_result.errors:
                    pool.terminate()

            start = perf_counter()
            for test in tests:
                pool.apply_async(self._run_worker, (test,), callback=_callback)
            pool.close()
            pool.join()
        self.time_taken = perf_counter() - start
        print("\n")
        self.test_vectors_success = 0
        for test_vector_res in test_vector_results:
            if test_vector_res.errors:
                for error in test_vector_res.errors:
                    # Use same format to report errors as TextTestRunner
                    print(f'{"=" * 71}\nFAIL: {error[0]}\n{"-" * 70}')
                    for line in error[1:]:
                        print(line)
            else:
                self.test_vectors_success += 1

            # Collect the test vector results and failures since they come
            # from a different process
            self.test_vectors[test_vector_res.name] = test_vector_res
        print(
            f"Ran {self.test_vectors_success}/{len(tests)} tests successfully \
              in {self.time_taken:.3f} secs"
        )

    def run(self, ctx: Context) -> Optional["TestSuite"]:
        """
        Run the test suite.
        Returns a new copy of the test suite with the result of the test
        """
        # pylint: disable=too-many-locals

        if not ctx.decoder.check(ctx.verbose):
            print(f"Skipping decoder {ctx.decoder.name} because it cannot be run")
            return None

        ctx.results_dir = os.path.join(ctx.results_dir, self.name)
        if os.path.exists(ctx.results_dir):
            rmtree(ctx.results_dir)
        os.makedirs(ctx.results_dir)

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
            string += f'Test vectors {" ".join(ctx.test_vectors)}\n'
        if ctx.skip_vectors:
            string += f'Skipping test vectors {" ".join(ctx.skip_vectors)}\n'
        string += f"Using {ctx.jobs} parallel job(s)"
        print(string)
        print("*" * 100 + "\n")

        test_suite.run_test_suite_in_parallel(ctx.jobs, tests, ctx.failfast)

        if ctx.reference:
            test_suite.to_json_file(test_suite.filename)

        if not ctx.keep_files and os.path.isdir(ctx.results_dir):
            rmtree(ctx.results_dir)

        return test_suite

    def generate_tests(self, ctx: Context) -> List[Test]:
        """Generate the tests for a decoder"""
        tests = []
        test_vectors_run = {}
        for name, test_vector in self.test_vectors.items():
            skip = False
            if ctx.test_vectors:
                if test_vector.name.lower() not in ctx.test_vectors:
                    continue
            if ctx.skip_vectors:
                if test_vector.name.lower() in ctx.skip_vectors:
                    skip = True
            tests.append(
                Test(
                    ctx.decoder,
                    self,
                    test_vector,
                    skip,
                    ctx.results_dir,
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
