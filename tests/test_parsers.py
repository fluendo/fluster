# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
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

"""Unit tests for the GStreamer parsers.

These tests do not require GStreamer to be installed: the parser pipeline
runner and element checks are mocked.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from typing import Optional
from unittest import mock

from fluster import test as fluster_test
from fluster.codec import Codec, OutputFormat, Profile
from fluster.decoder import NotSupportedError
from fluster.fluster import Context, Fluster
from fluster.parsers.base import PARSERS
from fluster.parsers.gstreamer import H264Parse, H265Parse, H266Parse, profile_to_gst
from fluster.test_suite import Context as TestSuiteContext
from fluster.test_suite import TestMethod, TestSuite
from fluster.test_vector import TestVector, TestVectorResult


class TestParserRegistry(unittest.TestCase):
    def test_registered_parsers(self) -> None:
        names = [parser.name for parser in PARSERS]
        self.assertEqual(names, ["h264parse", "h265parse", "h266parse"])

    def test_parsers_have_their_codec(self) -> None:
        parsers = {parser.name: parser for parser in PARSERS}
        self.assertEqual(parsers["h264parse"].codec, Codec.H264)
        self.assertEqual(parsers["h265parse"].codec, Codec.H265)
        self.assertEqual(parsers["h266parse"].codec, Codec.H266)

    def test_parsers_are_marked_as_parsers(self) -> None:
        for parser in PARSERS:
            with self.subTest(parser=parser.name):
                self.assertTrue(parser.is_parser)
                self.assertFalse(parser.is_reference)


class TestParserPipeline(unittest.TestCase):
    def test_pipeline_for_each_parser(self) -> None:
        cases = [
            (H264Parse(), "/tmp/vector.264", "filesrc location=/tmp/vector.264 ! h264parse ! fakesink"),
            (H265Parse(), "/tmp/vector.265", "filesrc location=/tmp/vector.265 ! h265parse ! fakesink"),
            (H266Parse(), "/tmp/vector.266", "filesrc location=/tmp/vector.266 ! h266parse ! fakesink"),
        ]
        for parser, input_file, pipeline in cases:
            with self.subTest(parser=parser.name):
                self.assertEqual(parser.gen_pipeline(input_file), pipeline)

    def test_profile_to_gst(self) -> None:
        cases = [
            (Codec.H264, Profile.CONSTRAINED_BASELINE, "constrained-baseline"),
            (Codec.H264, Profile.MAIN, "main"),
            (Codec.H264, Profile.HIGH_10, "high-10"),
            (Codec.H264, Profile.HIGH_4_4_4_PREDICTIVE, "high-4:4:4"),
            (Codec.H265, Profile.MAIN_10, "main-10"),
            (Codec.H265, Profile.MAIN_STILL_PICTURE, "main-still-picture"),
            (Codec.H266, Profile.MAIN_10, "main-10"),
            (Codec.H266, Profile.MAIN_10_4_4_4, "main-10-444"),
            (Codec.H266, Profile.MULTILAYER_MAIN_10_4_4_4, "multilayer-main-10-444"),
            (Codec.H266, Profile.MAIN_10_4_4_4_STILL_PICTURE, "main-10-444-still-picture"),
        ]
        for codec, profile, expected in cases:
            with self.subTest(codec=codec, profile=profile.value):
                self.assertEqual(profile_to_gst(profile, codec), expected)

    def test_pipeline_with_profile(self) -> None:
        self.assertEqual(
            H265Parse().gen_pipeline("/tmp/vector.265", Profile.MAIN),
            "filesrc location=/tmp/vector.265 ! h265parse ! video/x-h265,profile=main ! fakesink",
        )
        self.assertEqual(
            H266Parse().gen_pipeline("/tmp/vector.266", Profile.MAIN_10_4_4_4),
            "filesrc location=/tmp/vector.266 ! h266parse ! video/x-h266,profile=main-10-444 ! fakesink",
        )

    def test_parse_runs_pipeline(self) -> None:
        parser = H264Parse()
        with mock.patch("fluster.parsers.gstreamer.run_pipeline") as run_pipeline_mock:
            result = parser.parse("/tmp/vector.264", timeout=20, verbose=True)

        self.assertEqual(result, "")
        run_pipeline_mock.assert_called_once_with(
            "filesrc location=/tmp/vector.264 ! h264parse ! fakesink",
            timeout=20,
            verbose=True,
        )

    def test_parse_runs_pipeline_with_profile(self) -> None:
        parser = H265Parse()
        with mock.patch("fluster.parsers.gstreamer.run_pipeline") as run_pipeline_mock:
            result = parser.parse("/tmp/vector.265", timeout=20, verbose=True, profile=Profile.MAIN)

        self.assertEqual(result, "")
        run_pipeline_mock.assert_called_once_with(
            "filesrc location=/tmp/vector.265 ! h265parse ! video/x-h265,profile=main ! fakesink",
            timeout=20,
            verbose=True,
        )

    def test_parse_propagates_not_supported(self) -> None:
        parser = H264Parse()
        with mock.patch("fluster.parsers.gstreamer.run_pipeline", side_effect=NotSupportedError("unsupported")):
            with self.assertRaises(NotSupportedError):
                parser.parse("/tmp/vector.264", timeout=20, verbose=False)

    def test_parse_propagates_pipeline_errors(self) -> None:
        parser = H264Parse()
        with mock.patch(
            "fluster.parsers.gstreamer.run_pipeline",
            side_effect=subprocess.CalledProcessError(1, "runner"),
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                parser.parse("/tmp/vector.264", timeout=20, verbose=False)

    def test_check_uses_gst_element_exists(self) -> None:
        parser = H266Parse()
        with mock.patch("fluster.parsers.gstreamer.gst_element_exists", return_value=True) as exists_mock:
            self.assertTrue(parser.check(verbose=False))
        exists_mock.assert_called_once_with("h266parse")

        parser.check.cache_clear()
        with mock.patch("fluster.parsers.gstreamer.gst_element_exists", return_value=False):
            self.assertFalse(parser.check(verbose=False))


class TestParserExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.vector = TestVector(
            name="one",
            source="",
            source_checksum="",
            input_file="one.264",
            output_format=OutputFormat.YUV420P,
            result="",
        )
        self.test_suite = TestSuite(
            filename="",
            resources_dir=self.tmpdir,
            name="H264-min",
            codec=Codec.H264,
            description="",
            test_vectors={"one": self.vector},
        )

    def _make_test(self, parser: H264Parse, test_method: TestMethod = TestMethod.MD5) -> fluster_test.ParserTest:
        self.test_suite.test_method = test_method
        ctx = TestSuiteContext(
            jobs=1,
            decoder=parser,
            timeout=10,
            failfast=False,
            quiet=True,
            output_dir=self.tmpdir,
        )
        tests = self.test_suite.generate_tests(ctx)
        self.assertEqual(len(tests), 1)
        self.assertIsInstance(tests[0], fluster_test.ParserTest)
        return tests[0]

    def test_parser_success_does_not_compare_output(self) -> None:
        parser = H264Parse()
        self.vector.profile = Profile.MAIN
        with mock.patch.object(parser, "parse", return_value="") as parse_mock:
            test = self._make_test(parser)
            getattr(test, "one")()
        parse_mock.assert_called_once()
        self.assertEqual(parse_mock.call_args.args[3], Profile.MAIN)
        self.assertEqual(self.vector.test_result, TestVectorResult.SUCCESS)

    def test_parser_works_with_pixel_test_method_without_reference_decoder(self) -> None:
        parser = H264Parse()
        ctx = TestSuiteContext(
            jobs=1,
            decoder=parser,
            timeout=10,
            failfast=False,
            quiet=True,
            output_dir=self.tmpdir,
        )
        self.test_suite.test_method = TestMethod.PIXEL
        tests = self.test_suite.generate_tests(ctx)
        self.assertIsInstance(tests[0], fluster_test.ParserTest)
        self.assertIsNone(ctx.reference_decoder)


class TestParserSelection(unittest.TestCase):
    def setUp(self) -> None:
        self.fluster = Fluster(test_suites_dir="", resources_dir="", output_dir="")

    def test_parse_mode_selects_all_parsers_by_default(self) -> None:
        ctx = Context(
            jobs=1,
            timeout=10,
            test_suites=[],
            decoders=[],
            parsers=None,
            parse_mode=True,
            test_vectors=[],
            skip_vectors=[],
        )
        self.fluster._normalize_context(ctx)  # noqa: SLF001
        self.assertEqual([parser.name for parser in ctx.parsers], ["h264parse", "h265parse", "h266parse"])

    def test_parse_mode_matches_parser_name(self) -> None:
        ctx = Context(
            jobs=1,
            timeout=10,
            test_suites=[],
            decoders=[],
            parsers=["H266PARSE"],
            parse_mode=True,
            test_vectors=[],
            skip_vectors=[],
        )
        self.fluster._normalize_context(ctx)  # noqa: SLF001
        self.assertEqual([parser.name for parser in ctx.parsers], ["h266parse"])

    def test_unknown_parser_exits(self) -> None:
        ctx = Context(
            jobs=1,
            timeout=10,
            test_suites=[],
            decoders=[],
            parsers=["not-a-parser"],
            parse_mode=True,
            test_vectors=[],
            skip_vectors=[],
        )
        with self.assertRaises(SystemExit):
            self.fluster._normalize_context(ctx)  # noqa: SLF001


class TestListParsers(unittest.TestCase):
    def setUp(self) -> None:
        self.fluster = Fluster(test_suites_dir="", resources_dir="", output_dir="")

    def _list(self, codec: Optional[Codec] = None, check: bool = False) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            self.fluster.list_parsers(check=check, verbose=False, codec=codec)
        return output.getvalue()

    def test_list_contains_parser_section(self) -> None:
        output = self._list()
        self.assertIn("List of available parsers:", output)
        for name in ["h264parse", "h265parse", "h266parse"]:
            self.assertIn(name, output)

    def test_list_filters_by_codec(self) -> None:
        output = self._list(codec=Codec.H266)
        self.assertIn("h266parse", output)
        self.assertNotIn("h264parse", output)
        self.assertNotIn("h265parse", output)

    def test_list_check_uses_parser_check(self) -> None:
        with mock.patch("fluster.parsers.gstreamer.GStreamerParser.check", return_value=True):
            output = self._list(check=True)
        self.assertEqual(output.count("✔️"), 3)


if __name__ == "__main__":
    unittest.main()
