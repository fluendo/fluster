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
GStreamer utilities for Fluster.

This package provides CFFI bindings for GStreamer and a pipeline runner
that can be used to run GStreamer pipelines without depending on the
GStreamer Python bindings (gi.repository.Gst).
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

from fluster.gstreamer.gst_cffi import GStreamerInstallation
from fluster.gstreamer.runner import ExitCode as ExitCode


def run_pipeline(
    pipeline: str,
    timeout: Optional[int] = None,
    verbose: bool = False,
    quiet: bool = False,
    print_messages: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Run a GStreamer pipeline in a subprocess with proper environment setup.

    This is a convenience function that handles environment configuration and
    spawns the GStreamer runner as a subprocess. It's the recommended way to
    run GStreamer pipelines from fluster.

    Args:
        pipeline: The GStreamer pipeline description string (gst-launch format).
        timeout: Timeout in seconds for the pipeline to complete. None for no timeout.
        verbose: Enable verbose output from the runner.
        quiet: Suppress output except errors.
        print_messages: Print all bus messages (like gst-launch -m).

    Returns:
        subprocess.CompletedProcess with returncode, stdout, and stderr.

    Exit codes (see ExitCode enum):
        SUCCESS (0) - Pipeline completed successfully (EOS)
        ERROR (1) - Pipeline error occurred
        INIT_ERROR (2) - Invalid arguments or initialization error
        TIMEOUT (3) - Timeout occurred
    """
    cmd = [sys.executable, "-m", "fluster.gstreamer.runner"]
    if verbose:
        cmd.append("--verbose")
    if quiet:
        cmd.append("--quiet")
    if print_messages:
        cmd.append("--messages")
    if timeout is not None:
        cmd.extend(["--timeout", str(timeout)])
    cmd.append(pipeline)
    env = os.environ.copy()
    env.update(GStreamerInstallation().get_environment())
    return subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
