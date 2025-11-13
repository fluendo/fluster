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
import sys
import zipfile
from enum import Enum
from functools import lru_cache
from multiprocessing import Pool
from shutil import rmtree
from time import perf_counter
from typing import Any, Dict, List, Optional, Set, Type, cast
from unittest.result import TestResult

from fluster import utils
from fluster.codec import Codec
from fluster.decoder import Decoder, get_reference_decoder_for_codec
from fluster.test import MD5ComparisonTest, PixelComparisonTest, Test
from fluster.test_vector import TestVector, TestVectorResult


class DownloadWork:
    """Context to pass to download worker"""

    def __init__(
        self,
        out_dir: str,
        verify: bool,
        extract_all: bool,
        keep_file: bool,
        test_suite_name: str,
        retries: int,
    ):
        self.out_dir = out_dir
        self.verify = verify
        self.extract_all = extract_all
        self.keep_file = keep_file
        self.test_suite_name = test_suite_name
        self.retries = retries

    # This is added to avoid having to create an extra ancestor class
    def set_test_vector(self, test_vector: TestVector) -> None:
        """Setter function for member variable test vector"""

        self.test_vector = test_vector


class DownloadWorkSingleArchive(DownloadWork):
    """Context to pass to single archive download worker"""

    def __init__(
        self,
        out_dir: str,
        verify: bool,
        extract_all: bool,
        keep_file: bool,
        test_suite_name: str,
        test_vectors: Dict[str, TestVector],
        retries: int,
    ):
        super().__init__(out_dir, verify, extract_all, keep_file, test_suite_name, retries)
        self.test_vectors = test_vectors


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
            # Remove runtime-only fields that might be present in old JSON files
            data.pop("test_vectors_success", None)
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

    @staticmethod
    def _download_single_test_vector(ctx: DownloadWork) -> None:
        """Download and extract a single test vector"""
        dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name, ctx.test_vector.name)
        dest_path = os.path.join(dest_dir, os.path.basename(ctx.test_vector.source))
        os.makedirs(dest_dir, exist_ok=True)

        if (
            ctx.verify
            and os.path.exists(dest_path)
            and ctx.test_vector.source_checksum == utils.file_checksum(dest_path)
        ):
            # Remove file only in case the input file was extractable.
            # Otherwise, we'd be removing the original file we want to work
            # with every even time we execute the download subcommand.
            if utils.is_extractable(dest_path) and not ctx.keep_file:
                os.remove(dest_path)
            return

        print(f"\tDownloading test vector {ctx.test_vector.name} from {ctx.test_vector.source}")
        utils.download(ctx.test_vector.source, dest_dir, ctx.retries**ctx.retries)

        if ctx.test_vector.source_checksum != "__skip__":
            checksum = utils.file_checksum(dest_path)
            if ctx.test_vector.source_checksum != checksum:
                raise Exception(
                    f"Checksum mismatch for {ctx.test_vector.name}: {checksum} instead of "
                    f"{ctx.test_vector.source_checksum}"
                )

        if utils.is_extractable(dest_path):
            print(f"\tExtracting test vector {ctx.test_vector.name} to {dest_dir}")
            utils.extract(dest_path, dest_dir, file=ctx.test_vector.input_file if not ctx.extract_all else None)
            if not ctx.keep_file:
                os.remove(dest_path)

    @staticmethod
    def _download_single_archive(ctx: DownloadWorkSingleArchive) -> None:
        """Download a single archive containing many test vectors and extract them"""
        first_tv = ctx.test_vectors[next(iter(ctx.test_vectors))]
        dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name)
        dest_path = os.path.join(dest_dir, os.path.basename(first_tv.source))
        os.makedirs(dest_dir, exist_ok=True)

        # Clean up existing corrupt source file
        if (
            ctx.verify
            and os.path.exists(dest_path)
            and utils.is_extractable(dest_path)
            and first_tv.source_checksum != utils.file_checksum(dest_path)
        ):
            os.remove(dest_path)

        print(f"\tDownloading source file from {first_tv.source}")
        utils.download(first_tv.source, dest_dir, ctx.retries**ctx.retries)

        # Check that source file was downloaded correctly
        if first_tv.source_checksum != "__skip__":
            checksum = utils.file_checksum(dest_path)
            if first_tv.source_checksum != checksum:
                raise Exception(
                    f"Checksum mismatch for source file {os.path.basename(first_tv.source)}: {checksum} "
                    f"instead of '{first_tv.source_checksum}'"
                )

        try:
            with zipfile.ZipFile(dest_path, "r") as zip_file:
                print(f"\tExtracting test vectors from {os.path.basename(first_tv.source)}")
                for tv in ctx.test_vectors.values():
                    if tv.input_file in zip_file.namelist():
                        zip_file.extract(tv.input_file, dest_dir)
                    else:
                        print(
                            f"WARNING: test vector {tv.input_file} not found inside {os.path.basename(first_tv.source)}"
                        )
        except zipfile.BadZipFile as bad_zip_error:
            os.remove(dest_path)
            raise Exception(f"{dest_path} could not be opened as zip file. File was deleted") from bad_zip_error

        # Remove source file, if applicable
        if not ctx.keep_file:
            os.remove(dest_path)

    def download(
        self,
        jobs: int,
        out_dir: str,
        verify: bool,
        extract_all: bool = False,
        keep_file: bool = False,
        retries: int = 2,
    ) -> None:
        """Download the test suite"""
        os.makedirs(out_dir, exist_ok=True)
        unique_sources = {tv.source for tv in self.test_vectors.values()}

        if (
            len(unique_sources) == 1
            and len(self.test_vectors) > 1
            and utils.is_extractable(os.path.basename(next(iter(unique_sources))))
        ):
            # Download test suite of multiple test vectors from a single archive
            print(f"Downloading test suite {self.name} using 1 job (single archive)")
            dwork_single = DownloadWorkSingleArchive(
                out_dir, verify, extract_all, keep_file, self.name, self.test_vectors, retries
            )
            self._download_single_archive(dwork_single)
        elif len(unique_sources) == 1 and len(self.test_vectors) == 1:
            # Download test suite of single test vector
            print(f"Downloading test suite {self.name} using 1 job (single file)")
            single_tv = next(iter(self.test_vectors.values()))
            dwork = DownloadWork(out_dir, verify, extract_all, keep_file, self.name, retries)
            dwork.set_test_vector(single_tv)
            self._download_single_test_vector(dwork)
        else:
            # Download test suite of multiple test vectors
            print(f"Downloading test suite {self.name} using {jobs} parallel jobs")
            error_occurred = False
            with Pool(jobs) as pool:

                def _callback_error(err: Any) -> None:
                    nonlocal error_occurred
                    error_occurred = True
                    print(f"\nError downloading -> {err}\n")
                    pool.terminate()

                downloads = []
                for tv in self.test_vectors.values():
                    dwork = DownloadWork(out_dir, verify, extract_all, keep_file, self.name, retries)
                    dwork.set_test_vector(tv)
                    downloads.append(
                        pool.apply_async(
                            self._download_single_test_vector,
                            args=(dwork,),
                            error_callback=_callback_error,
                        )
                    )

                pool.close()
                pool.join()

            if error_occurred:
                sys.exit("Some download failed")
            else:
                for job in downloads:
                    if not job.successful():
                        sys.exit("Some download failed")

        print("All downloads finished")

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
                if self.negative_test:
                    if test_result.errors:
                        test_result.test_result = TestVectorResult.SUCCESS
                    else:
                        test_result.test_result = TestVectorResult.FAIL
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
        self.test_vectors_not_supported = 0
        for test_vector_res in test_vector_results:
            # Check for NOT_SUPPORTED first
            if test_vector_res.test_result == TestVectorResult.NOT_SUPPORTED:
                self.test_vectors_not_supported += 1
            elif test_vector_res.errors:
                if self.negative_test:
                    self.test_vectors_success += 1
                else:
                    for error in test_vector_res.errors:
                        # Use same format to report errors as TextTestRunner
                        print(f"{'=' * 71}\nFAIL: {error[0]}\n{'-' * 70}")
                        for line in error[1:]:
                            print(line)
            else:
                if not self.negative_test:
                    self.test_vectors_success += 1

            # Collect the test vector results and failures since they come
            # from a different process
            self.test_vectors[test_vector_res.name] = test_vector_res

        # Build status message
        status_parts = [f"{self.test_vectors_success}/{len(tests)} tests successfully"]
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

        if self.test_method == TestMethod.PIXEL:
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

        for name, test_vector in self.test_vectors.items():
            skip = False
            name_lower = test_vector.name.lower()
            if ctx.test_vector_names is not None and name_lower not in ctx.test_vector_names:
                continue
            if ctx.skip_vectors and name_lower in ctx.skip_vectors:
                skip = True

            if self.test_method == TestMethod.PIXEL:
                assert ctx.reference_decoder is not None
                tests.append(
                    PixelComparisonTest(
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
