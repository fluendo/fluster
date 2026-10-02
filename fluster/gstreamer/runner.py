#!/usr/bin/env python3
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

"""
GStreamer pipeline runner using ctypes bindings.

This script provides a replacement for gst-launch-1.0 that can be used by
fluster to run GStreamer pipelines. It uses custom ctypes bindings to avoid
depending on the GStreamer Python bindings (gi.repository.Gst).

fluster needs more control over pipeline errors than gst-launch-1.0 offers:
inspecting the messages posted on the pipeline bus lets this runner tell a
pipeline misconfiguration apart from media that GStreamer cannot handle
(missing plugin, unsupported codec, caps not negotiated, ...). Those cases are reported through
dedicated exit codes so the caller can mark a test vector as not supported
instead of as a failed test.

Usage:
    python -m fluster.gstreamer.runner [options] <pipeline_description>

Options:
    -m, --messages      Print all bus messages (similar to gst-launch -m)
    -v, --verbose       Enable verbose output
    -t, --timeout       Timeout in seconds (default: no timeout)
    -q, --quiet         Suppress output except errors

Exit codes:
    0 - Pipeline completed successfully (EOS)
    1 - Pipeline error occurred
    2 - Invalid arguments or initialization error
    3 - Timeout occurred
    69 - Format/codec not supported (EX_UNAVAILABLE, like gst-launch-1.0)
"""

from __future__ import annotations

import argparse
import ctypes
import signal
import sys
import time
from enum import IntEnum
from typing import Optional

from fluster.gstreamer.gst_ctypes import (
    GST_CLOCK_TIME_NONE,
    GST_CORE_ERROR_MISSING_PLUGIN,
    GST_FLOW_NOT_NEGOTIATED,
    GST_MESSAGE_ANY,
    GST_MESSAGE_ELEMENT,
    GST_MESSAGE_EOS,
    GST_MESSAGE_ERROR,
    GST_MESSAGE_WARNING,
    GST_SECOND,
    GST_STATE_CHANGE_FAILURE,
    GST_STATE_NULL,
    GST_STATE_PLAYING,
    GST_STREAM_ERROR_CODEC_NOT_FOUND,
    GST_STREAM_ERROR_NOT_IMPLEMENTED,
    GstCtypes,
    GstMessageError,
    GStreamerError,
)


class ExitCode(IntEnum):
    """Exit codes for the GStreamer runner."""

    SUCCESS = 0
    ERROR = 1
    INIT_ERROR = 2
    TIMEOUT = 3
    # BSD sysexits.h EX_UNAVAILABLE, also returned by gst-launch-1.0 when the
    # media is not supported (missing plugin, unsupported codec, ...).
    NOT_SUPPORTED = 69


class GStreamerRunner:
    """Runs GStreamer pipelines using ctypes bindings."""

    def __init__(
        self,
        verbose: bool = False,
        print_messages: bool = False,
        quiet: bool = False,
        timeout: Optional[int] = None,
    ) -> None:
        self.verbose = verbose
        self.print_messages = print_messages
        self.quiet = quiet
        self.timeout = timeout
        self.gst: Optional[GstCtypes] = None
        self.pipeline: Optional[ctypes.c_void_p] = None
        self.bus: Optional[ctypes.c_void_p] = None
        self._interrupted = False
        self._missing_plugin = False

    def _is_not_supported_error(self, error: GstMessageError) -> bool:
        """Return whether a Gst error maps to an unsupported decoder result."""
        if self.gst is None:
            return False

        if error.domain == self.gst.stream_error_quark():
            # No element accepted the stream's caps, e.g. a bit depth or chroma format the decoder lacks.
            if error.flow_return == GST_FLOW_NOT_NEGOTIATED:
                return True
            return error.code in (GST_STREAM_ERROR_CODEC_NOT_FOUND, GST_STREAM_ERROR_NOT_IMPLEMENTED)

        if error.domain == self.gst.core_error_quark():
            return error.code == GST_CORE_ERROR_MISSING_PLUGIN

        return False

    def _log(self, message: str) -> None:
        """Log a message if not in quiet mode."""
        if not self.quiet:
            print(message)

    def _log_verbose(self, message: str) -> None:
        """Log a message if in verbose mode."""
        if self.verbose and not self.quiet:
            print(message)

    def _log_error(self, message: str) -> None:
        """Log an error message (always shown)."""
        print(message, file=sys.stderr)

    def _signal_handler(self, signum: int, frame: object) -> None:
        """Handle interrupt signals."""
        self._interrupted = True
        self._log("\nInterrupt received, stopping pipeline...")

    def init(self) -> None:
        """Initialize GStreamer."""
        self.gst = GstCtypes()
        self.gst.init()
        self._log_verbose("GStreamer initialized")

    def deinit(self) -> None:
        """Deinitialize GStreamer once the pipeline is done."""
        if self.gst is not None:
            self.gst.deinit()
            self.gst = None

    def run_pipeline(self, pipeline_description: str) -> int:
        """
        Run a GStreamer pipeline.

        Args:
            pipeline_description: The pipeline description string

        Returns:
            Exit code: SUCCESS, ERROR, INIT_ERROR, or TIMEOUT
        """
        if self.gst is None:
            self._log_error("GStreamer not initialized")
            return ExitCode.INIT_ERROR

        # Install signal handlers
        original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            return self._run_pipeline_internal(pipeline_description)
        finally:
            # Restore signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            # Cleanup
            self._cleanup()

    def _run_pipeline_internal(self, pipeline_description: str) -> int:
        """Internal pipeline execution logic."""
        if self.gst is None:
            return ExitCode.INIT_ERROR

        self._log_verbose(f"Creating pipeline: {pipeline_description}")

        # Parse and create the pipeline
        try:
            self.pipeline = self.gst.parse_launch(pipeline_description)
        except GStreamerError as e:
            self._log_error(f"ERROR: {e}")
            return ExitCode.ERROR

        if not self.pipeline:
            self._log_error("ERROR: Failed to create pipeline")
            return ExitCode.ERROR

        # Get the bus
        self.bus = self.gst.element_get_bus(self.pipeline)
        if not self.bus:
            self._log_error("ERROR: Failed to get pipeline bus")
            return ExitCode.ERROR

        # Set pipeline to PLAYING
        self._log_verbose("Setting pipeline to PLAYING")
        ret = self.gst.element_set_state(self.pipeline, GST_STATE_PLAYING)

        if ret == GST_STATE_CHANGE_FAILURE:
            self._log_error("ERROR: Failed to set pipeline to PLAYING state")
            return ExitCode.ERROR

        self._log_verbose("Pipeline is running...")

        # Calculate timeout in nanoseconds
        if self.timeout:
            timeout_ns = self.timeout * GST_SECOND
        else:
            timeout_ns = GST_CLOCK_TIME_NONE

        # Message loop
        return self._message_loop(timeout_ns)

    def _message_loop(self, timeout_ns: int) -> int:
        """Process messages from the bus until EOS or error."""
        if self.gst is None or self.bus is None:
            return ExitCode.INIT_ERROR

        # Message types we're interested in
        if self.print_messages:
            msg_types = GST_MESSAGE_ANY
        else:
            msg_types = GST_MESSAGE_EOS | GST_MESSAGE_ERROR | GST_MESSAGE_WARNING | GST_MESSAGE_ELEMENT

        # Poll in short intervals so interrupts are responsive, and so the
        # timeout is checked even while messages keep arriving.
        poll_interval = GST_SECOND
        deadline = None if timeout_ns == GST_CLOCK_TIME_NONE else time.monotonic() + timeout_ns / GST_SECOND

        while not self._interrupted:
            # Check the timeout before blocking on the bus, otherwise a pipeline
            # that keeps posting messages would never time out.
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._log_error("ERROR: Pipeline timed out")
                    return ExitCode.TIMEOUT
                poll_timeout = max(1, min(poll_interval, int(remaining * GST_SECOND)))
            else:
                poll_timeout = poll_interval

            msg = self.gst.bus_timed_pop_filtered(self.bus, poll_timeout, msg_types)
            if msg is None:
                continue

            result = self._handle_message(msg)
            self.gst.message_unref(msg)
            if result is not None:
                return result

        # Interrupted
        self._log("Pipeline interrupted")
        return ExitCode.ERROR

    def _handle_message(self, msg: ctypes.c_void_p) -> Optional[int]:
        """
        Handle a bus message.

        Returns:
            None to continue, exit code to stop
        """
        if self.gst is None:
            return ExitCode.INIT_ERROR

        msg_type = self.gst.message_get_type(msg)

        if msg_type == GST_MESSAGE_EOS:
            self._log_verbose("End of stream")
            return ExitCode.SUCCESS

        if msg_type == GST_MESSAGE_ERROR:
            error = self.gst.message_parse_error(msg)
            self._log_error(f"ERROR: {error.message}")
            if self.verbose and error.debug:
                self._log_error(f"Debug: {error.debug}")
            # Post not supported if a missing plugin was found earlier
            if self._missing_plugin or self._is_not_supported_error(error):
                return ExitCode.NOT_SUPPORTED
            return ExitCode.ERROR

        if msg_type == GST_MESSAGE_WARNING:
            warn_msg, debug_msg = self.gst.message_parse_warning(msg)
            if not self.quiet:
                self._log(f"WARNING: {warn_msg}")
                if self.verbose and debug_msg:
                    self._log(f"Debug: {debug_msg}")

        elif msg_type == GST_MESSAGE_ELEMENT:
            structure = self.gst.message_get_structure(msg)
            # Autopluggers post this for any stream they cannot handle and keep going, so it
            # only means "not supported" if the pipeline then fails.
            if structure and self.gst.structure_get_name(structure) == "missing-plugin":
                self._log_error("WARNING: No suitable plugin found for a stream")
                self._missing_plugin = True

        # -m prints the structure of every message, like gst-launch -m.
        if self.print_messages:
            structure = self.gst.message_get_structure(msg)
            if structure:
                struct_str = self.gst.structure_to_string(structure)
                if struct_str:
                    print(struct_str)

        return None

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.gst is None:
            return

        if self.pipeline:
            self._log_verbose("Setting pipeline to NULL")
            self.gst.element_set_state(self.pipeline, GST_STATE_NULL)
            self.gst.object_unref(self.pipeline)
            self.pipeline = None

        if self.bus:
            self.gst.object_unref(self.bus)
            self.bus = None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run GStreamer pipelines using ctypes bindings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "videotestsrc num-buffers=100 ! fakesink"
    %(prog)s -m "filesrc location=test.mp4 ! decodebin ! videoconvert ! fakesink"
    %(prog)s -t 30 "filesrc location=test.h264 ! h264parse ! avdec_h264 ! fakesink"
""",
    )
    parser.add_argument(
        "pipeline",
        nargs="?",
        help="Pipeline description (gst-launch format)",
    )
    parser.add_argument(
        "-m",
        "--messages",
        action="store_true",
        help="Print all bus messages",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress output except errors",
    )

    args = parser.parse_args()

    if not args.pipeline:
        parser.print_help()
        return ExitCode.INIT_ERROR

    runner = GStreamerRunner(
        verbose=args.verbose,
        print_messages=args.messages,
        quiet=args.quiet,
        timeout=args.timeout,
    )
    try:
        runner.init()
        return runner.run_pipeline(args.pipeline)
    except GStreamerError as e:
        print(f"GStreamer error: {e}", file=sys.stderr)
        return ExitCode.INIT_ERROR
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return ExitCode.ERROR
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return ExitCode.INIT_ERROR
    finally:
        runner.deinit()


if __name__ == "__main__":
    sys.exit(main())
