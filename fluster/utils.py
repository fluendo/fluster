# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
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

import array
import contextlib
import hashlib
import io
import os
import platform
import re
import subprocess
import sys
import wave
from functools import partial
from typing import List, Optional, Tuple


def file_checksum(path: str) -> str:
    """Calculates the checksum of a file reading chunks of 64KiB"""
    md5 = hashlib.md5()
    with open(path, "rb") as file:
        while True:
            data = file.read(65536)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def run_command(
    command: List[str],
    verbose: bool = False,
    check: bool = True,
    timeout: Optional[int] = None,
) -> None:
    """Runs a command"""
    sout = subprocess.DEVNULL if not verbose else None
    serr = subprocess.DEVNULL if not verbose else None
    if verbose:
        print(f'\nRunning command "{" ".join(command)}"')
    try:
        subprocess.run(command, stdout=sout, stderr=serr, check=check, timeout=timeout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as ex:
        # Developer experience improvement (facilitates copy/paste)
        ex.cmd = " ".join(ex.cmd)
        raise ex


def run_command_with_output(
    command: List[str],
    verbose: bool = False,
    check: bool = True,
    timeout: Optional[int] = None,
    keep_stderr: bool = False,
) -> str:
    """Runs a command and returns std output trace"""
    serr = subprocess.DEVNULL
    if verbose or keep_stderr:
        serr = subprocess.STDOUT
    if verbose:
        print(f'\nRunning command "{" ".join(command)}"')

    try:
        output = subprocess.check_output(command, stderr=serr, timeout=timeout, universal_newlines=True)
        if verbose and output:
            print(output)
        return output or ""
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as ex:
        if verbose and ex.output:
            # Workaround inconsistent Python implementation
            if isinstance(ex, subprocess.TimeoutExpired):
                print(ex.output.decode("utf-8"))
            else:
                print(ex.output)

        if isinstance(ex, subprocess.CalledProcessError) and not check:
            return ex.output or ""

        # Developer experience improvement (facilitates copy/paste)
        ex.cmd = " ".join(ex.cmd)
        raise ex


def normalize_binary_cmd(cmd: str) -> str:
    """Return the OS-form binary"""
    if platform.system() == "Windows":
        return cmd if cmd.endswith(".exe") else cmd + ".exe"
    if cmd.endswith(".exe"):
        return cmd.replace(".exe", "")
    return cmd


def normalize_path(path: str) -> str:
    """Normalize the path to make it Unix-like"""
    if platform.system() == "Windows":
        return path.replace("\\", "/")
    return path


def _read_wav(path: str) -> Tuple[array.array[int], int, int]:
    """Load a WAV file and return (interleaved_samples, n_channels, sampwidth).
    Supports 16 and 32-bit PCM and WAVE_FORMAT_EXTENSIBLE (0xFFFE).
    Python < 3.12 rejects WAVE_FORMAT_EXTENSIBLE, so on failure we locate
    the fmt chunk and patch only the wFormatTag — the PCM data layout is identical."""
    try:
        with wave.open(path, "rb") as w:
            return _extract_wav(w)
    except wave.Error:
        pass
    # Locate the fmt chunk in the RIFF structure and patch only wFormatTag
    with open(path, "rb") as f:
        data = bytearray(f.read())
    pos = 12  # skip RIFF + size + WAVE
    while pos < len(data) - 8:
        chunk_id = data[pos : pos + 4]
        chunk_size = int.from_bytes(data[pos + 4 : pos + 8], "little")
        if chunk_id == b"fmt ":
            if int.from_bytes(data[pos + 8 : pos + 10], "little") == 0xFFFE:
                data[pos + 8 : pos + 10] = b"\x01\x00"
            break
        pos += 8 + chunk_size + (chunk_size % 2)
    with wave.open(io.BytesIO(bytes(data))) as w:
        return _extract_wav(w)


def _extract_wav(w: wave.Wave_read) -> Tuple[array.array[int], int, int]:
    n_channels = w.getnchannels()
    sampwidth = w.getsampwidth()
    raw = w.readframes(w.getnframes())
    if sampwidth == 2:
        typecode = "h"
    elif sampwidth == 4:
        typecode = "i"
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth * 8}bit")
    buf = array.array(typecode)
    buf.frombytes(raw)
    if sys.byteorder == "big":
        buf.byteswap()
    return buf, n_channels, sampwidth


def _active_channels(flat: array.array[int], nch: int) -> List[int]:
    """Return list of channel indices with at least one non-zero sample."""
    return [ch for ch in range(nch) if any(flat[ch::nch])]


def compare_wav_files(reference_file: str, test_file: str, tolerance: int = 128) -> int:
    """Compare two WAV files sample-by-sample with active-channel detection and lag compensation."""
    ref_flat, ref_nch, ref_sw = _read_wav(reference_file)
    test_flat, test_nch, test_sw = _read_wav(test_file)

    if ref_sw != test_sw:
        raise ValueError(f"Sample width mismatch: ref={ref_sw * 8}bit test={test_sw * 8}bit")
    if ref_flat == test_flat:
        return 0

    # Select channels to compare. When counts differ, only channels that are
    # active (non-silent) in both files at the same index are compared.
    if ref_nch == test_nch:
        channels = list(range(ref_nch))
    else:
        channels = _active_channels(ref_flat, ref_nch)
        test_active = _active_channels(test_flat, test_nch)
        if len(channels) != len(test_active):
            raise ValueError(f"Channel mismatch: ref active={len(channels)} test active={len(test_active)}")
        channels = [ch for ch in channels if ch < test_nch]

    n_ref = len(ref_flat) // ref_nch
    n_test = len(test_flat) // test_nch

    # Align to first non-zero frame to compensate for leading silence
    ref_nz = next((i for i in range(n_ref) if any(ref_flat[i * ref_nch + ch] for ch in channels)), None)
    test_nz = next((i for i in range(n_test) if any(test_flat[i * test_nch + ch] for ch in channels)), None)

    ref_start = test_start = 0
    if ref_nz is not None and test_nz is not None:
        lag = test_nz - ref_nz
        if lag > 0:
            test_start = lag
        elif lag < 0:
            ref_start = -lag

    n_compare = min(n_ref - ref_start, n_test - test_start)
    violations = 0
    for ch in channels:
        ref_ch = ref_flat[ref_start * ref_nch + ch : (ref_start + n_compare) * ref_nch : ref_nch]
        test_ch = test_flat[test_start * test_nch + ch : (test_start + n_compare) * test_nch : test_nch]
        violations += sum(abs(r - t) > tolerance for r, t in zip(ref_ch, test_ch))
    return violations


def compare_yuv_files(reference_file: str, test_file: str, tolerance: int = 2, blocksize: int = 1024) -> int:
    """Compare two YUV files byte-by-byte within a tolerance, streaming in blocks."""
    violations = 0
    with open(reference_file, "rb") as ref_fh, open(test_file, "rb") as test_fh:
        ref_iter = iter(partial(ref_fh.read, blocksize), b"")
        test_iter = iter(partial(test_fh.read, blocksize), b"")
        for ref_block in ref_iter:
            test_block = next(test_iter, None)
            if test_block is None:
                raise ValueError("Test file is shorter than reference file")
            if len(ref_block) != len(test_block):
                raise ValueError("File size mismatch between reference and test")
            for i in range(len(ref_block)):
                if abs(ref_block[i] - test_block[i]) > tolerance:
                    violations += 1
        if next(test_iter, None) is not None:
            raise ValueError("Test file is longer than reference file")
    return violations


def find_by_ext(dest_dir: str, exts: List[str], excludes: Optional[List[str]] = None) -> Optional[str]:
    """Return name by file extension"""
    excludes = excludes or []
    candidates = []

    for ext in exts:
        for subdir, _, files in os.walk(dest_dir):
            for filename in files:
                excluded = False
                filepath = os.path.join(subdir, filename)
                if not filepath.endswith(ext) or "__MACOSX" in filepath:
                    continue
                for excl in excludes:
                    if excl in filepath:
                        excluded = True
                        break
                if not excluded:
                    candidates.append(filepath)

    if len(candidates) > 1:
        for candidate in candidates.copy():
            # Prioritize files with 'L0' in the name (for JCT-VC-SHVC)
            if "L0" in candidate.upper():
                return candidate
            # Prioritize files with 'norpt' in the name (for JVT-AVC_V1)
            # Special case only for CVSEFDFT3_Sony_E.zip and CVSE3_Sony_H.zip
            # Prioritize files with 'layer0' in the name (for JVET-VVC_draft6
            # checksum files)
            if "norpt" in candidate.lower() or "layer0" in candidate.lower():
                return candidate
            # Files with 'first_picture' in the name are kicked out of the list
            # (for JVET-VVC_draft6 checksum files)
            # Reverse logic (with not in and return) does not produce desired value
            if "first_picture" in candidate.lower():
                candidates.remove(candidate)

    # If none of the above cases is fulfilled, return the first candidate
    return candidates[0] if candidates else None


def _parse_pcm_channel(filename: str) -> Tuple[str, int]:
    """Return (channel_type, channel_number) from a PCM filename, or ('', 0) if unmatched."""
    match = re.search(r"_([fbsl])(\d+)\.pcm$", os.path.basename(filename).lower())
    if match:
        return match.group(1), int(match.group(2))
    return "", 0


def interleave_pcm_files(pcm_files: List[str], output_filepath: str) -> None:
    """Interleave per-channel PCM files (_fNN/_sNN/_bNN/_lNN) into a single multichannel raw PCM stream."""
    channel_order = {"f": 0, "s": 1, "b": 2, "l": 3}
    classified = [(f, *_parse_pcm_channel(f)) for f in pcm_files]
    sorted_files = [
        f
        for f, ch_type, ch_num in sorted(classified, key=lambda x: (channel_order.get(x[1], 99), x[2]))
        if ch_type in channel_order
    ]

    with contextlib.ExitStack() as stack:
        handles = [stack.enter_context(open(f, "rb")) for f in sorted_files]
        outfile = stack.enter_context(open(output_filepath, "wb"))
        while True:
            # Read one 16-bit sample per channel
            data = [f.read(2) for f in handles]
            if all(block == b"" for block in data):
                break

            for block in data:
                if block:
                    outfile.write(block)


def _linux_user_data_dir(appname: str) -> str:
    """Return data directory tied to the user"""
    path = os.environ.get("XDG_DATA_HOME", "")
    if not path.strip():
        path = os.path.expanduser("~/.local/share")
    return os.path.join(path, appname)


def _linux_site_data_dirs(appname: str) -> List[str]:
    """Return data directory shared by users"""
    path = os.environ.get("XDG_DATA_DIRS", "")
    if not path.strip():
        path = "/usr/local/share:/usr/share"
    paths = path.split(os.pathsep)
    return [os.path.join(p, appname) for p in paths]


def _win_user_data_dir(appname: str) -> str:
    """Return data directory"""
    path = os.path.expanduser(r"~\AppData\Local")
    return os.path.join(path, appname)


def _win_site_data_dirs(appname: str) -> List[str]:
    """Return data directory shared by users"""
    # On Windows always user_data_dir
    return [_win_user_data_dir(appname)]


if sys.platform == "win32":
    site_data_dirs = _win_site_data_dirs
    user_data_dir = _win_user_data_dir
else:
    site_data_dirs = _linux_site_data_dirs
    user_data_dir = _linux_user_data_dir
