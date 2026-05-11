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

import csv
import json
import os
import os.path
import sys
from enum import Enum
from functools import lru_cache
from shutil import rmtree
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from fluster.codec import Codec, Profile
from fluster.decoder import DECODERS, Decoder

# Import decoders that will auto-register
from fluster.decoders import *  # noqa: F403
from fluster.decoders.av1_aom import AV1AOMDecoder
from fluster.system_info import SystemInfo
from fluster.test_suite import Context as TestSuiteContext
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVector, TestVectorResult


class Context:
    """Context for run and reference command"""

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
        output_dir: str,
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
            output_dir=output_dir,
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
    TestVectorResult.NOT_SUPPORTED: "○",
}

TEXT_RESULT = {
    TestVectorResult.NOT_RUN: "",
    TestVectorResult.SUCCESS: "OK",
    TestVectorResult.FAIL: "KO",
    TestVectorResult.TIMEOUT: "TO",
    TestVectorResult.ERROR: "ER",
    TestVectorResult.NOT_SUPPORTED: "NS",
}

RESULT_MAP = {
    TestVectorResult.SUCCESS: "Success",
    TestVectorResult.REFERENCE: "Reference",
    TestVectorResult.TIMEOUT: "Timeout",
    TestVectorResult.ERROR: "Error",
    TestVectorResult.FAIL: "Fail",
    TestVectorResult.NOT_RUN: "Not run",
    TestVectorResult.NOT_SUPPORTED: "Not supported",
}


class SummaryFormat(Enum):
    """Summary formats"""

    MARKDOWN = "md"
    CSV = "csv"
    JSON = "json"
    JUNITXML = "junitxml"


class Fluster:
    """Main class for fluster"""

    def __init__(
        self,
        test_suites_dir: str,
        decoders_dir: str,
        resources_dir: str,
        output_dir: str,
        verbose: bool = False,
        use_emoji: bool = True,
    ):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.resources_dir = resources_dir
        self.output_dir = output_dir
        self.verbose = verbose
        self.test_suites: List[TestSuite] = []
        self.decoders = DECODERS
        self.emoji = EMOJI_RESULT if use_emoji else TEXT_RESULT
        if self.verbose:
            print(
                f"NOTE: Internal dirs used:\n"
                f" * test_suites_dir: {self.test_suites_dir}\n"
                f" * resources_dir: {self.resources_dir}\n"
                f" * output_dir: {self.output_dir}"
            )

    def _walk_test_suite_dir(self) -> Iterator[Tuple[str, List[str], List[str]]]:
        for test_suite_dir in self.test_suites_dir.split(os.pathsep):
            for root, dirnames, files in os.walk(test_suite_dir):
                yield (root, dirnames, files)

    @lru_cache(maxsize=128)
    def _load_test_suites(self) -> None:
        for root, _, files in self._walk_test_suite_dir():
            for file in files:
                if os.path.splitext(file)[1] == ".json":
                    try:
                        test_suite = TestSuite.from_json_file(os.path.join(root, file), self.resources_dir)
                        if test_suite.name in [ts.name for ts in self.test_suites]:
                            raise Exception(f'Repeated test suite with name "{test_suite.name}"')
                        self.test_suites.append(test_suite)
                    except Exception as ex:
                        print(f"Error loading test suite {file}: {ex}")
        if len(self.test_suites) == 0:
            raise Exception(f'No test suites found in "{self.test_suites_dir}"')

    def list_decoders(self, check: bool, verbose: bool, codec: Optional[Codec] = None) -> None:
        """List all the available decoders"""
        print("\nList of available decoders:")
        decoders_dict: Dict[Codec, List[Decoder]] = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for current_codec, decoder_list in decoders_dict.items():
            if codec and codec != current_codec:
                continue
            print(f"\n{current_codec}")
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
        codec: Optional[Codec] = None,
    ) -> None:
        """List all test suites"""
        self._load_test_suites()
        print("\nList of available test suites:")
        if test_suites:
            test_suites = [x.lower() for x in test_suites]

        for test_suite in self.test_suites:
            if test_suites and test_suite.name.lower() not in test_suites:
                continue
            if codec and test_suite.codec != codec:
                continue
            print(test_suite)
            if show_test_vectors:
                for test_vector in test_suite.test_vectors.values():
                    print(test_vector)
        if len(self.test_suites) == 0:
            print(f'    No test suites found in "{self.test_suites_dir}"')

    @staticmethod
    def _get_matches(in_list: List[str], check_list: List[Any], name: str) -> List[Any]:
        if in_list:
            in_list_names = {x.lower() for x in in_list}
            check_list_names = {x.name.lower() for x in check_list}
            matches = in_list_names & check_list_names
            if len(matches) != len(in_list_names):
                sys.exit(f"No {name} found for: {', '.join(in_list_names - check_list_names)}")
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
            # Workaround to avoid BC break. Delete when next MAJOR version
            ctx.decoders_names = [x[0:-7] if "-gst1.0" in x else x for x in ctx.decoders_names]
        if ctx.test_vectors_names:
            ctx.test_vectors_names = [x.lower() for x in ctx.test_vectors_names]
        if ctx.skip_vectors_names:
            ctx.skip_vectors_names = [x.lower() for x in ctx.skip_vectors_names]
        ctx.test_suites = self._get_matches(ctx.test_suites_names, self.test_suites, "test suite")
        ctx.decoders = self._get_matches(ctx.decoders_names, self.decoders, "decoders")

    def run_test_suites(self, ctx: Context) -> None:
        """Run a group of test suites"""

        self._load_test_suites()
        self._normalize_context(ctx)

        if ctx.reference and (not ctx.decoders or len(ctx.decoders) > 1):
            dec_names = [dec.name for dec in ctx.decoders]
            raise Exception(f"Only one decoder can be the reference. Given: {', '.join(dec_names)}")

        if ctx.threshold and len(ctx.test_suites) > 1:
            raise Exception(
                "Threshold for success tests can only be applied running a single test suite for a single decoder"
            )

        if ctx.reference:
            print("\n=== Reference mode ===\n")

        error = False
        no_test_run = True
        results: Dict[str, List[Tuple[Decoder, TestSuite]]] = {}
        for test_suite in ctx.test_suites:
            test_suite_results: List[Tuple[Decoder, TestSuite]] = []
            for decoder in ctx.decoders:
                if isinstance(decoder, AV1AOMDecoder) and decoder.name == "libaom-AV1":
                    if any(keyword in test_suite.name for keyword in ["CORE", "STRESS"]):
                        decoder.annexb = True
                if decoder.codec != test_suite.codec:
                    continue
                if test_suite.test_method == TestMethod.PIXEL and decoder.is_reference:
                    continue
                test_suite_res = test_suite.run(
                    ctx.to_test_suite_context(
                        decoder,
                        self.output_dir,
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

        if not ctx.keep_files and os.path.isdir(self.output_dir):
            rmtree(self.output_dir)

        if (error and (not ctx.threshold and not ctx.time_threshold)) or no_test_run:
            sys.exit(1)

    def _show_summary_if_needed(self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
        if ctx.summary and results:
            if ctx.summary_format == SummaryFormat.JUNITXML.value:
                self._generate_junit_summary(ctx, results)
            elif ctx.summary_format == SummaryFormat.CSV.value:
                self._generate_csv_summary(ctx, results)
            elif ctx.summary_format == SummaryFormat.JSON.value:
                self._generate_json_summary(ctx, results)
            else:
                self._generate_md_summary(ctx, results)

    @staticmethod
    def _calculate_profile_stats(test_vectors: Dict[str, TestVector]) -> Dict[str, Dict[str, int]]:
        """Calculate profile statistics from test vectors"""
        profile_stats: Dict[str, Dict[str, int]] = {}
        for test_vector in test_vectors.values():
            if test_vector.profile is not None:
                profile_name = test_vector.profile.name
                if profile_name not in profile_stats:
                    profile_stats[profile_name] = {"passed": 0, "total": 0}
                profile_stats[profile_name]["total"] += 1
                if test_vector.test_result == TestVectorResult.SUCCESS:
                    profile_stats[profile_name]["passed"] += 1
        return profile_stats

    @staticmethod
    def _calculate_timeout_adjustment(ctx: Context, test_suite: TestSuite) -> float:
        """Calculate timeout adjustment for test suite timing"""
        if ctx.jobs == 1:
            return sum(
                ctx.timeout for tv in test_suite.test_vectors.values() if tv.test_result == TestVectorResult.TIMEOUT
            )
        return 0.0

    @staticmethod
    def _generate_junit_summary(ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
        try:
            import junitparser as junitp  # type: ignore
        except ImportError:
            sys.exit("error: junitparser required to use JUnit format. Please install with pip install junitparser.")

        system_info = SystemInfo()

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
            test_suite_tuple: Tuple[str, List[Tuple[Decoder, TestSuite]]],
        ) -> junitp.TestSuite:
            jsuites = []

            test_suite_name, test_suite_results = test_suite_tuple

            for suite_decoder_res in test_suite_results:
                timeouts = 0

                jsuite = junitp.TestSuite(test_suite_name)
                jsuite.add_property("decoder", suite_decoder_res[0].name)
                jsuite.add_property("os", f"{system_info.os_name} {system_info.os_version}")
                jsuite.add_property("cpu", system_info.cpu_model)
                jsuite.add_property("gpu", ", ".join(system_info.gpu_info))
                jsuite.add_property("ram", system_info.total_ram)
                for backend, info in system_info.backend_info.items():
                    jsuite.add_property(f"backend_{backend.lower().replace('-', '_')}", info)

                for vector in suite_decoder_res[1].test_vectors.values():
                    jcase = junitp.TestCase(vector.name)
                    if vector.test_result in [TestVectorResult.NOT_RUN, TestVectorResult.NOT_SUPPORTED]:
                        jcase.result = [junitp.Skipped(message=vector.test_result.value)]
                    elif vector.test_result not in [
                        TestVectorResult.SUCCESS,
                        TestVectorResult.REFERENCE,
                    ]:
                        jcase.result = _parse_vector_errors(vector)

                    jcase.time = vector.test_time

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

    def _generate_csv_summary(self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
        """Generate CSV summary with system info and comprehensive test results"""
        system_info = SystemInfo()

        rows: List[List[str]] = [
            ["SYSTEM INFORMATION", "", "", ""],
            ["OS", f"{system_info.os_name} {system_info.os_version}", "", ""],
            ["CPU", system_info.cpu_model, "", ""],
            ["GPU", ", ".join(system_info.gpu_info), "", ""],
            ["RAM", system_info.total_ram, "", ""],
        ]

        if system_info.backend_info:
            rows.extend([[f"Backend-{backend}", info, "", ""] for backend, info in system_info.backend_info.items()])

        rows.extend([["", "", "", ""], ["TEST RESULTS", "", "", ""]])

        for test_suite_name, test_suite_results in results.items():
            rows.extend([["", "", "", ""], [f"Test Suite: {test_suite_name}", "", "", ""]])

            for decoder, test_suite in test_suite_results:
                tv_total = len(test_suite.test_vectors)
                tv_passed = test_suite.test_vectors_success
                tv_not_run = test_suite.test_vectors_not_run
                tv_not_supported = test_suite.test_vectors_not_supported
                tv_failed = tv_total - tv_passed - tv_not_run - tv_not_supported
                timeouts = self._calculate_timeout_adjustment(ctx, test_suite)

                # Start building the decoder summary block
                rows.extend(
                    [
                        ["", "", "", ""],
                        [f"Decoder: {decoder.name}", "", "", ""],
                        ["Total Tests", str(tv_total), "", ""],
                        ["Passed", str(tv_passed), "", ""],
                    ]
                )

                # Conditional rows: Only add if they contain data
                if tv_not_run > 0:
                    rows.append(["Not Run", str(tv_not_run), "", ""])
                if tv_not_supported > 0:
                    rows.append(["Not Supported", str(tv_not_supported), "", ""])

                # Remaining summary items
                rows.extend(
                    [
                        ["Failed\\Error", str(tv_failed), "", ""],
                        ["Total Time (s)", f"{test_suite.time_taken - timeouts:.3f}", "", ""],
                    ]
                )

                profile_stats = self._calculate_profile_stats(test_suite.test_vectors)
                if profile_stats:
                    rows.extend([["", "", "", ""], ["Profile", "Passed", "Total", ""]])
                    rows.extend(
                        [
                            [profile_name, str(stats["passed"]), str(stats["total"]), ""]
                            for profile_name, stats in sorted(profile_stats.items())
                        ]
                    )

                # Detailed Vector Results
                rows.extend([["", "", "", ""], ["Vector Name", "Result", "Time (s)", "Profile"]])

                # Using list comprehension for performance
                rows.extend(
                    [
                        [
                            tv_name,
                            RESULT_MAP[tv.test_result],
                            f"{tv.test_time:.3f}" if tv.test_time else "0",
                            tv.profile.name if tv.profile else "",
                        ]
                        for tv_name, tv in sorted(test_suite.test_vectors.items())
                    ]
                )

        should_show_summary = len(results) > 1 or any(len(res) > 1 for res in results.values())

        if should_show_summary:
            rows.extend([["", "", "", ""], ["GLOBAL SUMMARY", "", "", ""]])

            stats_map: Dict[str, Dict[str, Any]] = {}

            for test_suite_results in results.values():
                for decoder, test_suite in test_suite_results:
                    name = decoder.name
                    if name not in stats_map:
                        stats_map[name] = {
                            "passed": 0,
                            "not_run": 0,
                            "not_supported": 0,
                            "failed_error": 0,
                            "total": 0,
                            "time": 0.0,
                            "profiles": {},
                        }

                    entry: Dict[str, Any] = stats_map[name]
                    ts = test_suite

                    # Update core counts
                    entry["total"] += len(ts.test_vectors)
                    entry["passed"] += ts.test_vectors_success
                    entry["not_run"] += ts.test_vectors_not_run
                    entry["not_supported"] += ts.test_vectors_not_supported

                    # Update time
                    timeouts = self._calculate_timeout_adjustment(ctx, ts)
                    entry["time"] += ts.time_taken - timeouts

                    # Update profiles
                    ts_profiles = self._calculate_profile_stats(ts.test_vectors)
                    for profile_name, profile_data in ts_profiles.items():
                        profile_entry: Dict[str, int] = entry["profiles"].setdefault(
                            profile_name, {"passed": 0, "total": 0}
                        )
                        profile_entry["passed"] += profile_data["passed"]
                        profile_entry["total"] += profile_data["total"]

            for name, data in stats_map.items():
                failed = data["total"] - data["passed"] - data["not_run"] - data["not_supported"]

                rows.extend(
                    [
                        ["", "", "", ""],
                        [f"Decoder: {name}", "", "", ""],
                        ["Total Tests", str(data["total"]), "", ""],
                        ["Passed", str(data["passed"]), "", ""],
                    ]
                )

                if data["not_run"] > 0:
                    rows.append(["Not Run", str(data["not_run"]), "", ""])
                if data["not_supported"] > 0:
                    rows.append(["Not Supported", str(data["not_supported"]), "", ""])

                rows.extend([["Failed\\Error", str(failed), "", ""], ["Total Time (s)", f"{data['time']:.3f}", "", ""]])

                if data["profiles"]:
                    rows.extend([["", "", "", ""], ["Profile", "Passed", "Total", ""]])
                    rows.extend(
                        [
                            [profile_name, str(profile_stats["passed"]), str(profile_stats["total"]), ""]
                            for profile_name, profile_stats in sorted(data["profiles"].items())
                        ]
                    )

        # Use a generator to normalize rows on the fly
        # This ensures exactly 4 columns: (row + 4 empty strings) truncated to 4
        formatted_rows = ((row + [""] * 4)[:4] for row in rows)

        if ctx.summary_output:
            with open(ctx.summary_output, "w", encoding="utf-8", newline="") as file:
                csv.writer(file).writerows(formatted_rows)
        else:
            csv.writer(sys.stdout).writerows(formatted_rows)

    def _generate_json_summary(self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
        """Generate JSON summary report with system information"""
        system_info = SystemInfo()
        test_suites_data: Dict[str, Any] = {}
        global_summary_data: Dict[str, Any] = {}
        json_output = {
            "system_info": system_info.to_dict(),
            "test_suites": test_suites_data,
            "global_summary": global_summary_data,
        }

        global_stats: Dict[str, Dict[str, Any]] = {}

        for test_suite_name, test_suite_results in results.items():
            suite_data: Dict[str, Any] = {"decoders": {}}
            for decoder, test_suite in test_suite_results:
                ts = test_suite
                name = decoder.name
                tv_total = len(ts.test_vectors)
                tv_passed = ts.test_vectors_success
                tv_not_run = ts.test_vectors_not_run
                tv_not_supported = ts.test_vectors_not_supported
                tv_failed = tv_total - tv_passed - tv_not_run - tv_not_supported
                timeouts = self._calculate_timeout_adjustment(ctx, ts)
                time_taken = ts.time_taken - timeouts

                if name not in global_stats:
                    global_stats[name] = {
                        "total_tests": 0,
                        "passed": 0,
                        "not_run": 0,
                        "not_supported": 0,
                        "failed_error": 0,
                        "time": 0.0,
                        "profiles": {},
                    }

                global_entry: Dict[str, Any] = global_stats[name]
                global_entry["total_tests"] += tv_total
                global_entry["passed"] += tv_passed
                global_entry["not_run"] += tv_not_run
                global_entry["not_supported"] += tv_not_supported
                global_entry["failed_error"] += tv_failed
                global_entry["time"] += time_taken

                # Build Decoder Data
                decoder_data: Dict[str, Any] = {
                    "decoder_name": name,
                    "total_tests": tv_total,
                    "passed": tv_passed,
                }

                if tv_not_run > 0:
                    decoder_data["not_run"] = tv_not_run
                if tv_not_supported > 0:
                    decoder_data["not_supported"] = tv_not_supported

                decoder_data["failed_error"] = tv_failed
                decoder_data["total_time"] = round(time_taken, 3)

                # Profile Stats
                profile_stats = self._calculate_profile_stats(ts.test_vectors)
                if profile_stats:
                    decoder_data["profile_stats"] = profile_stats
                    for profile_name, profile_data in profile_stats.items():
                        if profile_name not in global_entry["profiles"]:
                            global_entry["profiles"][profile_name] = {"passed": 0, "total": 0}
                        global_profile_entry: Dict[str, int] = global_entry["profiles"][profile_name]
                        global_profile_entry["passed"] += profile_data["passed"]
                        global_profile_entry["total"] += profile_data["total"]

                # Vector Details
                test_vectors_dict = {}
                for tv_name, tv in ts.test_vectors.items():
                    vector_data = {
                        "result": RESULT_MAP[tv.test_result],
                        "time": round(tv.test_time, 3) if tv.test_time else 0,
                    }
                    if tv.profile:
                        vector_data["profile"] = tv.profile.name

                    test_vectors_dict[tv_name] = vector_data

                decoder_data["vectors"] = test_vectors_dict
                suite_data["decoders"][name] = decoder_data

            test_suites_data[test_suite_name] = suite_data

        # Global Summary
        if len(results) > 1 or any(len(res) > 1 for res in results.values()):
            for name, data in global_stats.items():
                summary_entry: Dict[str, Any] = {
                    "total_tests": data["total_tests"],
                    "passed": data["passed"],
                }

                if data["not_run"] > 0:
                    summary_entry["not_run"] = data["not_run"]
                if data["not_supported"] > 0:
                    summary_entry["not_supported"] = data["not_supported"]

                summary_entry["failed_error"] = data["failed_error"]
                summary_entry["total_time"] = round(data["time"], 3)

                if data["profiles"]:
                    summary_entry["profile_stats"] = data["profiles"]

                global_summary_data[name] = summary_entry
        else:
            del json_output["global_summary"]

        # Output
        if ctx.summary_output:
            with open(ctx.summary_output, "w", encoding="utf-8") as f:
                json.dump(json_output, f, indent=2)
                f.write("\n")
        else:
            print(json.dumps(json_output, indent=2))

    def _generate_md_summary(self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
        system_info = SystemInfo()

        def _global_stats(
            results: List[Tuple[Decoder, TestSuite]],
            test_suites: List[TestSuite],
        ) -> str:
            separator = f"|-|{'-|' * len(results)}"
            output = f"**Test Suite: {test_suites[0].name}**" + "\n\n"
            output += "|Test|"
            for decoder, _ in results:
                output += f"{decoder.name}|"
            output += "\n" + separator

            rows: Dict[str, List[str]] = {
                "PASSED": [],
                "NOT RUN": [],
                "NOT SUPPORTED": [],
                "FAILED\\ERROR": [],
                "TOTAL TIME": [],
            }

            # Flags to track if we need to show these rows
            show_not_run = False
            show_not_supported = False

            for ts in test_suites:
                tv_total = len(ts.test_vectors)
                tv_passed = ts.test_vectors_success
                tv_not_run = ts.test_vectors_not_run
                tv_not_supported = ts.test_vectors_not_supported
                tv_failed = tv_total - tv_passed - tv_not_run - tv_not_supported

                # Track if we ever encounter a non-zero value
                if tv_not_run > 0:
                    show_not_run = True
                if tv_not_supported > 0:
                    show_not_supported = True

                # Store formatted strings for each column
                rows["PASSED"].append(f"{tv_passed}/{tv_total}")
                rows["NOT RUN"].append(f"{tv_not_run}/{tv_total}")
                rows["NOT SUPPORTED"].append(f"{tv_not_supported}/{tv_total}")
                rows["FAILED\\ERROR"].append(f"{tv_failed}/{tv_total}")

                timeouts = self._calculate_timeout_adjustment(ctx, ts)
                # Substract from the total time that took running a test suite on a decoder
                # the timeouts. This is not ideal since we won't be comparing decoding the
                # same number of test vectors, but at least it is much better than comparing
                # total times when timeouts are such a huge part of the global time taken.
                # Note: we only do this when the number of parallel jobs is 1, because
                # whenever there are actual parallel jobs, this gets much more complicated.
                rows["TOTAL TIME"].append(f"{ts.time_taken - timeouts:.3f}s")

            # Define the order and filter which rows to actually include
            labels_to_include = ["PASSED"]
            if show_not_run:
                labels_to_include.append("NOT RUN")
            if show_not_supported:
                labels_to_include.append("NOT SUPPORTED")
            labels_to_include.extend(["FAILED\\ERROR", "TOTAL TIME"])

            # Construct the final string using a join for performance
            output += "".join(f"\n|{label}|{'|'.join(rows[label])}|" for label in labels_to_include)
            return output

        def _profile_stats(
            results: List[Tuple[Decoder, TestSuite]],
        ) -> str:
            separator = f"|-|{'-|' * len(results)}"
            output = ""

            vectors_per_profile = {profile.name: 0 for profile in Profile}
            for test_vector in results[0][1].test_vectors.values():
                if test_vector.profile is not None:
                    vectors_per_profile[test_vector.profile.name] += 1

            vectors_passed_per_profile_per_decoder: Dict[str, Dict[str, int]] = {
                profile.name: {} for profile in Profile if vectors_per_profile[profile.name] != 0
            }

            if vectors_passed_per_profile_per_decoder:
                output = "|Profile|"
                for decoder, _ in results:
                    output += f"{decoder.name}|"
                output += "\n"
                output += separator

            for profile in vectors_passed_per_profile_per_decoder.keys():
                for decoder, _ in results:
                    vectors_passed_per_profile_per_decoder[profile][decoder.name] = 0

            for decoder, test_suite in results:
                for test_vector in test_suite.test_vectors.values():
                    if test_vector.test_result == TestVectorResult.SUCCESS and test_vector.profile is not None:
                        vectors_passed_per_profile_per_decoder[test_vector.profile.name][decoder.name] += 1

            for profile_temp, decoders in vectors_passed_per_profile_per_decoder.items():
                output += "\n|" + str(profile_temp) + "|"
                for decoder_temp in decoders:
                    output += (
                        str(vectors_passed_per_profile_per_decoder[profile_temp][decoder_temp])
                        + "/"
                        + str(vectors_per_profile[profile_temp])
                        + "|"
                    )

            return output

        def _generate_global_summary(results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> str:
            if not results:
                return ""

            all_decoders = []
            decoder_names = set()
            for test_suite_results in results.values():
                for decoder, _ in test_suite_results:
                    if decoder.name not in decoder_names:
                        all_decoders.append(decoder)
                        decoder_names.add(decoder.name)

            decoder_totals = {
                dec.name: {"passed": 0, "not_run": 0, "not_supported": 0, "total": 0} for dec in all_decoders
            }
            decoder_times = {dec.name: 0.0 for dec in all_decoders}
            global_profile_stats: Dict[str, Dict[str, Dict[str, int]]] = {dec.name: {} for dec in all_decoders}

            for test_suite_results in results.values():
                for decoder, test_suite in test_suite_results:
                    totals = decoder_totals[decoder.name]
                    totals["passed"] += test_suite.test_vectors_success
                    totals["not_run"] += test_suite.test_vectors_not_run
                    totals["not_supported"] += test_suite.test_vectors_not_supported
                    totals["total"] += len(test_suite.test_vectors)

                    timeouts = self._calculate_timeout_adjustment(ctx, test_suite)
                    decoder_times[decoder.name] += test_suite.time_taken - timeouts

                    test_suite_profile_stats = self._calculate_profile_stats(test_suite.test_vectors)
                    for profile_name, profile_data in test_suite_profile_stats.items():
                        stats = global_profile_stats[decoder.name].setdefault(profile_name, {"passed": 0, "total": 0})
                        stats["passed"] += profile_data["passed"]
                        stats["total"] += profile_data["total"]

            separator = f"|-|{'-|' * len(all_decoders)}"
            output = "\n# GLOBAL SUMMARY"
            output += "\n|Total Tests|" + "".join(f"{dec.name}|" for dec in all_decoders) + "\n" + separator
            output += "\n|PASSED|" + "".join(
                f"{decoder_totals[dec.name]['passed']}/{decoder_totals[dec.name]['total']}|" for dec in all_decoders
            )
            # Only add NOT RUN if at least one decoder has a 'not_run' count > 0
            if any(decoder_totals[dec.name]["not_run"] > 0 for dec in all_decoders):
                output += "\n|NOT RUN|" + "".join(
                    f"{decoder_totals[dec.name]['not_run']}/{decoder_totals[dec.name]['total']}|"
                    for dec in all_decoders
                )
            # Only add NOT SUPPORTED if at least one decoder has a 'not_supported' count > 0
            if any(decoder_totals[dec.name]["not_supported"] > 0 for dec in all_decoders):
                output += "\n|NOT SUPPORTED|" + "".join(
                    f"{decoder_totals[dec.name]['not_supported']}/{decoder_totals[dec.name]['total']}|"
                    for dec in all_decoders
                )
            fail_error_parts = []
            for dec in all_decoders:
                totals = decoder_totals[dec.name]
                failed = totals["total"] - totals["passed"] - totals["not_run"] - totals["not_supported"]
                fail_error_parts.append(f"{failed}/{totals['total']}|")
            output += "\n|FAILED\\ERROR|" + "".join(fail_error_parts)
            output += "\n|TOTAL TIME|" + "".join(f"{decoder_times[dec.name]:.3f}s|" for dec in all_decoders)

            all_profiles: Set[str] = set()
            for decoder_profiles in global_profile_stats.values():
                all_profiles.update(decoder_profiles.keys())

            if all_profiles:
                output += "\n\n"
                output += "|Profile|" + "".join(f"{dec.name}|" for dec in all_decoders) + "\n" + separator
                for profile in sorted(all_profiles):
                    output += f"\n|{profile}|"
                    for dec in all_decoders:
                        stats = global_profile_stats[dec.name].get(profile, {"passed": 0, "total": 0})
                        output += f"{stats['passed']}/{stats['total']}|"

            return output

        output = system_info.to_markdown()

        for test_suite_name, test_suite_results in results.items():
            decoders_names = [decoder.name for decoder, _ in test_suite_results]
            test_suites = [res[1] for res in test_suite_results]
            print(f"Generating summary for test suite {test_suite_name} and decoders {', '.join(decoders_names)}:\n")
            output += _global_stats(test_suite_results, test_suites)
            output += "\n\n"

            profile_output = _profile_stats(test_suite_results)
            if profile_output:
                output += profile_output + "\n\n"

            separator = f"|-|{'-|' * len(test_suite_results)}"
            output += "|Test|"
            for decoder, _ in test_suite_results:
                output += f"{decoder.name}|"
            output += "\n" + separator
            for test_vector in test_suite_results[0][1].test_vectors.values():
                output += f"\n|{test_vector.name}|"
                for test_suite in test_suites:
                    tvector = test_suite.test_vectors[test_vector.name]
                    output += self.emoji[tvector.test_result] + "|"
            output += "\n\n"

        if len(results.keys()) > 1 or any(len(test_suite_res) > 1 for test_suite_res in results.values()):
            global_summary = _generate_global_summary(results)
            if global_summary:
                output += global_summary + "\n\n"

        if ctx.summary_output:
            with open(ctx.summary_output, "w+", encoding="utf-8") as summary_file:
                summary_file.write(output)
        else:
            print(output)

    def download_test_suites(
        self, test_suites: List[str], jobs: int, keep_file: bool, retries: int, codec_string: Optional[str] = None
    ) -> None:
        """Download a group of test suites"""
        self._load_test_suites()

        # Parse codecs from comma-separated string
        codecs = None
        if codec_string:
            # Split by comma and convert to Codec enum
            codec_strings = [c.strip() for c in codec_string.split(",")]
            codecs = []
            for codec_str in codec_strings:
                if not codec_str:  # Skip empty strings
                    continue
                # Find matching codec (case-insensitive)
                for codec in Codec:
                    if codec.value.lower() == codec_str.lower():
                        codecs.append(codec)
                        break
                else:
                    sys.exit(f"Unknown codec: {codec_str}")

        download_test_suites: List[TestSuite] = []

        if codecs:
            codec_names = {codec.value for codec in codecs}
            download_test_suites = [ts for ts in self.test_suites if ts.codec.value in codec_names]
            if test_suites:
                download_test_suites += self._get_matches(test_suites, self.test_suites, "test suites")
            print(
                f"Test suites for codecs {', '.join(sorted(codec_names))}: {[ts.name for ts in download_test_suites]}"
            )
        else:
            if test_suites:
                download_test_suites = self._get_matches(test_suites, self.test_suites, "test suites")
            else:
                download_test_suites = self.test_suites
            print(f"Test suites: {[ts.name for ts in download_test_suites]}")

        for test_suite in download_test_suites:
            test_suite.download(
                jobs,
                self.resources_dir,
                verify=True,
                keep_file=keep_file,
                retries=retries,
            )
