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

from collections import defaultdict
import os
import os.path
from functools import lru_cache
from typing import List, Dict, Any, Tuple, Optional
import sys
from enum import Enum

# Import decoders that will auto-register
# pylint: disable=wildcard-import, unused-wildcard-import
from fluster.decoders import *  # noqa: F401,F403

# pylint: enable=wildcard-import, unused-wildcard-import

from fluster.test_suite import TestSuite
from fluster.test_suite import Context as TestSuiteContext
from fluster.decoder import DECODERS, Decoder
from fluster.test_vector import TestVector, TestVectorResult
from fluster.codec import Codec

# pylint: disable=broad-except


class Context:
    """Context for run and reference command"""

    # pylint: disable=too-many-instance-attributes too-many-locals

    def __init__(
        self,
        jobs: int,
        timeout: int,
        test_suites: List[str],
        decoders: List[str],
        test_vectors: List[str],
        skip_vectors: List[str],
        failfast: bool = False,
        quiet: bool = False,
        reference: bool = False,
        summary: bool = False,
        keep_files: bool = False,
        threshold: Optional[int] = None,
        time_threshold: Optional[int] = None,
        verbose: bool = False,
        summary_output: str = "",
        summary_format: str = "",
    ):
        self.jobs = jobs
        self.timeout = timeout
        self.test_suites_names = test_suites
        self.test_suites: List[TestSuite] = []
        self.decoders_names = decoders
        self.decoders: List[Decoder] = []
        self.test_vectors_names = test_vectors
        self.skip_vectors_names = skip_vectors
        self.failfast = failfast
        self.quiet = quiet
        self.reference = reference
        self.summary = summary
        self.keep_files = keep_files
        self.threshold = threshold
        self.time_threshold = time_threshold
        self.verbose = verbose
        self.summary_output = summary_output
        self.summary_format = summary_format

    def to_test_suite_context(
        self,
        decoder: Decoder,
        results_dir: str,
        test_vectors: List[str],
        skip_vectors: List[str],
    ) -> TestSuiteContext:
        """Create a TestSuite's Context from this"""
        ts_context = TestSuiteContext(
            jobs=self.jobs,
            decoder=decoder,
            timeout=self.timeout,
            failfast=self.failfast,
            quiet=self.quiet,
            results_dir=results_dir,
            reference=self.reference,
            test_vectors=test_vectors,
            skip_vectors=skip_vectors,
            keep_files=self.keep_files,
            verbose=self.verbose,
        )
        return ts_context


EMOJI_RESULT = {
    TestVectorResult.NOT_RUN: "",
    TestVectorResult.SUCCESS: "✔️",
    TestVectorResult.FAIL: "❌",
    TestVectorResult.TIMEOUT: "⌛",
    TestVectorResult.ERROR: "☠",
}

TEXT_RESULT = {
    TestVectorResult.NOT_RUN: "",
    TestVectorResult.SUCCESS: "OK",
    TestVectorResult.FAIL: "KO",
    TestVectorResult.TIMEOUT: "TO",
    TestVectorResult.ERROR: "ER",
}


class SummaryFormat(Enum):
    """Summary formats"""

    MARKDOWN = "md"
    CSV = "csv"
    JUNITXML = "junitxml"


class Fluster:
    """Main class for fluster"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        test_suites_dir: str,
        decoders_dir: str,
        resources_dir: str,
        results_dir: str,
        verbose: bool = False,
        use_emoji: bool = True,
    ):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.resources_dir = resources_dir
        self.results_dir = results_dir
        self.verbose = verbose
        self.test_suites: List[TestSuite] = []
        self.decoders = DECODERS
        self.emoji = EMOJI_RESULT if use_emoji else TEXT_RESULT

    @lru_cache(maxsize=128)
    def _load_test_suites(self) -> None:
        for root, _, files in os.walk(self.test_suites_dir):
            for file in files:
                if os.path.splitext(file)[1] == ".json":
                    try:
                        test_suite = TestSuite.from_json_file(
                            os.path.join(root, file), self.resources_dir
                        )
                        if test_suite.name in [ts.name for ts in self.test_suites]:
                            raise Exception(
                                f'Repeated test suite with name "{test_suite.name}"'
                            )
                        self.test_suites.append(test_suite)
                    except Exception as ex:
                        print(f"Error loading test suite {file}: {ex}")

    def list_decoders(self, check: bool, verbose: bool) -> None:
        """List all the available decoders"""
        print("\nList of available decoders:")
        decoders_dict: Dict[Codec, List[Decoder]] = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for codec, decoder_list in decoders_dict.items():
            print(f'\n{str(codec).split(".")[1]}')
            for decoder in decoder_list:
                string = f"{decoder}"
                if check:
                    string += "... " + (
                        self.emoji[TestVectorResult.SUCCESS]
                        if decoder.check(verbose)
                        else self.emoji[TestVectorResult.FAIL]
                    )
                print(string)

    def list_test_suites(
        self,
        show_test_vectors: bool = False,
        test_suites: Optional[List[str]] = None,
    ) -> None:
        """List all test suites"""
        self._load_test_suites()
        print("\nList of available test suites:")
        if test_suites:
            test_suites = [x.lower() for x in test_suites]
        for test_suite in self.test_suites:
            if test_suites:
                if test_suite.name.lower() not in test_suites:
                    continue
            print(test_suite)
            if show_test_vectors:
                for test_vector in test_suite.test_vectors.values():
                    print(test_vector)

    def _get_matches(
        self, in_list: List[str], check_list: List[Any], name: str
    ) -> List[Any]:
        if in_list:
            in_list_names = {x.lower() for x in in_list}
            check_list_names = {x.name.lower() for x in check_list}
            matches = in_list_names & check_list_names
            if len(matches) != len(in_list):
                sys.exit(
                    f'No {name} found for: {", ".join(in_list_names - check_list_names)}'
                )
            matches_ret = [x for x in check_list if x.name.lower() in matches]
        else:
            matches_ret = check_list
        return matches_ret

    def _normalize_context(self, ctx: Context) -> None:
        # Convert all test suites and decoders to lowercase to make the filter greedy
        if ctx.test_suites:
            ctx.test_suites_names = [x.lower() for x in ctx.test_suites_names]
        if ctx.decoders_names:
            ctx.decoders_names = [x.lower() for x in ctx.decoders_names]
        if ctx.test_vectors_names:
            ctx.test_vectors_names = [x.lower() for x in ctx.test_vectors_names]
        if ctx.skip_vectors_names:
            ctx.skip_vectors_names = [x.lower() for x in ctx.skip_vectors_names]
        ctx.test_suites = self._get_matches(
            ctx.test_suites_names, self.test_suites, "test suite"
        )
        ctx.decoders = self._get_matches(ctx.decoders_names, self.decoders, "decoders")

    def run_test_suites(self, ctx: Context) -> None:
        """Run a group of test suites"""
        # pylint: disable=too-many-branches

        self._load_test_suites()
        self._normalize_context(ctx)

        if ctx.reference and (not ctx.decoders or len(ctx.decoders) > 1):
            dec_names = [dec.name for dec in ctx.decoders]
            raise Exception(
                f'Only one decoder can be the reference. Given: {", ".join(dec_names)}'
            )

        if ctx.threshold and len(ctx.test_suites) > 1:
            raise Exception(
                "Threshold for success tests can only be applied running a single test "
                "suite for a single decoder"
            )

        if ctx.reference:
            print("\n=== Reference mode ===\n")

        error = False
        no_test_run = True
        results: Dict[str, List[Tuple[Decoder, TestSuite]]] = {}
        for test_suite in ctx.test_suites:
            test_suite_results: List[Tuple[Decoder, TestSuite]] = []
            for decoder in ctx.decoders:
                if decoder.codec != test_suite.codec:
                    continue
                test_suite_res = test_suite.run(
                    ctx.to_test_suite_context(
                        decoder,
                        self.results_dir,
                        ctx.test_vectors_names,
                        ctx.skip_vectors_names,
                    )
                )

                if test_suite_res:
                    no_test_run = False
                    test_suite_results.append((decoder, test_suite_res))
                    results[test_suite.name] = test_suite_results
                    success = True
                    for test_vector in test_suite_res.test_vectors.values():
                        if test_vector.errors:
                            success = False
                            break

                    if not success:
                        error = True
                        if ctx.failfast:
                            self._show_summary_if_needed(ctx, results)
                            sys.exit(1)

                    if ctx.threshold:
                        if test_suite_res.test_vectors_success < ctx.threshold:
                            self._show_summary_if_needed(ctx, results)
                            print(
                                f"Tests results below threshold: {test_suite_res.test_vectors_success} vs "
                                f"{ctx.threshold}\nReporting error through exit code 2"
                            )
                            sys.exit(2)

                    if ctx.time_threshold:
                        if test_suite_res.time_taken > ctx.time_threshold:
                            self._show_summary_if_needed(ctx, results)
                            print(
                                f"Tests results over time threshold: {test_suite_res.time_taken} vs "
                                f"{ctx.time_threshold}\nReporting error through exit code 3"
                            )
                            sys.exit(3)

        self._show_summary_if_needed(ctx, results)

        if (error and (not ctx.threshold and not ctx.time_threshold)) or no_test_run:
            sys.exit(1)

    def _show_summary_if_needed(
        self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]
    ) -> None:
        if ctx.summary and results:
            if ctx.summary_format == SummaryFormat.JUNITXML.value:
                self._generate_junit_summary(ctx, results)
            elif ctx.summary_format == SummaryFormat.CSV.value:
                self._generate_csv_summary(ctx, results)
            else:
                self._generate_md_summary(ctx, results)

    def _generate_junit_summary(
        self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]
    ) -> None:
        # pylint: disable=import-outside-toplevel

        try:
            import junitparser as junitp  # type: ignore
        except ImportError:
            sys.exit(
                "error: junitparser required to use JUnit format. Please install with pip install junitparser."
            )

        def _parse_vector_errors(vector: TestVector) -> List[junitp.Error]:
            junit_err_map = {
                TestVectorResult.ERROR: junitp.Error,
                TestVectorResult.FAIL: junitp.Failure,
                TestVectorResult.NOT_RUN: junitp.Skipped,
                TestVectorResult.TIMEOUT: junitp.Failure,
            }

            jerrors = []

            for err in vector.errors:
                jerr = junit_err_map[vector.test_result](message=f"FAIL: {err[0]}")
                jerr.text = "\n".join(err[1:])
                jerrors.append(jerr)

            return jerrors

        def _parse_suite_results(
            test_suite_tuple: Tuple[str, List[Tuple[Decoder, TestSuite]]]
        ) -> junitp.TestSuite:
            jsuites = []

            test_suite_name, test_suite_results = test_suite_tuple

            for suite_decoder_res in test_suite_results:
                timeouts = 0

                jsuite = junitp.TestSuite(test_suite_name)
                jsuite.add_property("decoder", suite_decoder_res[0].name)

                for vector in suite_decoder_res[1].test_vectors.values():
                    jcase = junitp.TestCase(vector.name)
                    if vector.test_result == TestVectorResult.NOT_RUN:
                        jcase.result = [junitp.Skipped()]
                    elif vector.test_result not in [
                        TestVectorResult.SUCCESS,
                        TestVectorResult.REFERENCE,
                    ]:
                        jcase.result = _parse_vector_errors(vector)

                    jsuite.add_testcase(jcase)

                    if vector.test_result is TestVectorResult.TIMEOUT and ctx.jobs == 1:
                        timeouts += ctx.timeout

                jsuite.time = round(suite_decoder_res[1].time_taken - timeouts, 3)

                jsuites.append(jsuite)

            return jsuites

        xml = junitp.JUnitXml()

        jsuites = map(_parse_suite_results, results.items())

        for jsuite in [item for sublist in jsuites for item in sublist]:
            xml.add_testsuite(jsuite)

        if ctx.summary_output:
            with open(ctx.summary_output, "w+", encoding="utf-8") as summary_file:
                xml.write(summary_file.name, pretty=True)

    def _generate_csv_summary(
        self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]
    ) -> None:
        # pylint: disable=too-many-locals
        result_map = {
            TestVectorResult.SUCCESS: "Success",
            TestVectorResult.REFERENCE: "Reference",
            TestVectorResult.TIMEOUT: "Timeout",
            TestVectorResult.ERROR: "Error",
            TestVectorResult.FAIL: "Fail",
            TestVectorResult.NOT_RUN: "Not run",
        }
        content: Dict[Any, Any] = defaultdict(lambda: defaultdict(dict))
        max_vectors = 0
        for test_suite, suite_results in results.items():
            for decoder, vectors in suite_results:
                decoder_name = str(decoder.name[: decoder.name.find(":")])
                max_vectors = max(max_vectors, len(vectors.test_vectors.values()))
                for vector in vectors.test_vectors.values():
                    vector_name = str(vector.name)
                    content[str(test_suite)][decoder_name][vector_name] = result_map[
                        vector.test_result
                    ]

        suite_row = []
        decoder_row = []
        field_row = []
        content_rows: List[List[Any]] = [[] for _ in range(max_vectors)]
        for suite in content:
            suite_row.append(str(suite))
            num_decoders = len(content[suite])
            suite_row += ["" for _ in range(num_decoders + (num_decoders - 1))]
            for decoder in content[suite]:
                decoder_row += [str(decoder), ""]
                field_row += ["Vector", "Result"]
                for index, vector in enumerate(content[suite][decoder]):
                    content_rows[index] += [vector, content[suite][decoder][vector]]
                for index in range(len(content[suite][decoder]), max_vectors):
                    content_rows[index] += ["", ""]
        rows = [suite_row, decoder_row, field_row] + content_rows
        if ctx.summary_output:
            with open(ctx.summary_output, mode="w", encoding="utf8") as file:
                file.writelines([",".join(row) + "\n" for row in rows])

    def _generate_md_summary(
        self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]
    ) -> None:
        def _global_stats(
            results: List[Tuple[Decoder, TestSuite]],
            test_suites: List[TestSuite],
            first: bool,
        ) -> str:
            separator = f'\n|-|{"-|" * len(results)}'
            output = separator if not first else ""
            output += "\n|Test|" if not first else "|Test|"
            for decoder, _ in results:
                output += f"{decoder.name}|"
            output += separator if first else ""
            output += "\n|TOTAL|"
            for test_suite in test_suites:
                output += (
                    f"{test_suite.test_vectors_success}/{len(test_suite.test_vectors)}|"
                )
            output += "\n|TOTAL TIME|"
            for test_suite in test_suites:
                # Substract from the total time that took running a test suite on a decoder
                # the timeouts. This is not ideal since we won't be comparing decoding the
                # same number of test vectors, but at least it is much better than comparing
                # total times when timeouts are such a huge part of the global time taken.
                # Note: we only do this when the number of parallel jobs is 1, because
                # whenever there are actual parallel jobs, this gets much more complicated.
                timeouts = (
                    sum(
                        [
                            ctx.timeout
                            for tv in test_suite.test_vectors.values()
                            if tv.test_result == TestVectorResult.TIMEOUT
                        ]
                    )
                    if ctx.jobs == 1
                    else 0
                )
                total_time = test_suite.time_taken - timeouts
                output += f"{total_time:.3f}s|"
            output += separator if first else ""
            return output

        output = ""

        for test_suite_name, test_suite_results in results.items():
            decoders_names = [decoder.name for decoder, _ in test_suite_results]
            test_suites = [res[1] for res in test_suite_results]
            print(
                f'Generating summary for test suite {test_suite_name} and decoders {", ".join(decoders_names)}:\n'
            )
            output += _global_stats(test_suite_results, test_suites, True)
            for test_vector in test_suite_results[0][1].test_vectors.values():
                output += f"\n|{test_vector.name}|"
                for test_suite in test_suites:
                    tvector = test_suite.test_vectors[test_vector.name]
                    output += self.emoji[tvector.test_result] + "|"
            output += _global_stats(test_suite_results, test_suites, False)
            output += "\n\n"
        if ctx.summary_output:
            with open(ctx.summary_output, "w+", encoding="utf-8") as summary_file:
                summary_file.write(output)
        else:
            print(output)

    def download_test_suites(
        self, test_suites: List[str], jobs: int, keep_file: bool, retries: int
    ) -> None:
        """Download a group of test suites"""
        self._load_test_suites()
        if not test_suites:
            download_test_suites = self.test_suites
        else:
            download_test_suites = self._get_matches(
                test_suites, self.test_suites, "test suites"
            )

        for test_suite in download_test_suites:
            test_suite.download(
                jobs,
                self.resources_dir,
                verify=True,
                keep_file=keep_file,
                retries=retries,
            )
