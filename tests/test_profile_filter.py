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

from __future__ import annotations

import unittest
from typing import Optional, Set

from fluster.codec import Codec, OutputFormat, Profile
from fluster.decoders.dummy import Dummy
from fluster.fluster import Fluster
from fluster.test_suite import Context, TestMethod, TestSuite
from fluster.test_vector import TestVector


def _make_suite() -> TestSuite:
    test_vectors = {
        "baseline-a": TestVector("baseline-a", "", "", "a.bit", OutputFormat.YUV420P, "", Profile.BASELINE),
        "main-a": TestVector("main-a", "", "", "b.bit", OutputFormat.YUV420P, "", Profile.MAIN),
        "high-a": TestVector("high-a", "", "", "d.bit", OutputFormat.YUV420P, "", Profile.HIGH),
        "no-profile": TestVector("no-profile", "", "", "c.bit", OutputFormat.YUV420P, ""),
    }
    return TestSuite(
        "dummy.json",
        "/tmp/fluster-profile-test",
        "dummy",
        Codec.DUMMY,
        "Dummy test suite",
        test_vectors,
        test_method=TestMethod.MD5,
    )


def _make_context(
    profiles: Optional[Set[Profile]] = None,
    skip_profiles: Optional[Set[Profile]] = None,
) -> Context:
    return Context(
        jobs=1,
        decoder=Dummy(),
        timeout=30,
        failfast=False,
        quiet=True,
        output_dir="/tmp/fluster-profile-test",
        test_vectors=None,
        skip_vectors=None,
        profiles=profiles,
        skip_profiles=skip_profiles,
    )


def _run_generate_tests(
    profiles: Optional[Set[Profile]] = None,
    skip_profiles: Optional[Set[Profile]] = None,
) -> Set[str]:
    suite = _make_suite()
    tests = suite.generate_tests(_make_context(profiles=profiles, skip_profiles=skip_profiles))
    return {test.test_vector.name for test in tests}


class TestProfileFilter(unittest.TestCase):
    def test_no_filter_runs_all_vectors(self) -> None:
        self.assertEqual(_run_generate_tests(), {"baseline-a", "main-a", "high-a", "no-profile"})

    def test_include_single_profile(self) -> None:
        self.assertEqual(_run_generate_tests(profiles={Profile.BASELINE}), {"baseline-a"})

    def test_include_multiple_profiles_is_or(self) -> None:
        self.assertEqual(_run_generate_tests(profiles={Profile.BASELINE, Profile.MAIN}), {"baseline-a", "main-a"})

    def test_include_excludes_vectors_without_profile(self) -> None:
        self.assertNotIn("no-profile", _run_generate_tests(profiles={Profile.BASELINE, Profile.MAIN, Profile.HIGH}))

    def test_skip_single_profile(self) -> None:
        self.assertEqual(_run_generate_tests(skip_profiles={Profile.MAIN}), {"baseline-a", "high-a", "no-profile"})

    def test_skip_keeps_vectors_without_profile(self) -> None:
        self.assertIn("no-profile", _run_generate_tests(skip_profiles={Profile.MAIN}))

    def test_skip_multiple_profiles(self) -> None:
        self.assertEqual(_run_generate_tests(skip_profiles={Profile.MAIN, Profile.HIGH}), {"baseline-a", "no-profile"})

    def test_skip_wins_over_include(self) -> None:
        result = _run_generate_tests(profiles={Profile.BASELINE, Profile.MAIN}, skip_profiles={Profile.MAIN})
        self.assertEqual(result, {"baseline-a"})


class TestParseProfiles(unittest.TestCase):
    def setUp(self) -> None:
        self.fluster = Fluster(
            test_suites_dir="unused",
            resources_dir="unused",
            output_dir="unused",
        )

    def test_none_returns_empty_set(self) -> None:
        self.assertEqual(self.fluster._parse_profiles(None), set())  # noqa: SLF001

    def test_empty_list_returns_empty_set(self) -> None:
        self.assertEqual(self.fluster._parse_profiles([]), set())  # noqa: SLF001

    def test_names_are_case_insensitive(self) -> None:
        parsed = self.fluster._parse_profiles(["baseline", "VP9 PROFILE 0"])  # noqa: SLF001
        self.assertEqual(parsed, {Profile.BASELINE, Profile.VP9_PROFILE_0})

    def test_unknown_profile_exits(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self.fluster._parse_profiles(["NotAProfile"])  # noqa: SLF001
        self.assertIn("Unknown profile 'NotAProfile'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
