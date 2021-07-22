# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import os.path
from functools import lru_cache
from typing import List, Dict, Any, Tuple
import sys

# Import decoders that will auto-register
# pylint: disable=wildcard-import, unused-wildcard-import
from fluster.decoders import *  # noqa: F401,F403

# pylint: enable=wildcard-import, unused-wildcard-import

from fluster.test_suite import TestSuite
from fluster.test_suite import Context as TestSuiteContext
from fluster.decoder import DECODERS, Decoder
from fluster.test_vector import TestVectorResult
from fluster.codec import Codec

# pylint: disable=broad-except


class Context:
    """Context for run and reference command"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        jobs: int,
        timeout: int,
        test_suites: List[str],
        decoders: List[str],
        test_vectors: List[str],
        failfast: bool = False,
        quiet: bool = False,
        reference: bool = False,
        summary: bool = False,
        keep_files: bool = False,
        threshold: int = None,
        time_threshold: int = None,
        verbose: bool = False,
        summary_output: str = None,
    ):
        self.jobs = jobs
        self.timeout = timeout
        self.test_suites_names = test_suites
        self.test_suites: List[TestSuite] = []
        self.decoders_names = decoders
        self.decoders: List[Decoder] = []
        self.test_vectors_names = test_vectors
        self.failfast = failfast
        self.quiet = quiet
        self.reference = reference
        self.summary = summary
        self.keep_files = keep_files
        self.threshold = threshold
        self.time_threshold = time_threshold
        self.verbose = verbose
        self.summary_output = summary_output

    def to_test_suite_context(self, decoder, results_dir, test_vectors):
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
            keep_files=self.keep_files,
            verbose=self.verbose,
        )
        return ts_context


EMOJI_RESULT = {
    TestVectorResult.NOT_RUN: "",
    TestVectorResult.SUCCESS: "✔️",
    TestVectorResult.FAILURE: "❌",
    TestVectorResult.TIMEOUT: "⌛",
    TestVectorResult.ERROR: "☠",
}

TEXT_RESULT = {
    TestVectorResult.NOT_RUN: "",
    TestVectorResult.SUCCESS: "OK",
    TestVectorResult.FAILURE: "KO",
    TestVectorResult.TIMEOUT: "TO",
    TestVectorResult.ERROR: "ER",
}


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

    @lru_cache(maxsize=None)
    def _load_test_suites(self):
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

    def list_decoders(self, check: bool, verbose: bool):
        """List all the available decoders"""
        print("\nList of available decoders:")
        decoders_dict: Dict[Codec, List[Decoder]] = {}
        for dec in self.decoders:
            if dec.codec not in decoders_dict:
                decoders_dict[dec.codec] = []
            decoders_dict[dec.codec].append(dec)

        for codec in decoders_dict:
            print(f'\n{str(codec).split(".")[1]}')
            for decoder in decoders_dict[codec]:
                string = f"{decoder}"
                if check:
                    string += "... " + (
                        self.emoji[TestVectorResult.SUCCESS]
                        if decoder.check(verbose)
                        else self.emoji[TestVectorResult.FAILURE]
                    )
                print(string)

    def list_test_suites(
        self, show_test_vectors: bool = False, test_suites: List[str] = None
    ):
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

    def _normalize_context(self, ctx: Context):
        # Convert all test suites and decoders to lowercase to make the filter greedy
        if ctx.test_suites:
            ctx.test_suites_names = [x.lower() for x in ctx.test_suites_names]
        if ctx.decoders_names:
            ctx.decoders_names = [x.lower() for x in ctx.decoders_names]
        if ctx.test_vectors_names:
            ctx.test_vectors_names = [x.lower() for x in ctx.test_vectors_names]
        ctx.test_suites = self._get_matches(
            ctx.test_suites_names, self.test_suites, "test suite"
        )
        ctx.decoders = self._get_matches(ctx.decoders_names, self.decoders, "decoders")

    def run_test_suites(self, ctx: Context):
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
        for test_suite in ctx.test_suites:
            results = []
            for decoder in ctx.decoders:
                if decoder.codec != test_suite.codec:
                    continue
                test_suite_res = test_suite.run(
                    ctx.to_test_suite_context(
                        decoder, self.results_dir, ctx.test_vectors_names
                    )
                )

                if test_suite_res:
                    no_test_run = False
                    results.append((decoder, test_suite_res))
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
        self, ctx: Context, results: List[Tuple[Decoder, TestSuite]]
    ):
        if ctx.summary and results:
            self._generate_summary(ctx, results)

    def _generate_summary(self, ctx: Context, results: List[Tuple[Decoder, TestSuite]]):
        def _global_stats(
            results: List[Tuple[Decoder, TestSuite]],
            test_suites: List[TestSuite],
            first: bool,
        ):
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
            output += separator if first else ""
            return output

        test_suite_name = results[0][1].name
        decoders_names = [decoder.name for decoder, _ in results]
        test_suites = [res[1] for res in results]
        print(
            f'Generating summary for test suite {test_suite_name} and decoders {", ".join(decoders_names)}:\n'
        )

        output = ""
        output += _global_stats(results, test_suites, True)
        for test_vector in results[0][1].test_vectors.values():
            output += f"\n|{test_vector.name}|"
            for test_suite in test_suites:
                tvector = test_suite.test_vectors[test_vector.name]
                output += self.emoji[tvector.test_result] + "|"
        output += _global_stats(results, test_suites, False)
        output += "\n\n"
        if ctx.summary_output:
            with open(ctx.summary_output, "w+", encoding="utf-8") as summary_file:
                summary_file.write(output)
        else:
            print(output)

    def download_test_suites(self, test_suites: List[str], jobs: int, keep_file: bool):
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
                jobs, self.resources_dir, verify=True, keep_file=keep_file
            )
