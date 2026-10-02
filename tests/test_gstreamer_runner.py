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

"""Unit tests for the GStreamer pipeline runner.

These tests do not require GStreamer to be installed: the ctypes bindings and
the runner are exercised through lightweight fakes and mocked subprocesses.
"""

from __future__ import annotations

import ctypes
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Optional, Tuple, cast
from unittest import mock

from fluster.decoder import NotSupportedError
from fluster.gstreamer import SUBPROCESS_TIMEOUT_GRACE, run_pipeline
from fluster.gstreamer.gst_ctypes import (
    GST_CLOCK_TIME_NONE,
    GST_CORE_ERROR_MISSING_PLUGIN,
    GST_FLOW_NOT_NEGOTIATED,
    GST_MESSAGE_ELEMENT,
    GST_MESSAGE_EOS,
    GST_MESSAGE_ERROR,
    GST_MESSAGE_STATE_CHANGED,
    GST_MESSAGE_UNKNOWN,
    GST_MESSAGE_WARNING,
    GST_STREAM_ERROR_CODEC_NOT_FOUND,
    GST_STREAM_ERROR_NOT_IMPLEMENTED,
    GErrorStruct,
    GstCtypes,
    GstMessageError,
    GStreamerError,
    GStreamerInstallation,
    _GstMessageHead,
    _GstMiniObject,
)
from fluster.gstreamer.runner import ExitCode, GStreamerRunner, main

DUMMY_MSG = ctypes.c_void_p(1)
DUMMY_BUS = ctypes.c_void_p(2)

CORE_ERROR_QUARK = 1000
STREAM_ERROR_QUARK = 2000

# GStreamer sets the high bit for "extended" message types (GST_MESSAGE_EXTENDED
# is 1 << 31) and numbers the types after it sequentially. Several of them share
# low bits with the basic message types, which is why a bitmask test is wrong.
GST_MESSAGE_EXTENDED = 1 << 31
GST_MESSAGE_DEVICE_ADDED = GST_MESSAGE_EXTENDED + 1
GST_MESSAGE_DEVICE_REMOVED = GST_MESSAGE_EXTENDED + 2
GST_MESSAGE_STREAM_COLLECTION = GST_MESSAGE_EXTENDED + 4
GST_MESSAGE_STREAMS_SELECTED = GST_MESSAGE_EXTENDED + 5


class FakeGst:
    """Minimal stand-in for :class:`GstCtypes` used to test message handling."""

    def __init__(
        self,
        msg_type: int = 0,
        structure_name: str = "",
        error: Optional[GstMessageError] = None,
        warning: str = "",
    ) -> None:
        self.msg_type = msg_type
        self.structure_name = structure_name
        self.error = error if error is not None else GstMessageError(0, 0, "", "")
        self.warning = warning
        self.parse_error_calls = 0
        self.parse_warning_calls = 0

    def core_error_quark(self) -> int:
        return CORE_ERROR_QUARK

    def stream_error_quark(self) -> int:
        return STREAM_ERROR_QUARK

    def message_get_type(self, message: ctypes.c_void_p) -> int:
        return self.msg_type

    def message_parse_error(self, message: ctypes.c_void_p) -> GstMessageError:
        self.parse_error_calls += 1
        return self.error

    def message_parse_warning(self, message: ctypes.c_void_p) -> Tuple[str, str]:
        self.parse_warning_calls += 1
        return self.warning, ""

    def message_get_structure(self, message: ctypes.c_void_p) -> Optional[ctypes.c_void_p]:
        return DUMMY_MSG if self.structure_name else None

    def structure_get_name(self, structure: ctypes.c_void_p) -> str:
        return self.structure_name

    def structure_to_string(self, structure: ctypes.c_void_p) -> str:
        return self.structure_name

    def bus_timed_pop_filtered(
        self, bus: ctypes.c_void_p, timeout: int, message_types: int
    ) -> Optional[ctypes.c_void_p]:
        return DUMMY_MSG

    def message_unref(self, message: ctypes.c_void_p) -> None:
        """Nothing to release in the fake."""


def _ignore_log(message: str) -> None:
    """Discard a runner log message to keep the test output clean."""


def make_runner(gst: FakeGst) -> GStreamerRunner:
    """Build a quiet runner wired to *gst*, bypassing GStreamer initialization."""
    runner = GStreamerRunner(quiet=True)
    runner.gst = cast(Any, gst)
    runner.bus = DUMMY_BUS
    runner._log_error = _ignore_log  # type: ignore[method-assign]  # noqa: SLF001
    return runner


def handle(runner: GStreamerRunner) -> Optional[int]:
    """Call the runner's message handler with a dummy message."""
    return runner._handle_message(DUMMY_MSG)  # noqa: SLF001


class FakeLibraries:
    """Replace the loaded GStreamer/GLib libraries of :class:`GstCtypes`.

    This lets the helpers that read and free GLib strings be tested without a
    GStreamer installation.
    """

    def __init__(self) -> None:
        self.gst = GstCtypes()
        self._original = (self.gst._gst, self.gst._glib)  # noqa: SLF001
        self.gst_mock = mock.Mock()
        self.glib_mock = mock.Mock()
        self.gst._gst = self.gst_mock  # noqa: SLF001
        self.gst._glib = self.glib_mock  # noqa: SLF001

    def restore(self) -> None:
        """Put the original libraries back on the singleton."""
        self.gst._gst, self.gst._glib = self._original  # noqa: SLF001


class FakeOutParameter:
    """Emulates a GStreamer function that fills ``c_void_p`` out parameters.

    ``ctypes.byref()`` keeps the wrapped object in ``_obj``, which is where the
    pointers the real function would return are written.
    """

    def __init__(self, error_ptr: int = 0, debug_ptr: int = 0) -> None:
        self.error_ptr = error_ptr
        self.debug_ptr = debug_ptr

    def __call__(self, message: Any, error_out: Any, debug_out: Any) -> None:
        error_out._obj.value = self.error_ptr  # noqa: SLF001
        debug_out._obj.value = self.debug_ptr  # noqa: SLF001


def c_string(value: bytes) -> Tuple[Any, int]:
    """Return a NUL-terminated C string buffer along with its address."""
    buffer = ctypes.create_string_buffer(value)
    return buffer, ctypes.cast(buffer, ctypes.c_void_p).value or 0


class TestExitCodes(unittest.TestCase):
    def test_not_supported_uses_ex_unavailable(self) -> None:
        # EX_UNAVAILABLE from sysexits.h, matching gst-launch-1.0 behaviour.
        self.assertEqual(int(ExitCode.NOT_SUPPORTED), 69)


class TestHandleMessage(unittest.TestCase):
    def test_eos_returns_success(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_EOS))
        self.assertEqual(handle(runner), ExitCode.SUCCESS)

    def test_error_returns_error(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR))
        self.assertEqual(handle(runner), ExitCode.ERROR)

    def test_missing_plugin_error_is_not_supported(self) -> None:
        error = GstMessageError(CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, "missing", "")
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.NOT_SUPPORTED)

    def test_codec_not_found_error_is_not_supported(self) -> None:
        error = GstMessageError(STREAM_ERROR_QUARK, GST_STREAM_ERROR_CODEC_NOT_FOUND, "missing", "")
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.NOT_SUPPORTED)

    def test_missing_plugin_element_is_not_supported(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ELEMENT, structure_name="missing-plugin"))
        self.assertEqual(handle(runner), ExitCode.NOT_SUPPORTED)

    def test_non_missing_plugin_element_is_ignored(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ELEMENT, structure_name="something-else"))
        self.assertIsNone(handle(runner))

    def test_unknown_message_is_ignored(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_STATE_CHANGED))
        self.assertIsNone(handle(runner))

    def test_extended_types_are_not_mistaken_for_basic_ones(self) -> None:
        # These extended types set low bits that overlap EOS/ERROR/WARNING.
        for msg_type in (
            GST_MESSAGE_DEVICE_ADDED,
            GST_MESSAGE_DEVICE_REMOVED,
            GST_MESSAGE_STREAM_COLLECTION,
            GST_MESSAGE_STREAMS_SELECTED,
        ):
            with self.subTest(msg_type=msg_type):
                gst = FakeGst(msg_type=msg_type)
                runner = make_runner(gst)
                self.assertIsNone(handle(runner))
                self.assertEqual(gst.parse_error_calls, 0)
                self.assertEqual(gst.parse_warning_calls, 0)

    def test_warning_message_is_parsed(self) -> None:
        gst = FakeGst(msg_type=GST_MESSAGE_WARNING, warning="careful")
        runner = make_runner(gst)
        self.assertIsNone(handle(runner))
        self.assertEqual(gst.parse_warning_calls, 1)


class TestMessageTypeRead(unittest.TestCase):
    def test_gst_mini_object_layout(self) -> None:
        # GstMessage starts with a GstMiniObject. The size is 64 bytes on
        # 64-bit but 36 (not 32) on 32-bit: nine 4-byte fields, no padding.
        expected_size = 64 if ctypes.sizeof(ctypes.c_void_p) == 8 else 36
        self.assertEqual(ctypes.sizeof(_GstMiniObject), expected_size)
        self.assertEqual(_GstMessageHead.type.offset, ctypes.sizeof(_GstMiniObject))

    def test_extended_type_is_read_as_unsigned(self) -> None:
        gst = GstCtypes()
        buffer = ctypes.create_string_buffer(ctypes.sizeof(_GstMessageHead))
        type_value = GST_MESSAGE_STREAMS_SELECTED
        ctypes.c_uint.from_buffer(buffer, _GstMessageHead.type.offset).value = type_value
        self.assertEqual(gst.message_get_type(ctypes.cast(buffer, ctypes.c_void_p)), type_value)


class TestWindowsLibraryLookup(unittest.TestCase):
    """The Windows lookup path is exercised with a faked layout and platform."""

    def setUp(self) -> None:
        self.installation = GStreamerInstallation()
        self.original_lib_path = self.installation._lib_path  # noqa: SLF001
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        self.installation._lib_path = self.original_lib_path  # noqa: SLF001

    def test_finds_msvc_and_mingw_dll_spellings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("fluster.gstreamer.gst_ctypes.platform.system", return_value="Windows"):
                self.installation._lib_path = tmpdir  # noqa: SLF001

                # MSVC ships "glib-2.0-0.dll"
                msvc = os.path.join(tmpdir, "glib-2.0-0.dll")
                with open(msvc, "w"):
                    pass
                self.assertEqual(self.installation.find_library("glib-2.0"), msvc)
                os.remove(msvc)

                # MinGW ships "libglib-2.0-0.dll"
                mingw = os.path.join(tmpdir, "libglib-2.0-0.dll")
                with open(mingw, "w"):
                    pass
                self.assertEqual(self.installation.find_library("glib-2.0"), mingw)


class TestMessageLoop(unittest.TestCase):
    def test_timeout_after_continuous_messages(self) -> None:
        # Even if messages keep arriving, the loop must honour the timeout.
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_STATE_CHANGED))
        self.assertEqual(runner._message_loop(10 * 1000 * 1000), ExitCode.TIMEOUT)  # noqa: SLF001

    def test_interrupt_returns_error(self) -> None:
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_STATE_CHANGED))
        runner._interrupted = True  # noqa: SLF001
        self.assertEqual(runner._message_loop(GST_CLOCK_TIME_NONE), ExitCode.ERROR)  # noqa: SLF001

    def test_missing_bus_returns_init_error(self) -> None:
        runner = make_runner(FakeGst())
        runner.bus = None
        self.assertEqual(runner._message_loop(GST_CLOCK_TIME_NONE), ExitCode.INIT_ERROR)  # noqa: SLF001


class TestRunPipeline(unittest.TestCase):
    def _mock_run(self, returncode: int) -> mock.Mock:
        completed: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
            args=["fluster.gstreamer.runner"], returncode=returncode
        )
        completed.stdout = "stdout"
        completed.stderr = "stderr"
        patcher = mock.patch.object(subprocess, "run", return_value=completed)
        run_mock = patcher.start()
        self.addCleanup(patcher.stop)
        return run_mock

    def test_success_returns_result(self) -> None:
        self._mock_run(int(ExitCode.SUCCESS))
        result = run_pipeline("videotestsrc ! fakesink", timeout=10)
        self.assertEqual(result.stdout, "stdout")

    def test_not_supported_raises(self) -> None:
        self._mock_run(int(ExitCode.NOT_SUPPORTED))
        with self.assertRaises(NotSupportedError):
            run_pipeline("videotestsrc ! fakesink", timeout=10)

    def test_timeout_raises(self) -> None:
        self._mock_run(int(ExitCode.TIMEOUT))
        with self.assertRaises(subprocess.TimeoutExpired):
            run_pipeline("videotestsrc ! fakesink", timeout=10)

    def test_error_raises_called_process_error(self) -> None:
        self._mock_run(int(ExitCode.ERROR))
        with self.assertRaises(subprocess.CalledProcessError):
            run_pipeline("videotestsrc ! fakesink", timeout=10)

    def test_runner_is_invoked_with_pythonpath_and_without_no_fault(self) -> None:
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        run_pipeline("videotestsrc ! fakesink", timeout=10)

        cmd = run_mock.call_args[0][0]
        env = run_mock.call_args[1]["env"]
        self.assertNotIn("--no-fault", cmd)
        self.assertEqual(cmd[1:3], ["-m", "fluster.gstreamer.runner"])
        # The package root must be first on PYTHONPATH so the runner can be
        # imported regardless of the current working directory.
        package_root = env["PYTHONPATH"].split(os.pathsep)[0]
        self.assertTrue(os.path.isdir(os.path.join(package_root, "fluster")))

    def test_flags_map_to_runner_options(self) -> None:
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            run_pipeline("videotestsrc ! fakesink", timeout=5, verbose=True, quiet=True, print_messages=True)

        cmd = run_mock.call_args[0][0]
        self.assertEqual(cmd[3:6], ["--verbose", "--quiet", "--messages"])
        self.assertEqual(cmd[6:8], ["--timeout", "5"])
        self.assertEqual(cmd[-1], "videotestsrc ! fakesink")

    def test_subprocess_timeout_is_longer_than_the_pipeline_timeout(self) -> None:
        # The runner reports the timeout itself, the subprocess timeout is only
        # a safety net for a stuck runner.
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        run_pipeline("videotestsrc ! fakesink", timeout=10)
        self.assertEqual(run_mock.call_args[1]["timeout"], 10 + SUBPROCESS_TIMEOUT_GRACE)

    def test_no_timeout_means_no_subprocess_timeout(self) -> None:
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        run_pipeline("videotestsrc ! fakesink")
        self.assertIsNone(run_mock.call_args[1]["timeout"])

    def test_callers_environment_is_not_mutated(self) -> None:
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        caller_env = {"FLUSTER_TEST": "1"}
        run_pipeline("videotestsrc ! fakesink", env=caller_env)

        self.assertEqual(caller_env, {"FLUSTER_TEST": "1"})
        passed_env = run_mock.call_args[1]["env"]
        self.assertIsNot(passed_env, caller_env)
        self.assertEqual(passed_env["FLUSTER_TEST"], "1")

    def test_existing_pythonpath_is_preserved(self) -> None:
        run_mock = self._mock_run(int(ExitCode.SUCCESS))
        run_pipeline("videotestsrc ! fakesink", env={"PYTHONPATH": "/custom"})

        entries = run_mock.call_args[1]["env"]["PYTHONPATH"].split(os.pathsep)
        self.assertIn("/custom", entries)
        self.assertEqual(len(entries), 2)

    def test_verbose_prints_the_pipeline_and_the_process_output(self) -> None:
        self._mock_run(int(ExitCode.SUCCESS))
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            run_pipeline("videotestsrc ! fakesink", timeout=10, verbose=True)

        self.assertIn('Running pipeline "videotestsrc ! fakesink"', stdout.getvalue())
        self.assertIn("stdout", stdout.getvalue())
        self.assertIn("stderr", stderr.getvalue())


class TestNotSupportedMapping(unittest.TestCase):
    """Error codes that mean "the decoder cannot handle this media"."""

    def test_stream_not_implemented_is_not_supported(self) -> None:
        error = GstMessageError(STREAM_ERROR_QUARK, GST_STREAM_ERROR_NOT_IMPLEMENTED, "nope", "")
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.NOT_SUPPORTED)

    def test_unrelated_core_error_is_reported_as_error(self) -> None:
        error = GstMessageError(CORE_ERROR_QUARK, 1, "boom", "")
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.ERROR)

    def test_not_negotiated_stream_error_is_not_supported(self) -> None:
        # GST_ELEMENT_FLOW_ERROR posts GST_STREAM_ERROR_FAILED (1) with the flow return in its details.
        error = GstMessageError(STREAM_ERROR_QUARK, 1, "Internal data stream error.", "", GST_FLOW_NOT_NEGOTIATED)
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.NOT_SUPPORTED)

    def test_not_negotiated_outside_stream_domain_is_error(self) -> None:
        error = GstMessageError(CORE_ERROR_QUARK, 1, "boom", "", GST_FLOW_NOT_NEGOTIATED)
        runner = make_runner(FakeGst(msg_type=GST_MESSAGE_ERROR, error=error))
        self.assertEqual(handle(runner), ExitCode.ERROR)


class TestGstCtypesHelpers(unittest.TestCase):
    """The GLib string/GError helpers must release everything they read."""

    def setUp(self) -> None:
        self.libs = FakeLibraries()
        self.addCleanup(self.libs.restore)

    def test_read_string_decodes_and_frees(self) -> None:
        _, pointer = c_string(b"missing-plugin")
        self.assertEqual(self.libs.gst._read_string(pointer), "missing-plugin")  # noqa: SLF001
        self.libs.glib_mock.g_free.assert_called_once_with(pointer)

    def test_read_string_of_null_pointer_is_empty(self) -> None:
        self.assertEqual(self.libs.gst._read_string(None), "")  # noqa: SLF001
        self.libs.glib_mock.g_free.assert_not_called()

    def test_take_gerror_reads_the_message_and_frees_it(self) -> None:
        gerror = GErrorStruct(CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, b"no plugin")
        pointer = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0

        self.assertEqual(
            self.libs.gst._take_gerror(pointer),  # noqa: SLF001
            (CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, "no plugin"),
        )
        self.libs.glib_mock.g_error_free.assert_called_once_with(pointer)

    def test_decode_gerror_combines_message_and_domain_description(self) -> None:
        gerror = GErrorStruct(CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, b"no plugin")
        pointer = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0
        _, description = c_string(b"No such element")
        self.libs.gst_mock.gst_error_get_message.return_value = description

        decoded = self.libs.gst._decode_gerror(pointer)  # noqa: SLF001

        self.assertIn("no plugin", decoded)
        self.assertIn("No such element", decoded)
        self.assertIn(f"code={GST_CORE_ERROR_MISSING_PLUGIN}", decoded)
        # Both the GError and the string returned by GLib are released.
        self.libs.glib_mock.g_error_free.assert_called_once_with(pointer)
        self.libs.glib_mock.g_free.assert_called_once_with(description)

    def test_decode_gerror_without_error_is_empty(self) -> None:
        self.assertEqual(self.libs.gst._decode_gerror(None), "")  # noqa: SLF001

    def _fake_parse_launch(self, error_ptr: int, pipeline_ptr: int) -> None:
        """Make gst_parse_launch() return ``pipeline_ptr`` and set ``error_ptr``."""

        def parse_launch(description: bytes, error_out: Any) -> int:
            error_out._obj.value = error_ptr  # noqa: SLF001
            return pipeline_ptr

        self.libs.gst_mock.gst_parse_launch.side_effect = parse_launch
        # No translated description for the error domain.
        self.libs.gst_mock.gst_error_get_message.return_value = None

    def test_parse_launch_releases_the_partial_pipeline_on_error(self) -> None:
        gerror = GErrorStruct(CORE_ERROR_QUARK, 1, b'no element "missing"')
        error_ptr = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0
        self._fake_parse_launch(error_ptr, pipeline_ptr=0x1234)

        with self.assertRaises(GStreamerError):
            self.libs.gst.parse_launch("appsrc ! missing ! fakesink")

        self.libs.gst_mock.gst_object_unref.assert_called_once_with(0x1234)
        self.libs.glib_mock.g_error_free.assert_called_once_with(error_ptr)

    def test_parse_launch_error_without_pipeline_unrefs_nothing(self) -> None:
        gerror = GErrorStruct(CORE_ERROR_QUARK, 1, b"syntax error")
        error_ptr = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0
        self._fake_parse_launch(error_ptr, pipeline_ptr=0)

        with self.assertRaises(GStreamerError):
            self.libs.gst.parse_launch("appsrc !")

        self.libs.gst_mock.gst_object_unref.assert_not_called()

    def test_parse_launch_success_keeps_the_pipeline(self) -> None:
        self._fake_parse_launch(error_ptr=0, pipeline_ptr=0x1234)

        pipeline = self.libs.gst.parse_launch("appsrc ! fakesink")

        self.assertEqual(pipeline.value, 0x1234)
        self.libs.gst_mock.gst_object_unref.assert_not_called()


class TestMessageParsing(unittest.TestCase):
    """``message_parse_error`` and ``message_parse_warning`` share their decoding."""

    def setUp(self) -> None:
        self.libs = FakeLibraries()
        self.addCleanup(self.libs.restore)

    def test_message_parse_error_returns_all_fields(self) -> None:
        gerror = GErrorStruct(CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, b"no plugin")
        error_pointer = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0
        _, debug_pointer = c_string(b"debug dump")
        self.libs.gst_mock.gst_message_parse_error = FakeOutParameter(error_pointer, debug_pointer)

        self.assertEqual(
            self.libs.gst.message_parse_error(DUMMY_MSG),
            GstMessageError(CORE_ERROR_QUARK, GST_CORE_ERROR_MISSING_PLUGIN, "no plugin", "debug dump"),
        )

    def test_message_parse_warning_returns_the_message_and_debug(self) -> None:
        gerror = GErrorStruct(STREAM_ERROR_QUARK, 1, b"careful")
        error_pointer = ctypes.cast(ctypes.pointer(gerror), ctypes.c_void_p).value or 0
        _, debug_pointer = c_string(b"debug dump")
        self.libs.gst_mock.gst_message_parse_warning = FakeOutParameter(error_pointer, debug_pointer)

        self.assertEqual(self.libs.gst.message_parse_warning(DUMMY_MSG), ("careful", "debug dump"))

    def test_message_parse_error_without_error_is_empty(self) -> None:
        self.libs.gst_mock.gst_message_parse_error = FakeOutParameter()
        self.assertEqual(self.libs.gst.message_parse_error(DUMMY_MSG), GstMessageError(0, 0, "", ""))

    def test_message_parse_error_reads_the_flow_return_detail(self) -> None:
        def parse_details(message: Any, details_out: Any) -> None:
            details_out._obj.value = 0x1234  # noqa: SLF001

        def get_int(structure: Any, field: bytes, value_out: Any) -> int:
            self.assertEqual(field, b"flow-return")
            value_out._obj.value = GST_FLOW_NOT_NEGOTIATED  # noqa: SLF001
            return 1

        self.libs.gst_mock.gst_message_parse_error = FakeOutParameter()
        self.libs.gst_mock.gst_message_parse_error_details = parse_details
        self.libs.gst_mock.gst_structure_get_int = get_int

        self.assertEqual(self.libs.gst.message_parse_error(DUMMY_MSG).flow_return, GST_FLOW_NOT_NEGOTIATED)


class TestSingletons(unittest.TestCase):
    def test_gst_ctypes_is_a_singleton(self) -> None:
        self.assertIs(GstCtypes(), GstCtypes())

    def test_installation_is_a_singleton(self) -> None:
        self.assertIs(GStreamerInstallation(), GStreamerInstallation())

    def test_message_type_of_a_null_message_is_unknown(self) -> None:
        self.assertEqual(GstCtypes().message_get_type(None), GST_MESSAGE_UNKNOWN)

    def test_deinit_calls_gst_deinit_only_once(self) -> None:
        libs = FakeLibraries()
        self.addCleanup(libs.restore)
        self.addCleanup(setattr, libs.gst, "_initialized", libs.gst._initialized)  # noqa: SLF001

        libs.gst._initialized = False  # noqa: SLF001
        libs.gst.deinit()
        libs.gst_mock.gst_deinit.assert_not_called()

        libs.gst._initialized = True  # noqa: SLF001
        libs.gst.deinit()
        libs.gst_mock.gst_deinit.assert_called_once()
        self.assertFalse(libs.gst._initialized)  # noqa: SLF001


class TestInstallationEnvironment(unittest.TestCase):
    """``get_environment`` merges into the base environment it is given."""

    def setUp(self) -> None:
        self.installation = GStreamerInstallation()
        self.original = (
            self.installation._lib_path,  # noqa: SLF001
            self.installation._plugin_path,  # noqa: SLF001
            self.installation._bin_path,  # noqa: SLF001
        )
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        lib_path, plugin_path, bin_path = self.original
        self.installation._lib_path = lib_path  # noqa: SLF001
        self.installation._plugin_path = plugin_path  # noqa: SLF001
        self.installation._bin_path = bin_path  # noqa: SLF001

    def test_macos_prepends_the_dyld_path_and_preserves_the_base(self) -> None:
        with mock.patch("fluster.gstreamer.gst_ctypes.platform.system", return_value="Darwin"):
            self.installation._lib_path = "/opt/gst/lib"  # noqa: SLF001
            self.installation._plugin_path = "/opt/gst/plugins"  # noqa: SLF001

            env = self.installation.get_environment({"DYLD_LIBRARY_PATH": "/existing"})

        self.assertEqual(env["DYLD_LIBRARY_PATH"], "/opt/gst/lib:/existing")
        self.assertEqual(env["GST_PLUGIN_SYSTEM_PATH"], "/opt/gst/plugins")

    def test_macos_does_not_duplicate_an_existing_path(self) -> None:
        with mock.patch("fluster.gstreamer.gst_ctypes.platform.system", return_value="Darwin"):
            self.installation._lib_path = "/opt/gst/lib"  # noqa: SLF001
            self.installation._plugin_path = None  # noqa: SLF001

            self.assertEqual(self.installation.get_environment({"DYLD_LIBRARY_PATH": "/opt/gst/lib"}), {})

    def test_windows_prepends_the_bin_directory(self) -> None:
        with mock.patch("fluster.gstreamer.gst_ctypes.platform.system", return_value="Windows"):
            self.installation._bin_path = "C:\\gst\\bin"  # noqa: SLF001
            self.installation._plugin_path = "C:\\gst\\plugins"  # noqa: SLF001

            env = self.installation.get_environment({"PATH": "C:\\Windows"})

        self.assertEqual(env["PATH"], "C:\\gst\\bin;C:\\Windows")
        self.assertEqual(env["GST_PLUGIN_SYSTEM_PATH"], "C:\\gst\\plugins")

    def test_linux_needs_no_extra_environment(self) -> None:
        with mock.patch("fluster.gstreamer.gst_ctypes.platform.system", return_value="Linux"):
            self.assertEqual(self.installation.get_environment(), {})


class TestRunnerLifecycle(unittest.TestCase):
    def test_run_before_init_returns_init_error(self) -> None:
        runner = GStreamerRunner(quiet=True)
        runner._log_error = _ignore_log  # type: ignore[method-assign]  # noqa: SLF001
        self.assertEqual(runner.run_pipeline("fakesrc ! fakesink"), ExitCode.INIT_ERROR)

    def test_deinit_is_idempotent(self) -> None:
        runner = GStreamerRunner(quiet=True)
        fake_gst = mock.Mock()
        runner.gst = cast(Any, fake_gst)

        runner.deinit()
        fake_gst.deinit.assert_called_once()
        self.assertIsNone(runner.gst)

        runner.deinit()
        fake_gst.deinit.assert_called_once()


class TestMain(unittest.TestCase):
    """The CLI entry point wires argparse to :class:`GStreamerRunner`."""

    def _patch(self, attribute: str, **kwargs: Any) -> mock.Mock:
        patcher = mock.patch.object(GStreamerRunner, attribute, **kwargs)
        patched: mock.Mock = patcher.start()
        self.addCleanup(patcher.stop)
        return patched

    def test_missing_pipeline_prints_the_usage_and_fails(self) -> None:
        with mock.patch.object(sys, "argv", ["runner"]), redirect_stdout(io.StringIO()):
            self.assertEqual(main(), ExitCode.INIT_ERROR)

    def test_pipeline_is_run_and_the_runner_deinitialised(self) -> None:
        run_pipeline_mock = self._patch("run_pipeline", return_value=int(ExitCode.SUCCESS))
        deinit_mock = self._patch("deinit")
        self._patch("init")

        with mock.patch.object(sys, "argv", ["runner", "fakesrc ! fakesink"]):
            self.assertEqual(main(), ExitCode.SUCCESS)

        run_pipeline_mock.assert_called_once_with("fakesrc ! fakesink")
        deinit_mock.assert_called_once()

    def test_initialisation_error_is_reported(self) -> None:
        self._patch("init", side_effect=GStreamerError("boom"))
        deinit_mock = self._patch("deinit")

        stderr = io.StringIO()
        with mock.patch.object(sys, "argv", ["runner", "fakesrc ! fakesink"]):
            with redirect_stderr(stderr):
                self.assertEqual(main(), ExitCode.INIT_ERROR)

        self.assertIn("boom", stderr.getvalue())
        deinit_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
