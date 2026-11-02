#!/usr/bin/env python3

# GStreamer Parser - testing framework for GStreamer parsers
# Copyright (C) 2026, Fluendo, S.A.
#  Author: Ruben Gonzalez Gonzalez <rgonzalez@fluendo.com>, Fluendo, S.A.
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

"""Standalone test runner for GStreamer parsers."""

from __future__ import annotations

import subprocess
from functools import lru_cache, partial
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import fluster.main as fluster_main
import fluster.test_suite as fluster_test_suite
from fluster.codec import Codec, Profile
from fluster.fluster import Fluster
from fluster.gstreamer import run_pipeline
from fluster.decoders.gstreamer import gst_element_exists

from fluster.test import Test
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVectorResult
from fluster.utils import normalize_binary_cmd

PARSER_PIPELINE_TPL = "filesrc location={} ! {} ! fakesink"
PARSER_PROFILE_PIPELINE_TPL = "filesrc location={} ! {} ! {},profile={} ! fakesink"
CAPS_NAME = {
    Codec.H264: "video/x-h264",
    Codec.H265: "video/x-h265",
    Codec.H266: "video/x-h266",
}


def profile_to_gst(profile: Profile, codec: Codec) -> str:
    """Convert a Fluster profile to the matching GStreamer caps profile."""
    value = str(profile.value).lower().replace(" ", "-")
    if codec == Codec.H266:
        value = value.replace("4:4:4", "444")
    if codec == Codec.H264 and value == "high-4:4:4-predictive":
        value = "high-4:4:4"
    return value


PARSERS: Dict[Codec, List[str]] = {
    Codec.H264: ["h264parse", "rsh264parse"],
    Codec.H265: ["h265parse"],
    Codec.H266: ["h266parse"],
}


def build_pipeline(
    codec: Codec,
    element: str,
    input_filepath: str,
    profile: Optional[Profile] = None,
) -> str:
    """Generate the GStreamer pipeline used to parse a test vector."""
    caps_name = CAPS_NAME.get(codec)
    if profile is not None and caps_name:
        return PARSER_PROFILE_PIPELINE_TPL.format(
            input_filepath,
            element,
            caps_name,
            profile_to_gst(profile, codec),
        )
    return PARSER_PIPELINE_TPL.format(input_filepath, element)


def check_parser(element: str, verbose: bool) -> bool:
    """Check if the GStreamer parser element is available."""
    exists = gst_element_exists(element)
    if verbose and not exists:
        print(f"GStreamer element {element} can't be found to be executed")
    return exists


def parse_element(
    codec: Codec,
    element: str,
    input_filepath: str,
    timeout: int,
    verbose: bool,
    profile: Optional[Profile] = None,
) -> str:
    """Parse a test vector and check that the pipeline completes."""
    run_pipeline(build_pipeline(codec, element, input_filepath, profile), timeout=timeout, verbose=verbose)
    return ""


def make_parser(codec: Codec, element: str) -> SimpleNamespace:
    """Create the tool object used by Fluster's generic test runner."""
    return SimpleNamespace(
        name=element,
        codec=codec,
        is_reference=False,
        is_parser=True,
        check=partial(check_parser, element),
        parse=partial(parse_element, codec, element),
    )


def make_parsers() -> List[SimpleNamespace]:
    """Create the parser tools for every configured codec."""
    return [make_parser(codec, element) for codec, elements in PARSERS.items() for element in elements]


class GstParserTest(Test):
    """Test class for parsers.

    Parsers do not produce a decoded output that can be compared against a
    result, so a test vector passes when the parser pipeline completes without
    errors.
    """

    def _execute_decode(self) -> str:
        """Execute the parser and return the result."""
        return self.decoder.parse(
            self.input_filepath,
            self.timeout,
            self.verbose,
            self.test_vector.profile,
        )

    def compare_result(self, result: str) -> None:
        """Parsers have no expected output to compare."""


_ORIGINAL_GENERATE_TESTS = TestSuite.generate_tests


def _generate_parser_tests(self: TestSuite, ctx: Any) -> List[Test]:
    """Generate parser tests, delegating non-parser runs to Fluster."""
    if not getattr(ctx.decoder, "is_parser", False):
        return _ORIGINAL_GENERATE_TESTS(self, ctx)

    original_test_cls = fluster_test_suite.MD5ComparisonTest
    fluster_test_suite.MD5ComparisonTest = GstParserTest
    try:
        return _ORIGINAL_GENERATE_TESTS(self, ctx)
    finally:
        fluster_test_suite.MD5ComparisonTest = original_test_cls


TestSuite.generate_tests = _generate_parser_tests


def prepare_parser_fluster(fluster: Fluster) -> None:
    """Configure a Fluster instance for parser runs."""
    fluster.decoders = make_parsers()
    fluster._load_test_suites()  # noqa: SLF001
    for test_suite in fluster.test_suites:
        test_suite.test_method = TestMethod.MD5
        test_suite.negative_test = False


def list_parsers(fluster: Fluster, check: bool, verbose: bool, codec: Optional[Codec] = None) -> None:
    """List all the available parsers."""
    print("\nList of available parsers:")
    for current_codec, elements in PARSERS.items():
        if codec and codec != current_codec:
            continue
        print(f"\n{current_codec}")
        for element in elements:
            string = f"    {element}: GStreamer {current_codec.value} parser"
            if check:
                string += "... " + (
                    fluster.emoji[TestVectorResult.SUCCESS]
                    if check_parser(element, verbose)
                    else fluster.emoji[TestVectorResult.FAIL]
                )
            print(string)


class ParserFluster(Fluster):
    """Fluster instance prepared to run parsers as its decoders."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        prepare_parser_fluster(self)


fluster_main.Fluster = ParserFluster


class Main(fluster_main.Main):
    """gstparser CLI, reusing Fluster's main plumbing."""

    def _add_download_cmd(self, subparsers: Any) -> None:
        """gstparser does not provide a download command."""

    def _add_reference_cmd(self, subparsers: Any) -> None:
        """gstparser does not provide a reference command."""

    @staticmethod
    def _list_cmd(args: Any, fluster: Fluster) -> None:
        fluster.list_test_suites(show_test_vectors=args.testvectors, test_suites=args.testsuites, codec=args.codec)
        list_parsers(fluster, check=args.check, verbose=args.verbose, codec=args.codec)


def gstparser_main() -> None:
    """Entrypoint for the application."""
    main = Main()
    main.run()


if __name__ == "__main__":
    gstparser_main()
