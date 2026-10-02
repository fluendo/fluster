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

This package provides ctypes bindings for GStreamer and a pipeline runner
that can be used to run GStreamer pipelines without depending on the
GStreamer Python bindings (gi.repository.Gst).
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

from fluster.decoder import NotSupportedError
from fluster.gstreamer.gst_ctypes import GStreamerInstallation

# Extra seconds added to the pipeline timeout of the subprocess call, so the
# runner can enforce and report the timeout itself before its parent gives up.
SUBPROCESS_TIMEOUT_GRACE = 30


def run_pipeline(
    pipeline: str,
    timeout: Optional[int] = None,
    verbose: bool = False,
    quiet: bool = False,
    print_messages: bool = False,
    env: Optional[dict[str, str]] = None,
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
        env: Base environment for the runner subprocess. None to inherit the
            current environment.

    Returns:
        subprocess.CompletedProcess with returncode, stdout, and stderr.

    Raises:
        NotSupportedError: When GStreamer cannot handle the media.
        subprocess.TimeoutExpired: When a timeout occurs.
        subprocess.CalledProcessError: For other non-zero exit codes.

    Exit codes (see ExitCode enum):
        SUCCESS (0) - Pipeline completed successfully (EOS)
        ERROR (1) - Pipeline error occurred
        INIT_ERROR (2) - Invalid arguments or initialization error
        TIMEOUT (3) - Timeout occurred
        NOT_SUPPORTED (69) - Format/codec not supported
    """
    # Imported here (instead of at module import time) so that executing the
    # runner with "python -m fluster.gstreamer.runner" does not import it twice
    # and trigger a RuntimeWarning from runpy.
    from fluster.gstreamer.runner import ExitCode

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

    process_env = os.environ.copy() if env is None else env.copy()
    process_env.update(GStreamerInstallation().get_environment(process_env))
    # Make sure the runner module can be imported even when fluster is run from
    # a source checkout and the current directory is not the fluster root.
    pkg_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    process_env["PYTHONPATH"] = os.pathsep.join(filter(None, [pkg_root, process_env.get("PYTHONPATH")]))

    if verbose:
        print(f'\nRunning pipeline "{pipeline}"')

    # The runner enforces the pipeline timeout and reports it through the TIMEOUT
    # exit code. A slightly longer subprocess timeout is used as a safety net so
    # that a stuck runner (e.g. during teardown/cleanup) cannot block fluster
    # forever.
    subprocess_timeout = timeout + SUBPROCESS_TIMEOUT_GRACE if timeout is not None else None
    result = subprocess.run(
        cmd,
        env=process_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=subprocess_timeout,
    )

    if verbose:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode == ExitCode.SUCCESS:
        return result
    if result.returncode == ExitCode.NOT_SUPPORTED:
        raise NotSupportedError(f"GStreamer runner not supported error: {result.stderr.strip()}")
    if result.returncode == ExitCode.TIMEOUT:
        raise subprocess.TimeoutExpired(
            result.args,
            timeout if timeout is not None else 0,
            output=result.stdout,
            stderr=result.stderr,
        )
    raise subprocess.CalledProcessError(
        result.returncode,
        result.args,
        output=result.stdout,
        stderr=result.stderr,
    )
