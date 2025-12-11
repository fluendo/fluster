# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
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

import os
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
FLUSTER_SCRIPT = PROJECT_ROOT / "fluster.py"
CHECK_DIR = PROJECT_ROOT / "check"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def run_fluster(
    args: List[str],
    no_emoji: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run the fluster CLI with the given arguments.

    Args:
        args: List of arguments to pass to fluster.py
        no_emoji: If True, add --no-emoji flag

    Returns:
        CompletedProcess with stdout and stderr
    """
    cmd = [sys.executable, str(FLUSTER_SCRIPT), "-tsd", str(CHECK_DIR)]
    # Always use --no-emoji on Windows to avoid encoding issues
    if no_emoji or IS_WINDOWS:
        cmd.append("-ne")
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result


class TestList(unittest.TestCase):
    def test_list_basic(self) -> None:
        result = run_fluster(["list"])
        self.assertIn("dummy", result.stdout)
        self.assertIn("Dummy", result.stdout)

    def test_list_with_check(self) -> None:
        result = run_fluster(["list", "-c"])
        self.assertIn("dummy", result.stdout)

    def test_list_no_emoji_with_check(self) -> None:
        result = run_fluster(["list", "-c"], no_emoji=True)
        self.assertIn("dummy", result.stdout)
        # Should not contain emoji characters
        self.assertNotIn("✔", result.stdout)
        self.assertNotIn("❌", result.stdout)

    def test_list_test_suite_with_vectors(self) -> None:
        result = run_fluster(["list", "-ts", "dummy", "-tv"])
        self.assertIn("dummy", result.stdout)
        self.assertIn("one", result.stdout)


class TestDownload(unittest.TestCase):
    def test_download_dummy_suites(self) -> None:
        result = run_fluster(["download", "dummy", "dummy_fail", "-k"])
        self.assertEqual(result.returncode, 0)

    def test_download_non_existing_suite_fails(self) -> None:
        result = run_fluster(["download", "dummy", "non_existing_test_suite", "-k"])
        self.assertNotEqual(result.returncode, 0)

    def test_download_checksum_failure(self) -> None:
        result = run_fluster(["download", "dummy", "dummy_download_fail", "-k"])
        self.assertNotEqual(result.returncode, 0)

    def test_download_h264_h265(self) -> None:
        result = run_fluster(["download", "H264-min", "H265-min", "-k"])
        self.assertEqual(result.returncode, 0)

    def test_download_av1_vp8_vp9(self) -> None:
        result = run_fluster(["download", "AV1-min", "VP8-min", "VP9-min", "-k"])
        self.assertEqual(result.returncode, 0)


class TestReference(unittest.TestCase):
    def setUp(self) -> None:
        run_fluster(["download", "dummy", "-k"])

    def test_reference_dummy(self) -> None:
        result = run_fluster(["reference", "Dummy", "dummy"])
        self.assertIn("Reference run", result.stdout)
        self.assertEqual(result.returncode, 0)


class TestRun(unittest.TestCase):
    def setUp(self) -> None:
        run_fluster(["download", "dummy", "dummy_fail", "-k"])

    def test_run_single_vector(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-tv", "one"])
        self.assertIn("Success", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_run_single_vector_single_job(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-tv", "one", "-j1"])
        self.assertIn("Success", result.stdout)

    def test_run_with_summary(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-s"])
        self.assertIn("Success", result.stdout)
        self.assertIn("TOTAL", result.stdout)

    def test_run_no_emoji_with_summary(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-s"], no_emoji=True)
        self.assertIn("Success", result.stdout)
        # Should not contain emoji
        self.assertNotIn("✔", result.stdout)

    def test_run_with_summary_output_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            summary_file = f.name

        try:
            result = run_fluster(["run", "-ts", "dummy", "-so", summary_file])
            self.assertEqual(result.returncode, 0)

            # Verify summary file was created and has content
            self.assertTrue(os.path.exists(summary_file))
            with open(summary_file, "r") as f:
                content = f.read()
                self.assertIn("TOTAL", content)
        finally:
            if os.path.exists(summary_file):
                os.unlink(summary_file)

    def test_run_single_job_with_summary(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-j1", "-s"])
        self.assertIn("Success", result.stdout)

    def test_run_threshold_pass(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-th", "1"])
        self.assertEqual(result.returncode, 0)

    def test_run_time_threshold_pass(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-tth", "10"])
        self.assertEqual(result.returncode, 0)

    def test_run_non_existing_suite_fails(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "non_existing_test_suite"])
        self.assertNotEqual(result.returncode, 0)

    def test_run_threshold_below_fails_exit_2(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-th", "2"])
        self.assertEqual(result.returncode, 2)

    def test_run_time_threshold_exceeded_exit_3(self) -> None:
        result = run_fluster(["run", "-ts", "dummy", "-tth", "0.000000001"])
        self.assertEqual(result.returncode, 3)

    def test_run_dummy_fail_threshold_1(self) -> None:
        result = run_fluster(["run", "-ts", "dummy_fail", "-th", "1"])
        self.assertEqual(result.returncode, 0)

    def test_run_dummy_fail_threshold_2_exit_2(self) -> None:
        result = run_fluster(["run", "-ts", "dummy_fail", "-th", "2"])
        self.assertEqual(result.returncode, 2)

    def test_run_failfast(self) -> None:
        result = run_fluster(["run", "-ts", "dummy_fail", "-j1", "-ff", "-s"])
        self.assertNotEqual(result.returncode, 0)

    @unittest.skipIf(IS_WINDOWS, "Unix-specific test")
    def test_run_h264_decoders(self) -> None:
        run_fluster(["download", "H264-min", "-k"])
        result = run_fluster(["run", "-ts", "H264-min", "-d", "GStreamer-H.264-Libav-Gst1.0", "FFmpeg-H.264", "-s"])
        # May fail if decoders are not available, but command should run
        self.assertTrue("H264-min" in result.stdout or "Skipping" in result.stdout)

    @unittest.skipIf(IS_WINDOWS, "Unix-specific test")
    def test_run_h265_decoders(self) -> None:
        run_fluster(["download", "H265-min", "-k"])
        result = run_fluster(["run", "-ts", "H265-min", "-d", "GStreamer-H.265-Libav-Gst1.0", "FFmpeg-H.265", "-s"])
        # May fail if decoders are not available, but command should run
        self.assertTrue("H265-min" in result.stdout or "Skipping" in result.stdout)

    @unittest.skipUnless(IS_LINUX, "Linux-specific test")
    def test_run_av1_libaom(self) -> None:
        run_fluster(["download", "AV1-min", "-k"])
        result = run_fluster(["run", "-ts", "AV1-min", "-d", "libaom-AV1", "-s"])
        self.assertTrue("AV1-min" in result.stdout or "Skipping" in result.stdout or "cannot be run" in result.stdout)

    @unittest.skipUnless(IS_LINUX, "Linux-specific test")
    def test_run_vp8_libvpx(self) -> None:
        run_fluster(["download", "VP8-min", "-k"])
        result = run_fluster(["run", "-ts", "VP8-min", "-d", "libvpx-VP8", "-s"])
        self.assertTrue("VP8-min" in result.stdout or "Skipping" in result.stdout or "cannot be run" in result.stdout)

    @unittest.skipUnless(IS_LINUX, "Linux-specific test")
    def test_run_vp9_libvpx(self) -> None:
        run_fluster(["download", "VP9-min", "-k"])
        result = run_fluster(["run", "-ts", "VP9-min", "-d", "libvpx-VP9", "-s"])
        self.assertTrue("VP9-min" in result.stdout or "Skipping" in result.stdout or "cannot be run" in result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
