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
import http.client
import io
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
import zipfile
from dataclasses import dataclass, field
from functools import partial
from multiprocessing import Pool
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

TARBALL_EXTS = ("tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz")

download_lock = Lock()


def create_enhanced_opener() -> urllib.request.OpenerDirector:
    """Creates an enhanced URL opener with custom headers and cookie support."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"),
        ("Accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
    ]
    return opener


def handle_iso_terms(opener: urllib.request.OpenerDirector, url: str) -> Any:
    """Handles ISO terms acceptance by submitting a form and returns the response content."""
    form_data = urllib.parse.urlencode({"ok": "I accept"}).encode("utf-8")
    req = urllib.request.Request(url, data=form_data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    response = opener.open(req)
    return response


def _format_eta(seconds: float) -> str:
    """Format ETA seconds into human-readable string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    return f"{hours}h {minutes}m"


def _format_bytes(bytes_size: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def _update_progress_bar(
    filename: str,
    downloaded: int,
    total_size: Optional[int],
    start_time: float,
    last_update_time: float,
    is_finished: bool = False,
) -> float:
    """Update and print progress bar, returns new last_update_time."""
    current_time = time.time()
    if current_time - last_update_time >= 5.0 or (total_size and downloaded >= total_size) or is_finished:
        elapsed = current_time - start_time
        if elapsed > 0:
            rate = downloaded / elapsed
            progress = 0.0
            if total_size:
                progress = downloaded / total_size
            else:
                if is_finished:
                    progress = 1.0
                    total_size = downloaded

            if rate > 0 and total_size and downloaded < total_size:
                eta_str = _format_eta((total_size - downloaded) / rate)
            else:
                eta_str = "--"
            filled = int(40 * progress)
            size_info = f"{_format_bytes(downloaded)}/{_format_bytes(total_size) if total_size else '???'}"
            if total_size:
                progress_bar = f"[{'=' * filled}{'-' * (40 - filled)}] {progress * 100:.1f}% "
                progress_bar += f"{size_info} | {_format_bytes(int(rate))}/s | ETA: {eta_str}"
            else:
                progress_bar = f"{size_info} | {_format_bytes(int(rate))}/s"

            print(f"\t{filename:<40} {progress_bar}")

            return current_time
    return last_update_time


def _download_simple(url: str, dest_path: str, filename: str, timeout: int, chunk_size: int) -> None:
    """Download file with progress tracking and retry logic"""
    opener = create_enhanced_opener()
    with opener.open(url, timeout=timeout) as response:
        url_handler = response
        if "text/html" in response.headers.get("content-type", "").lower():
            url_handler = handle_iso_terms(opener, url)

        content_length = url_handler.headers.get("content-length")
        total_size = int(content_length) if content_length else None

        with open(dest_path, "wb") as dest:
            downloaded = 0
            start_time = time.time()
            last_update_time = start_time
            while True:
                chunk = url_handler.read(chunk_size)
                if not chunk:
                    break
                dest.write(chunk)
                downloaded += len(chunk)
                last_update_time = _update_progress_bar(filename, downloaded, total_size, start_time, last_update_time)

            if not total_size and downloaded > 0:
                _update_progress_bar(filename, downloaded, total_size, start_time, last_update_time, is_finished=True)


def download(
    url: str,
    dest_dir: str,
    max_retries: int = 5,
    timeout: int = 300,
    chunk_size: int = 2048 * 2048,  # 4MB
) -> None:
    """Downloads a file to a directory with a mutex lock
    to avoid conflicts and retries with exponential backoff."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(url)
    dest_path = os.path.join(dest_dir, filename)
    for attempt in range(max_retries):
        try:
            with download_lock:
                _download_simple(url, dest_path, filename, timeout, chunk_size)
            break
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            OSError,
            IOError,
            ConnectionError,
            TimeoutError,
            http.client.IncompleteRead,
        ) as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)

            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 2**attempt)
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Failed to download {url} after {max_retries} attempts: {e}") from e


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


def is_extractable(filepath: str) -> bool:
    """Checks is a file can be extracted, based on its extension"""
    return filepath.endswith((*TARBALL_EXTS, ".zip", ".gz"))


def extract(filepath: str, output_dir: str, file: Optional[str] = None) -> None:
    """Extracts a file to a directory"""
    if filepath.endswith(TARBALL_EXTS):
        command = ["tar", "-C", output_dir, "-xf", filepath]
        if file:
            command.append(file)
        subprocess.run(command, check=True)
    elif filepath.endswith(".zip"):
        with zipfile.ZipFile(filepath, "r") as zip_file:
            prefix = os.path.basename(filepath) + "/"
            if file:
                # Find file with or without prefix
                target_file = next(
                    (member for member in zip_file.namelist() if member == file or member == prefix + file), None
                )
                if not target_file:
                    raise FileNotFoundError(f"There is no item named '{file}' in the archive")
                # Remove prefix if present
                final_name = target_file[len(prefix) :] if target_file.startswith(prefix) else target_file
                target_path = os.path.join(output_dir, final_name)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zip_file.open(target_file) as source, open(target_path, "wb") as dest:
                    shutil.copyfileobj(source, dest)
            else:
                # Extract all files, removing prefix if present
                for member in zip_file.namelist():
                    if member.endswith("/"):
                        continue
                    target = member[len(prefix) :] if member.startswith(prefix) else member
                    if not target:
                        continue
                    target_path = os.path.join(output_dir, target)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_file.open(member) as source, open(target_path, "wb") as dest:
                        shutil.copyfileobj(source, dest)
    elif filepath.endswith(".gz"):
        output_file = os.path.join(output_dir, os.path.basename(filepath[:-3]))
        command = ["gunzip", "-c", filepath]
        with open(output_file, "wb") as f:
            subprocess.run(command, check=True, stdout=f)
    else:
        raise Exception(f"Unknown tarball format {filepath}")


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


def compare_wav_files(reference_file: str, test_file: str, tolerance: int = 128) -> int:
    """Compare two WAV files sample-by-sample with active-channel detection and lag compensation."""
    ref_flat, ref_nch, ref_sw = _read_wav(reference_file)
    test_flat, test_nch, test_sw = _read_wav(test_file)
    n_ref = len(ref_flat) // ref_nch
    n_test = len(test_flat) // test_nch

    if ref_sw != test_sw:
        raise ValueError(f"Sample width mismatch: ref={ref_sw * 8}bit test={test_sw * 8}bit")

    # Fast path: byte-identical samples → zero violations (C-level comparison)
    if ref_flat == test_flat:
        return 0

    if ref_nch == test_nch:
        # Same channel layout: compare all channels directly
        active = list(range(ref_nch))
    else:
        # Different channel counts: select only active (non-silent) channels from reference
        active = [ch for ch in range(ref_nch) if any(ref_flat[ch::ref_nch])]
        if len(active) != test_nch:
            raise ValueError(f"Channel mismatch: ref active={len(active)} test={test_nch}")

    # Align to first non-zero frame to compensate for constant leading silence
    ref_nz = next((i for i in range(n_ref) if any(ref_flat[i * ref_nch + ch] for ch in active)), None)
    test_nz = next((i for i in range(n_test) if any(test_flat[i * test_nch + ai] for ai in range(test_nch))), None)

    ref_start = test_start = 0
    if ref_nz is not None and test_nz is not None:
        lag = test_nz - ref_nz
        if lag > 0:
            test_start = lag
        elif lag < 0:
            ref_start = -lag

    n_compare = min(n_ref - ref_start, n_test - test_start)
    violations = 0
    for ai, ach in enumerate(active):
        ref_ch = ref_flat[ref_start * ref_nch + ach : (ref_start + n_compare) * ref_nch : ref_nch]
        test_ch = test_flat[test_start * test_nch + ai : (test_start + n_compare) * test_nch : test_nch]
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


@dataclass
class _DownloadTask:
    """A unique source URL to download, with all destinations that need it.

    Each destination is a (test_suite_name, test_vector_name, input_file) tuple.
    """

    source_url: str
    source_checksum: str
    destinations: List[Tuple[str, str, str]] = field(default_factory=list)


class DownloadManager:
    """Manages downloading test suite resources with URI deduplication and parallel downloads.

    Downloads each unique source URL once to a cache directory, then distributes
    the files to each test suite's destination directory. Supports both single-file
    test vectors and archives containing multiple test vectors.
    """

    CACHE_DIR = ".cache"

    def __init__(
        self,
        out_dir: str,
        verify: bool = True,
        extract_all: bool = False,
        keep_file: bool = False,
        retries: int = 2,
    ):
        self.out_dir = out_dir
        self.verify = verify
        self.extract_all = extract_all
        self.keep_file = keep_file
        self.retries = retries

    @property
    def cache_dir(self) -> str:
        """Path to the shared download cache directory."""
        return os.path.join(self.out_dir, self.CACHE_DIR)

    def download(self, test_suites: List[Any], jobs: int) -> None:
        """Download resources for multiple test suites.

        Collects all test vectors from all suites, deduplicates by source URL,
        then downloads each unique source in parallel and distributes files
        to their respective test suite directories.

        Args:
            test_suites: List of TestSuite instances to download resources for.
            jobs: Number of parallel download jobs.
        """
        os.makedirs(self.out_dir, exist_ok=True)

        # Collect all test vectors and group by source URL (deduplication)
        source_map: Dict[str, _DownloadTask] = {}
        for test_suite in test_suites:
            for tv_name, tv in test_suite.test_vectors.items():
                source = tv.source
                if source not in source_map:
                    source_map[source] = _DownloadTask(
                        source_url=source,
                        source_checksum=tv.source_checksum,
                    )
                source_map[source].destinations.append((test_suite.name, tv_name, tv.input_file))

        if not source_map:
            print("No test vectors to download")
            return

        tasks = list(source_map.values())
        suite_names = sorted({ts.name for ts in test_suites})
        print(f"Downloading resources for test suites: {', '.join(suite_names)}")
        print(f"Unique sources: {len(tasks)}, using {min(jobs, len(tasks))} parallel job(s)")

        # Download all unique sources in parallel
        error_occurred = False
        num_jobs = max(1, min(jobs, len(tasks)))

        with Pool(num_jobs) as pool:

            def _callback_error(err: Any) -> None:
                nonlocal error_occurred
                error_occurred = True
                print(f"\nError downloading -> {err}\n")
                pool.terminate()

            results = []
            for task in tasks:
                results.append(
                    pool.apply_async(
                        self._process_task,
                        args=(task,),
                        error_callback=_callback_error,
                    )
                )

            pool.close()
            pool.join()

        if error_occurred:
            sys.exit("Some download failed")

        for result in results:
            if not result.successful():
                sys.exit("Some download failed")

        # Clean up cache directory
        if not self.keep_file and os.path.isdir(self.cache_dir):
            shutil.rmtree(self.cache_dir)

        print("All downloads finished")

    def download_test_suite(self, test_suite: Any, jobs: int) -> None:
        """Download resources for a single test suite.

        Convenience wrapper around :meth:`download`.

        Args:
            test_suite: TestSuite instance to download.
            jobs: Number of parallel download jobs.
        """
        self.download([test_suite], jobs)

    def _process_task(self, task: _DownloadTask) -> None:
        """Download a unique source and distribute to all its destinations.

        Determines whether the source is an archive (extractable with multiple
        destinations) or individual file(s), then downloads, verifies, extracts,
        and copies appropriately. Skips the download entirely if all destination
        files already exist with correct checksums.

        Args:
            task: The download task with source URL and destination list.
        """
        source_filename = os.path.basename(task.source_url)
        is_extractable_file = is_extractable(source_filename)

        # Determine strategy: archive (extractable source shared by multiple
        # vectors) vs individual (one source per vector or single vector)
        is_archive = is_extractable_file and len(task.destinations) > 1

        # Skip if all destinations already have their files with correct checksums
        if self.verify and self._all_destinations_satisfied(task, is_extractable_file, is_archive):
            return

        # Use a hash of the URL to create a unique cache directory, avoiding
        # collisions when different URLs share the same filename basename.
        url_hash = hashlib.md5(task.source_url.encode()).hexdigest()
        cache_dir = os.path.join(self.cache_dir, url_hash)
        cache_path = os.path.join(cache_dir, source_filename)
        os.makedirs(cache_dir, exist_ok=True)

        if is_archive:
            self._process_archive(task, cache_path, source_filename)
        else:
            self._process_individual(task, cache_path, source_filename, is_extractable_file)

    def _all_destinations_satisfied(self, task: _DownloadTask, is_extractable_file: bool, is_archive: bool) -> bool:
        """Check if all destination files for a task already exist with correct checksums.

        Args:
            task: The download task to check.
            is_extractable_file: Whether the source file is extractable.
            is_archive: Whether the task is an archive task.

        Returns:
            True if all destinations are already satisfied and download can be skipped.
        """
        source_filename = os.path.basename(task.source_url)
        skip_checksum = task.source_checksum == "__skip__"

        if is_archive:
            for suite_name, _tv_name, input_file in task.destinations:
                dest_path = os.path.join(self.out_dir, suite_name, input_file)
                if not os.path.exists(dest_path):
                    return False
        else:
            for suite_name, tv_name, _input_file in task.destinations:
                dest_dir = os.path.join(self.out_dir, suite_name, tv_name)
                dest_path = os.path.join(dest_dir, source_filename)

                if is_extractable_file:
                    input_file = _input_file
                    if self.extract_all or not input_file:
                        if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
                            return False
                    else:
                        extracted_path = os.path.join(dest_dir, input_file)
                        if not os.path.exists(extracted_path):
                            return False
                else:
                    if not os.path.exists(dest_path):
                        return False
                    if not skip_checksum and task.source_checksum != file_checksum(dest_path):
                        return False

        return True

    def _download_to_cache(self, task: _DownloadTask, cache_path: str) -> bool:
        """Download a source file to the cache directory, with verification.

        Skips download if the file already exists in cache and checksum matches.

        Args:
            task: The download task.
            cache_path: Destination path in the cache.

        Returns:
            True if the file was downloaded (or already present), False if skipped.
        """
        if self.verify and os.path.exists(cache_path) and task.source_checksum == file_checksum(cache_path):
            return True

        # Remove corrupt cached file if present
        if os.path.exists(cache_path):
            os.remove(cache_path)

        print(f"\tDownloading source from {task.source_url}")
        cache_dir = os.path.dirname(cache_path)
        download(task.source_url, cache_dir, self.retries**self.retries)

        # Verify checksum
        if task.source_checksum != "__skip__":
            checksum = file_checksum(cache_path)
            if task.source_checksum != checksum:
                raise Exception(
                    f"Checksum mismatch for {os.path.basename(task.source_url)}: "
                    f"{checksum} instead of '{task.source_checksum}'"
                )

        return True

    def _process_archive(self, task: _DownloadTask, cache_path: str, source_filename: str) -> None:
        """Process an archive source containing multiple test vectors.

        Downloads the archive once, then extracts each destination's input_file
        into the corresponding test suite directory.

        Args:
            task: The download task.
            cache_path: Path to the cached archive file.
            source_filename: Basename of the source URL.
        """
        self._download_to_cache(task, cache_path)

        print(f"\tExtracting test vectors from {source_filename}")
        for suite_name, _tv_name, input_file in task.destinations:
            dest_dir = os.path.join(self.out_dir, suite_name)
            os.makedirs(dest_dir, exist_ok=True)
            try:
                extract(cache_path, dest_dir, file=input_file)
            except FileNotFoundError:
                print(f"WARNING: test vector {input_file} not found inside {source_filename}")

        # Remove the archive from cache unless keep_file is set
        if not self.keep_file and os.path.exists(cache_path):
            os.remove(cache_path)

    def _process_individual(
        self,
        task: _DownloadTask,
        cache_path: str,
        source_filename: str,
        is_extractable_file: bool,
    ) -> None:
        """Process an individual source file (one per test vector).

        Downloads the file to cache, then copies it to each destination's
        test vector subdirectory. If extractable, extracts the input file
        and removes the archive.

        Args:
            task: The download task.
            cache_path: Path to the cached file.
            source_filename: Basename of the source URL.
            is_extractable_file: Whether the source file can be extracted.
        """
        self._download_to_cache(task, cache_path)

        for suite_name, tv_name, input_file in task.destinations:
            dest_dir = os.path.join(self.out_dir, suite_name, tv_name)
            dest_path = os.path.join(dest_dir, source_filename)
            os.makedirs(dest_dir, exist_ok=True)

            # Check if already correctly downloaded at the destination
            if self.verify and os.path.exists(dest_path) and task.source_checksum == file_checksum(dest_path):
                if is_extractable_file and not self.keep_file:
                    os.remove(dest_path)
                continue

            # Copy from cache to destination
            shutil.copy2(cache_path, dest_path)

            if is_extractable_file:
                print(f"\tExtracting test vector {tv_name} to {dest_dir}")
                extract(
                    dest_path,
                    dest_dir,
                    file=input_file if not self.extract_all else None,
                )
                if not self.keep_file:
                    os.remove(dest_path)

        # Remove from cache
        if os.path.exists(cache_path):
            os.remove(cache_path)
