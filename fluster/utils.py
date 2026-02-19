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
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import Any, Dict, List, Optional, Tuple, Type

TARBALL_EXTS = ("tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz")

# Pre-download thread-pool ceiling. HTTP concurrency is capped lower by
# DownloadManager's BoundedSemaphore (default 8); the surplus (2x) lets a
# waiting thread grab a freed slot without spinning up a new worker.
MAX_PREDOWNLOAD_POOL_WORKERS = 16

# Serialize concurrent progress-bar prints so lines don't garble under the
# ThreadPoolExecutor pre-download.
_print_lock = threading.Lock()


def _locked_print(msg: str) -> None:
    """Print *msg* under the shared print lock."""
    with _print_lock:
        print(msg)


def filename_from_url(url: str) -> str:
    """Return a safe filename from *url*, stripping query string and fragment.

    Plain os.path.basename on a URL keeps the query string (e.g. a signed
    GCS/S3 URL ending in "?X-Amz-Signature=..."), which then wrecks suffix
    checks like is_extractable() and leaves odd filenames on disk.

    Raises ValueError if the URL has no usable filename component (e.g.
    "https://host/" or "https://host"). Catching this here surfaces a
    clear error instead of an opaque IsADirectoryError further downstream.
    """
    filename = os.path.basename(urllib.parse.urlsplit(url).path)
    if not filename:
        raise ValueError(f"URL {url!r} has no filename component")
    return filename


class ChecksumMismatchError(Exception):
    """Downloaded file's checksum does not match the expected value."""


class BadArchiveError(Exception):
    """Downloaded archive is corrupt or unreadable."""


# Errors that make further retries pointless: the remote content genuinely
# differs from the expected checksum, so retrying just re-downloads the same
# wrong file.
_NON_RETRYABLE_DOWNLOAD_ERRORS = (ChecksumMismatchError,)


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

            _locked_print(f"\t{filename:<40} {progress_bar}")

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
    """Downloads a file to a directory with retries and full-jitter backoff.

    Between attempts it sleeps a uniform random delay in [1, 2**attempt)
    seconds, so the backoff window grows exponentially while the actual
    wait is randomized (AWS-style "full jitter")."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = filename_from_url(url)
    dest_path = os.path.join(dest_dir, filename)
    for attempt in range(max_retries):
        try:
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


class DownloadManager:
    """Centralized download manager that ensures each URL is downloaded at most once.

    Thread-safe: multiple threads may call get() concurrently. If the same URL
    is requested by multiple threads, only one performs the download while
    the others wait for the result. Archives managed by this class are cleaned
    up via cleanup() unless keep_file is set.
    """

    def __init__(
        self,
        cache_dir: str,
        verify: bool,
        keep_file: bool,
        retries: int,
        max_concurrent_downloads: int = 8,
        max_pool_workers: int = MAX_PREDOWNLOAD_POOL_WORKERS,
    ):
        self._cache_dir = cache_dir
        self._cache: Dict[str, str] = {}
        self._verify = verify
        self._keep_file = keep_file
        self._retries = retries
        self._managed_files: List[str] = []
        self._lock = threading.Lock()
        self._in_progress: Dict[str, threading.Event] = {}
        self._errors: Dict[str, Exception] = {}
        self._attempts: Dict[str, int] = {}
        # Cap concurrent HTTP downloads across all callers. Browsers typically
        # use 6-8 connections per host; keep that order of magnitude regardless
        # of how many extraction workers the CLI spins up.
        self._download_slots = threading.BoundedSemaphore(max(1, max_concurrent_downloads))
        # Single persistent pool that drives get_many(). The fan-out width is a
        # property of the manager, not of each batch; the BoundedSemaphore above
        # still caps actual HTTP concurrency underneath. Shut down in __exit__.
        workers = max(1, min(max_pool_workers, MAX_PREDOWNLOAD_POOL_WORKERS))
        self._pool: Optional[ThreadPoolExecutor] = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dl")

    def get_many(self, url_checksums: Dict[str, str]) -> Tuple[Dict[str, str], List[Tuple[str, Exception]]]:
        """Download many URLs concurrently via the manager's persistent pool.

        Returns (successes, errors): successes maps every URL that
        downloaded/cached OK to its local path; errors lists (url, exception)
        for every URL that failed. Never raises for per-URL failures — the
        caller decides policy. Fan-out width is fixed by the pool
        (max_pool_workers); the BoundedSemaphore caps actual HTTP concurrency
        underneath.
        """
        successes: Dict[str, str] = {}
        errors: List[Tuple[str, Exception]] = []
        if not url_checksums:
            return successes, errors
        if self._pool is None:
            raise RuntimeError("get_many() called after the manager was closed")
        futures = {self._pool.submit(self.get, url, checksum): url for url, checksum in url_checksums.items()}
        for future in as_completed(futures):
            url = futures[future]
            try:
                successes[url] = future.result()
            except Exception as exc:  # noqa: BLE001 - report every per-URL failure
                errors.append((url, exc))
        return successes, errors

    def get(self, url: str, source_checksum: str) -> str:
        """Download *url* once into the session cache dir and return the local path.

        Thread-safe. Concurrent calls for the same URL will block until
        the first caller finishes, then reuse the cached result.
        """
        while True:
            with self._lock:
                # Poison the URL only after exceeding the per-URL retry budget.
                if url in self._errors and self._attempts.get(url, 0) >= self._retries:
                    raise RuntimeError(
                        f"Download of {url} failed after {self._attempts[url]} attempts: {self._errors[url]}"
                    ) from self._errors[url]

                if url in self._cache and os.path.exists(self._cache[url]):
                    _locked_print(f"\tReusing cached download for {filename_from_url(url)}")
                    return self._cache[url]

                if url in self._in_progress:
                    event = self._in_progress[url]
                else:
                    event = threading.Event()
                    self._in_progress[url] = event
                    # Clear any previous error so this new attempt can run.
                    self._errors.pop(url, None)
                    break

            event.wait()

            with self._lock:
                # A concurrent attempt completed. If it failed and the budget
                # is exhausted, poison; otherwise loop and try again ourselves.
                if url in self._errors and self._attempts.get(url, 0) >= self._retries:
                    raise RuntimeError(
                        f"Download of {url} failed after {self._attempts[url]} attempts: {self._errors[url]}"
                    ) from self._errors[url]

        done_event: Optional[threading.Event] = None
        try:
            result, downloaded_now = self._do_download(url, source_checksum)
            with self._lock:
                self._cache[url] = result
                self._errors.pop(url, None)
                self._attempts.pop(url, None)
                if downloaded_now:
                    self._managed_files.append(result)
                done_event = self._in_progress.pop(url, None)
            return result
        except Exception as exc:
            with self._lock:
                self._errors[url] = exc
                if isinstance(exc, _NON_RETRYABLE_DOWNLOAD_ERRORS):
                    # Poison immediately — retrying won't help.
                    self._attempts[url] = self._retries
                else:
                    self._attempts[url] = self._attempts.get(url, 0) + 1
                done_event = self._in_progress.pop(url, None)
            raise
        finally:
            if done_event is not None:
                done_event.set()

    def _do_download(self, url: str, source_checksum: str) -> Tuple[str, bool]:
        """Perform the actual download/skip logic. Returns (path, downloaded_now)."""
        dest_path = os.path.join(self._cache_dir, filename_from_url(url))
        os.makedirs(self._cache_dir, exist_ok=True)

        # When the cached file's checksum matches the expected one, skip
        # redownload regardless of `verify`. For the CLI path, cleanup() wipes
        # the cache dir at end-of-run; for scripts (keep_file=True), the
        # checksum match is itself the safety gate.
        skip = False
        if os.path.exists(dest_path):
            if source_checksum == "__skip__":
                skip = True
            elif source_checksum == file_checksum(dest_path):
                skip = True
            elif self._verify and is_extractable(dest_path):
                os.remove(dest_path)

        if skip:
            _locked_print(f"\tSkipping download of {filename_from_url(url)} (already exists)")
        else:
            _locked_print(f"\tDownloading {filename_from_url(url)} from {url}")
            # Hold an HTTP slot only for the network transfer; the checksum
            # below runs unslotted (it needs no connection).
            with self._download_slots:
                # download() retries internally with backoff. Pass retries
                # straight through; the per-URL budget in get() is the outer
                # envelope. (Avoids the old retries**retries blow-up: -r 5
                # used to mean 3125 attempts per URL.)
                download(url, self._cache_dir, max_retries=self._retries)

            if source_checksum != "__skip__":
                checksum = file_checksum(dest_path)
                if source_checksum != checksum:
                    raise ChecksumMismatchError(
                        f"Checksum mismatch for {filename_from_url(url)}: {checksum} instead of '{source_checksum}'"
                    )

        return dest_path, not skip

    def is_poisoned(self, url: str) -> bool:
        """True if this URL has exhausted its retry budget and will fail on next get()."""
        with self._lock:
            return url in self._errors and self._attempts.get(url, 0) >= self._retries

    def cached_path(self, url: str) -> Optional[str]:
        """Return the cached path for *url* if present and on disk, else None.

        Read-only; never triggers a download or alters manager state. Useful
        for callers that want to skip a redundant get() round-trip when an
        earlier phase has already warmed the cache.
        """
        with self._lock:
            path = self._cache.get(url)
        if path is not None and os.path.exists(path):
            return path
        return None

    def invalidate(self, url: str) -> None:
        """Drop the cached download for *url* and delete the on-disk file.

        Use when a consumer detects the cached archive is unusable (e.g.
        a corrupt zip that passed the checksum). The next get() call will
        re-download from scratch.
        """
        with self._lock:
            path = self._cache.pop(url, None)
            # Forget tracking so cleanup() won't later try to remove the
            # re-downloaded file twice.
            if path and path in self._managed_files:
                self._managed_files.remove(path)
        if path and os.path.exists(path):
            with contextlib.suppress(OSError):
                os.remove(path)

    def release(self, url: str) -> None:
        """Forget the cached path for *url* without deleting the file.

        Use when a consumer has taken ownership of the cached file (e.g.
        moved it elsewhere). Differs from invalidate() in that no on-disk
        removal happens — the caller now owns the file and the manager
        forgets it. Only meaningful in the parent process; subprocess
        workers can't mutate the parent's manager state.
        """
        with self._lock:
            path = self._cache.pop(url, None)
            if path and path in self._managed_files:
                self._managed_files.remove(path)

    def __enter__(self) -> "DownloadManager":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        # Always tear the pool down so its threads never leak, even when an
        # exception is propagating (the file cleanup below is what we skip on
        # error, not the pool shutdown).
        self._shutdown_pool()
        # Skip file cleanup when an exception is propagating (especially
        # KeyboardInterrupt mid-download), so the user can resume on the
        # next run instead of starting over.
        if exc_type is None:
            self.cleanup()

    def _shutdown_pool(self) -> None:
        """Shut down the persistent download pool. Idempotent."""
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None

    def cleanup(self) -> None:
        """Remove downloaded archives unless keep_file was requested.

        Not safe against concurrent DownloadManager instances sharing the
        same cache_dir (across fluster processes). Each DownloadManager only
        tracks files it downloaded itself, so cross-process corruption is
        bounded, but callers running concurrent fluster sessions should
        either use --keep or point at separate resource dirs.
        """
        # Direct callers (not via __exit__) still need the pool reclaimed.
        self._shutdown_pool()
        if self._keep_file:
            return
        for path in self._managed_files:
            # Best-effort: a missing file (already removed) or one we can't
            # delete shouldn't abort cleanup of the rest. Suppressing OSError
            # also avoids a TOCTOU race against an exists() check.
            with contextlib.suppress(OSError):
                os.remove(path)
        self._managed_files.clear()
        # Best-effort: remove the cache dir if it is now empty. Fails quietly
        # if the dir still contains files (e.g., concurrent fluster instance).
        with contextlib.suppress(OSError):
            os.rmdir(self._cache_dir)


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
    """Load a WAV file and return (interleaved_samples, n_channels, sampwidth). Supports 16 and 32-bit PCM."""
    with wave.open(path, "rb") as w:
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
