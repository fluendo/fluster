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

from fluster import utils
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
        resources_dir: str,
        output_dir: str,
        verbose: bool = False,
        use_emoji: bool = True,
    ):
        self.test_suites_dir = test_suites_dir
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
                (tv.test_time for tv in test_suite.test_vectors.values() if tv.test_result == TestVectorResult.TIMEOUT),
                0.0,
            )
        return 0.0

    def _collect_suite_stats(self, ctx: Context, test_suite: TestSuite) -> Dict[str, Any]:
        """Return calculated statistics for a single test suite / decoder pair."""
        total = len(test_suite.test_vectors)
        passed = test_suite.test_vectors_success
        not_run = test_suite.test_vectors_not_run
        not_supported = test_suite.test_vectors_not_supported
        return {
            "total": total,
            "passed": passed,
            "not_run": not_run,
            "not_supported": not_supported,
            "failed": total - passed - not_run - not_supported,
            "time_taken": test_suite.time_taken - self._calculate_timeout_adjustment(ctx, test_suite),
            "profile_stats": self._calculate_profile_stats(test_suite.test_vectors),
        }

    def _collect_global_stats(
        self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Accumulate suite stats across all test suites, grouped by decoder name."""
        global_stats: Dict[str, Dict[str, Any]] = {}
        for test_suite_results in results.values():
            for decoder, test_suite in test_suite_results:
                name = decoder.name
                suite = self._collect_suite_stats(ctx, test_suite)
                if name not in global_stats:
                    global_stats[name] = {
                        "total": 0,
                        "passed": 0,
                        "not_run": 0,
                        "not_supported": 0,
                        "failed": 0,
                        "time_taken": 0.0,
                        "profile_stats": {},
                    }
                entry = global_stats[name]
                for key in ("total", "passed", "not_run", "not_supported", "failed", "time_taken"):
                    entry[key] += suite[key]
                for profile_name, data in suite["profile_stats"].items():
                    p = entry["profile_stats"].setdefault(profile_name, {"passed": 0, "total": 0})
                    p["passed"] += data["passed"]
                    p["total"] += data["total"]
        return global_stats

    def _generate_junit_summary(self, ctx: Context, results: Dict[str, List[Tuple[Decoder, TestSuite]]]) -> None:
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

                timeout_time = self._calculate_timeout_adjustment(ctx, suite_decoder_res[1])

                jsuite.time = round(suite_decoder_res[1].time_taken - timeout_time, 3)

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

        global_stats = self._collect_global_stats(ctx, results)

        for test_suite_name, test_suite_results in results.items():
            rows.extend([["", "", "", ""], [f"Test Suite: {test_suite_name}", "", "", ""]])
            for decoder, test_suite in test_suite_results:
                # Start building the decoder summary block
                suite_stats = self._collect_suite_stats(ctx, test_suite)
                rows.extend(
                    [
                        ["", "", "", ""],
                        [f"Decoder: {decoder.name}", "", "", ""],
                        ["Total Tests", str(suite_stats["total"]), "", ""],
                        ["Passed", str(suite_stats["passed"]), "", ""],
                    ]
                )
                # Conditional rows: Only add if they contain data
                if suite_stats["not_run"] > 0:
                    rows.append(["Not Run", str(suite_stats["not_run"]), "", ""])
                if suite_stats["not_supported"] > 0:
                    rows.append(["Not Supported", str(suite_stats["not_supported"]), "", ""])
                # Remaining summary items
                rows.extend(
                    [
                        ["Failed\\Error", str(suite_stats["failed"]), "", ""],
                        ["Total Time (s)", f"{suite_stats['time_taken']:.3f}", "", ""],
                    ]
                )
                if suite_stats["profile_stats"]:
                    rows.extend([["", "", "", ""], ["Profile", "Passed", "Total", ""]])
                    rows.extend(
                        [
                            [profile_name, str(profile_stats["passed"]), str(profile_stats["total"]), ""]
                            for profile_name, profile_stats in sorted(suite_stats["profile_stats"].items())
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

        if len(results) > 1 or any(len(res) > 1 for res in results.values()):
            rows.extend([["", "", "", ""], ["GLOBAL SUMMARY", "", "", ""]])
            for decoder_name, decoder_stats in global_stats.items():
                rows.extend(
                    [
                        ["", "", "", ""],
                        [f"Decoder: {decoder_name}", "", "", ""],
                        ["Total Tests", str(decoder_stats["total"]), "", ""],
                        ["Passed", str(decoder_stats["passed"]), "", ""],
                    ]
                )
                if decoder_stats["not_run"] > 0:
                    rows.append(["Not Run", str(decoder_stats["not_run"]), "", ""])
                if decoder_stats["not_supported"] > 0:
                    rows.append(["Not Supported", str(decoder_stats["not_supported"]), "", ""])
                rows.extend(
                    [
                        ["Failed\\Error", str(decoder_stats["failed"]), "", ""],
                        ["Total Time (s)", f"{decoder_stats['time_taken']:.3f}", "", ""],
                    ]
                )
                if decoder_stats["profile_stats"]:
                    rows.extend([["", "", "", ""], ["Profile", "Passed", "Total", ""]])
                    rows.extend(
                        [
                            [profile_name, str(profile_stats["passed"]), str(profile_stats["total"]), ""]
                            for profile_name, profile_stats in sorted(decoder_stats["profile_stats"].items())
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

        global_stats = self._collect_global_stats(ctx, results)

        for test_suite_name, test_suite_results in results.items():
            suite_data: Dict[str, Any] = {"decoders": {}}
            for decoder, test_suite in test_suite_results:
                name = decoder.name
                suite_stats = self._collect_suite_stats(ctx, test_suite)
                # Build Decoder Data
                decoder_data: Dict[str, Any] = {
                    "decoder_name": name,
                    "total_tests": suite_stats["total"],
                    "passed": suite_stats["passed"],
                }
                # Track if we ever encounter a non-zero value
                if suite_stats["not_run"] > 0:
                    decoder_data["not_run"] = suite_stats["not_run"]
                if suite_stats["not_supported"] > 0:
                    decoder_data["not_supported"] = suite_stats["not_supported"]
                decoder_data["failed_error"] = suite_stats["failed"]
                decoder_data["total_time"] = round(suite_stats["time_taken"], 3)
                if suite_stats["profile_stats"]:
                    decoder_data["profile_stats"] = suite_stats["profile_stats"]
                # Vector Details
                test_vectors_dict = {}
                for tv_name, tv in test_suite.test_vectors.items():
                    vector_data: Dict[str, Any] = {
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
            for decoder_name, decoder_stats in global_stats.items():
                summary_entry: Dict[str, Any] = {
                    "total_tests": decoder_stats["total"],
                    "passed": decoder_stats["passed"],
                }
                if decoder_stats["not_run"] > 0:
                    summary_entry["not_run"] = decoder_stats["not_run"]
                if decoder_stats["not_supported"] > 0:
                    summary_entry["not_supported"] = decoder_stats["not_supported"]
                summary_entry["failed_error"] = decoder_stats["failed"]
                summary_entry["total_time"] = round(decoder_stats["time_taken"], 3)
                if decoder_stats["profile_stats"]:
                    summary_entry["profile_stats"] = decoder_stats["profile_stats"]
                global_summary_data[decoder_name] = summary_entry
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
                suite_stats = self._collect_suite_stats(ctx, ts)
                if suite_stats["not_run"] > 0:
                    show_not_run = True
                if suite_stats["not_supported"] > 0:
                    show_not_supported = True
                rows["PASSED"].append(f"{suite_stats['passed']}/{suite_stats['total']}")
                rows["NOT RUN"].append(f"{suite_stats['not_run']}/{suite_stats['total']}")
                rows["NOT SUPPORTED"].append(f"{suite_stats['not_supported']}/{suite_stats['total']}")
                rows["FAILED\\ERROR"].append(f"{suite_stats['failed']}/{suite_stats['total']}")
                rows["TOTAL TIME"].append(f"{suite_stats['time_taken']:.3f}s")

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
            decoder_names: Set[str] = set()
            for test_suite_results in results.values():
                for decoder, _ in test_suite_results:
                    if decoder.name not in decoder_names:
                        all_decoders.append(decoder)
                        decoder_names.add(decoder.name)

            global_stats = self._collect_global_stats(ctx, results)

            separator = f"|-|{'-|' * len(all_decoders)}"
            output = "\n# GLOBAL SUMMARY"
            output += "\n|Total Tests|" + "".join(f"{dec.name}|" for dec in all_decoders) + "\n" + separator
            output += "\n|PASSED|" + "".join(
                f"{global_stats[dec.name]['passed']}/{global_stats[dec.name]['total']}|" for dec in all_decoders
            )
            # Only add NOT RUN if at least one decoder has a 'not_run' count > 0
            if any(global_stats[dec.name]["not_run"] > 0 for dec in all_decoders):
                output += "\n|NOT RUN|" + "".join(
                    f"{global_stats[dec.name]['not_run']}/{global_stats[dec.name]['total']}|" for dec in all_decoders
                )
            # Only add NOT SUPPORTED if at least one decoder has a 'not_supported' count > 0
            if any(global_stats[dec.name]["not_supported"] > 0 for dec in all_decoders):
                output += "\n|NOT SUPPORTED|" + "".join(
                    f"{global_stats[dec.name]['not_supported']}/{global_stats[dec.name]['total']}|"
                    for dec in all_decoders
                )
            output += "\n|FAILED\\ERROR|" + "".join(
                f"{global_stats[dec.name]['failed']}/{global_stats[dec.name]['total']}|" for dec in all_decoders
            )
            output += "\n|TOTAL TIME|" + "".join(
                f"{global_stats[dec.name]['time_taken']:.3f}s|" for dec in all_decoders
            )

            all_profiles: Set[str] = set()
            for decoder_stats in global_stats.values():
                all_profiles.update(decoder_stats["profile_stats"].keys())

            if all_profiles:
                output += "\n\n"
                output += "|Profile|" + "".join(f"{dec.name}|" for dec in all_decoders) + "\n" + separator
                for profile in sorted(all_profiles):
                    output += f"\n|{profile}|"
                    for dec in all_decoders:
                        profile_stats = global_stats[dec.name]["profile_stats"].get(profile, {"passed": 0, "total": 0})
                        output += f"{profile_stats['passed']}/{profile_stats['total']}|"

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

        if not download_test_suites:
            print("No test suites to download.")
            return

        cache_dir = os.path.join(self.resources_dir, ".cache")
        with utils.DownloadManager(
            cache_dir=cache_dir, verify=True, keep_file=keep_file, retries=retries, max_pool_workers=jobs
        ) as manager:
            # Phase 1: collect every (url, checksum) across all selected suites,
            # deduplicated. Different suites can share a URL (e.g. AV1-ARGON
            # archive).
            url_checksums: Dict[str, str] = {}
            checksum_conflicts: List[Tuple[str, str, str]] = []
            for ts in download_test_suites:
                for tv in ts.test_vectors.values():
                    existing = url_checksums.get(tv.source)
                    if existing is None or existing == "__skip__":
                        # Prefer a real checksum over an unset/__skip__ one.
                        url_checksums[tv.source] = tv.source_checksum
                    elif tv.source_checksum not in (existing, "__skip__"):
                        checksum_conflicts.append((tv.source, existing, tv.source_checksum))
            if checksum_conflicts:
                for src, kept, other in checksum_conflicts:
                    print(
                        f"ERROR: conflicting checksums for {src}: "
                        f"{kept} vs {other} — the test-suite definitions disagree."
                    )
                sys.exit(
                    f"{len(checksum_conflicts)} URL(s) have conflicting checksums across "
                    f"selected suites; refusing to download (fix the test-suite JSON)."
                )

            # Phase 2: parallel pre-download via the manager's persistent pool.
            # The manager owns the fan-out and the BoundedSemaphore that caps
            # actual HTTP concurrency. get_many() returns per-URL errors instead
            # of raising so we can skip only the affected suites below.
            if url_checksums:
                print(
                    f"Pre-downloading {len(url_checksums)} unique source(s) across {len(download_test_suites)} suite(s)"
                )
                _successes, pre_errors = manager.get_many(url_checksums)
                if pre_errors:
                    failed_urls = {err_url for err_url, _ in pre_errors}
                    for err_url, err_exc in pre_errors:
                        print(f"Error pre-downloading {err_url}: {type(err_exc).__name__}: {err_exc}")
                    print(f"{len(pre_errors)} URL(s) failed to pre-download — skipping affected suites.")
                else:
                    failed_urls = set()
            else:
                failed_urls = set()

            # Phase 3: extract per suite. Cache is now warm — TestSuite.download
            # hits manager.get() which short-circuits to the cached path.
            # Suites whose URLs intersect with failed_urls are skipped so the
            # rest of the batch still extracts.
            skipped_suites: List[str] = []
            failed_extractions: List[str] = []
            for test_suite in download_test_suites:
                suite_urls = {tv.source for tv in test_suite.test_vectors.values()}
                if suite_urls & failed_urls:
                    skipped_suites.append(test_suite.name)
                    continue
                try:
                    test_suite.download(
                        jobs,
                        self.resources_dir,
                        download_manager=manager,
                    )
                except utils.BadArchiveError as exc:
                    # The cache entry was already invalidated inside download();
                    # report cleanly and keep going so the rest of the batch
                    # still extracts.
                    print(f"\n{test_suite.name}: {exc}")
                    failed_extractions.append(test_suite.name)
            if skipped_suites:
                print(f"\nSkipped {len(skipped_suites)} suite(s) due to pre-download failures: {skipped_suites}")
            if failed_extractions:
                print(f"Corrupt archive(s) invalidated for: {failed_extractions} (re-run to retry)")
            if skipped_suites or failed_extractions:
                sys.exit(1)
