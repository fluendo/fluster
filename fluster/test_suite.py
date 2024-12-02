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
import urllib.error
import zipfile


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
        # pylint: disable=attribute-defined-outside-init

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
        super().__init__(
            out_dir, verify, extract_all, keep_file, test_suite_name, retries
        )
        self.test_vectors = test_vectors


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
        output_dir: str,
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
        self.output_dir = output_dir
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
        is_single_archive: Optional[bool] = False,
        failing_test_vectors: Optional[Dict[str, TestVector]] = None,
    ):
        # JSON members
        self.name = name
        self.codec = codec
        self.description = description
        self.is_single_archive = is_single_archive
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
            if self.is_single_archive is False:
                data.pop("is_single_archive")
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

    @staticmethod
    def _download_worker(ctx: DownloadWork) -> None:
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
        for i in range(ctx.retries):
            try:
                exception_str = ""
                utils.download(test_vector.source, dest_dir)
            except urllib.error.URLError as ex:
                exception_str = str(ex)
                print(
                    f"\tUnable to download {test_vector.source} to {dest_dir}, {exception_str}, retry count={i+1}"
                )
                continue
            except Exception as ex:
                raise Exception(str(ex)) from ex
            break

        if exception_str:
            raise Exception(exception_str)

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

    @staticmethod
    def _download_worker_single_archive(ctx: DownloadWorkSingleArchive) -> None:
        """Download single archive test suite and extract all test vectors"""

        test_vectors = ctx.test_vectors
        # Extract 1st test vector from the Dict to use as reference for the download process of .zip source file that
        # contains all test vectors
        test_vector_0 = test_vectors[next(iter(test_vectors))]
        dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name)
        # Local path to source file
        dest_path = os.path.join(dest_dir, os.path.basename(test_vector_0.source))

        # Clean up existing corrupt source file
        if (
            ctx.verify
            and os.path.exists(dest_path)
            and utils.is_extractable(dest_path)
            and test_vector_0.source_checksum != utils.file_checksum(dest_path)
        ):
            os.remove(dest_path)
            print(
                f"\tRemoved source file {dest_path} from path, checksum doesn't match with expected"
            )

        os.makedirs(dest_dir, exist_ok=True)

        print(f"\tDownloading source file from {test_vector_0.source}")
        for i in range(ctx.retries):
            try:
                exception_str = ""
                utils.download(test_vector_0.source, dest_dir)
            except urllib.error.URLError as ex:
                exception_str = str(ex)
                print(
                    f"\tUnable to download {test_vector_0.source} to {dest_dir}, "
                    f"{exception_str}, retry count={i+1}"
                )
                continue
            except Exception as ex:
                raise Exception(str(ex)) from ex
            break

        if exception_str:
            raise Exception(exception_str)

        # Check that source file was downloaded correctly
        if test_vector_0.source_checksum != "__skip__":
            checksum = utils.file_checksum(dest_path)
            if test_vector_0.source_checksum != checksum:
                raise Exception(
                    f"Checksum error for source file '{os.path.basename(test_vector_0.source)}': "
                    f"'{checksum}' instead of '{test_vector_0.source_checksum}'"
                )

        # Extract all test vectors from compressed source file
        try:
            with zipfile.ZipFile(dest_path, "r") as zip_file:
                print(
                    f"\tExtracting test vectors from {os.path.basename(test_vector_0.source)}"
                )
                for test_vector_iter in test_vectors.values():
                    if test_vector_iter.input_file in zip_file.namelist():
                        zip_file.extract(test_vector_iter.input_file, dest_dir)
                    else:
                        print(
                            f"WARNING: test vector {test_vector_iter.input_file} was not found inside source file "
                            f"{os.path.basename(test_vector_iter.source)}"
                        )
        except zipfile.BadZipFile as bad_zip_exception:
            raise Exception(
                f"{dest_path} could not be opened as zip file. Delete the file manually and re-try."
            ) from bad_zip_exception

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
        retries: int = 1,
    ) -> None:
        """Download the test suite"""
        os.makedirs(out_dir, exist_ok=True)

        with Pool(jobs) as pool:

            def _callback_error(err: Any) -> None:
                print(f"\nError downloading -> {err}\n")
                pool.terminate()

            downloads = []

            if self.is_single_archive is False:
                print(f"Downloading test suite {self.name} using {jobs} parallel jobs")
                for test_vector in self.test_vectors.values():
                    dwork = DownloadWork(
                        out_dir,
                        verify,
                        extract_all,
                        keep_file,
                        self.name,
                        retries,
                    )
                    dwork.set_test_vector(test_vector)
                    downloads.append(
                        pool.apply_async(
                            self._download_worker,
                            args=(dwork,),
                            error_callback=_callback_error,
                        )
                    )
            else:
                print(
                    f"Downloading test suite {self.name} using 1 job (no parallel execution possible)"
                )
                dwork_single_archive = DownloadWorkSingleArchive(
                    out_dir,
                    verify,
                    extract_all,
                    keep_file,
                    self.name,
                    self.test_vectors,
                    retries,
                )
                # We can only use 1 parallel job because all test vectors are inside the same .zip source file
                downloads.append(
                    pool.apply_async(
                        self._download_worker_single_archive,
                        args=(dwork_single_archive,),
                        error_callback=_callback_error,
                    )
                )
            pool.close()
            pool.join()

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

        ctx.output_dir = os.path.join(ctx.output_dir, self.name)
        if os.path.exists(ctx.output_dir):
            rmtree(ctx.output_dir)
        os.makedirs(ctx.output_dir)

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

        if not ctx.keep_files and os.path.isdir(ctx.output_dir):
            rmtree(ctx.output_dir)

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
