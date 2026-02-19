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

import contextlib
import http.client
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from fluster.test_vector import TestVector
from fluster.utils import file_checksum

if TYPE_CHECKING:
    from fluster.test_suite import TestSuite

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


class _CorruptCacheError(Exception):
    """Raised by an extract worker when the cached archive is unusable.

    The worker runs in a multiprocessing.Pool subprocess and cannot mutate
    the parent's DownloadManager directly; it raises this instead so the
    parent can invalidate the URL and re-download on the next run.
    """

    def __init__(self, source_url: str, original: Exception):
        # Pass both args to Exception so __reduce__ pickles them and the
        # exception round-trips through multiprocessing.Pool's result queue.
        super().__init__(source_url, original)
        self.source_url = source_url
        self.original = original

    def __str__(self) -> str:
        return f"corrupt cache for {self.source_url}: {self.original}"


class DownloadWork:
    """Context passed to the per-test-vector extraction worker."""

    def __init__(
        self,
        out_dir: str,
        extract_all: bool,
        test_suite_name: str,
        archive_path: str,
        test_vector: Optional[TestVector] = None,
    ):
        self.out_dir = out_dir
        self.extract_all = extract_all
        self.test_suite_name = test_suite_name
        self.archive_path = archive_path
        self.test_vector = test_vector


class DownloadWorkSingleArchive(DownloadWork):
    """Context passed to the single-archive extraction worker."""

    def __init__(
        self,
        out_dir: str,
        extract_all: bool,
        test_suite_name: str,
        test_vectors: Dict[str, TestVector],
        archive_path: str,
        source_url: str,
        download_manager: "DownloadManager",
    ):
        super().__init__(out_dir, extract_all, test_suite_name, archive_path)
        self.test_vectors = test_vectors
        self.source_url = source_url
        self.download_manager = download_manager


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


def _download_single_test_vector(ctx: DownloadWork) -> None:
    """Extract a single test vector from a pre-downloaded archive.

    The DownloadManager always provides ctx.archive_path for extractable
    sources; non-extractable single-file sources skip this worker entirely
    (see DownloadManager.download_test_suite).

    Concurrency note: in the multi-TV branch this runs inside a
    multiprocessing.Pool subprocess. Subprocesses get a fork-time copy of
    the parent's DownloadManager, so any state mutation here (cache
    bookkeeping, invalidation, etc.) does NOT propagate back to the
    parent. Communicate failures by raising — the parent handles them via
    the Pool's error_callback (e.g. _CorruptCacheError → manager
    invalidation in DownloadManager.download_test_suite)."""
    if ctx.test_vector is None:
        raise ValueError("per-TV worker requires a test_vector")
    if not ctx.archive_path:
        raise ValueError("DownloadManager must provide archive_path")
    dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name, ctx.test_vector.name)
    os.makedirs(dest_dir, exist_ok=True)

    if is_extractable(ctx.archive_path):
        # Skip extraction if the target file is already on disk from a
        # previous run. Trusts presence as proof of content; users can
        # force re-extraction by removing the file (or the suite dir).
        extracted_path = os.path.join(dest_dir, ctx.test_vector.input_file)
        if not ctx.extract_all and os.path.exists(extracted_path):
            print(f"\tSkipping extraction of {ctx.test_vector.name} (already extracted)")
            return
        print(f"\tExtracting test vector {ctx.test_vector.name} to {dest_dir}")
        try:
            extract(
                ctx.archive_path,
                dest_dir,
                file=ctx.test_vector.input_file if not ctx.extract_all else None,
            )
        except (zipfile.BadZipFile, subprocess.CalledProcessError, OSError) as exc:
            # Worker runs in a multiprocessing.Pool subprocess (or here in
            # the main thread for the single-TV branch); raise so the
            # parent can call manager.invalidate(source_url).
            raise _CorruptCacheError(ctx.test_vector.source, exc) from exc
    else:
        # Raw (non-extractable) source file: move from the manager's cache
        # into the suite dir so it's stored only once. Non-extractable
        # files aren't shared across suites, so there's no dedup value in
        # keeping the cache copy.
        dest_path = os.path.join(dest_dir, os.path.basename(ctx.archive_path))
        if os.path.exists(dest_path):
            print(f"\tSkipping placement of {ctx.test_vector.name} (already exists)")
        else:
            print(f"\tPlacing test vector {ctx.test_vector.name} at {dest_path}")
            shutil.move(ctx.archive_path, dest_path)


def _download_single_archive(ctx: DownloadWorkSingleArchive) -> None:
    """Extract many test vectors from a pre-downloaded single archive.

    The DownloadManager always provides ctx.archive_path."""
    first_tv = ctx.test_vectors[next(iter(ctx.test_vectors))]
    dest_dir = os.path.join(ctx.out_dir, ctx.test_suite_name)
    os.makedirs(dest_dir, exist_ok=True)
    if not ctx.archive_path:
        raise ValueError("DownloadManager must provide archive_path")

    try:
        with zipfile.ZipFile(ctx.archive_path, "r") as zip_file:
            print(f"\tExtracting test vectors from {filename_from_url(first_tv.source)}")
            namelist = zip_file.namelist()
            for tv in ctx.test_vectors.values():
                # Skip extraction if the target file is already on disk
                # from a previous run. Trusts presence as proof of content.
                if os.path.exists(os.path.join(dest_dir, tv.input_file)):
                    continue
                if tv.input_file in namelist:
                    zip_file.extract(tv.input_file, dest_dir)
                else:
                    print(f"WARNING: test vector {tv.input_file} not found inside {filename_from_url(first_tv.source)}")
    except zipfile.BadZipFile as bad_zip_error:
        # Corrupt archive: ask the DownloadManager to invalidate its
        # cache entry so the next run re-downloads from scratch.
        ctx.download_manager.invalidate(ctx.source_url)
        raise BadArchiveError(f"{ctx.archive_path} could not be opened as zip file (invalidated)") from bad_zip_error


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

    def download_test_suite(
        self,
        test_suite: "TestSuite",
        jobs: int,
        out_dir: str,
        *,
        extract_all: bool = False,
    ) -> None:
        """Download all test vectors for *test_suite* using this manager.

        The manager owns the cache, retry budget, HTTP semaphore, and
        persistent pool, so download orchestration belongs here rather than
        on the TestSuite domain object.
        """
        os.makedirs(out_dir, exist_ok=True)
        unique_sources = {tv.source for tv in test_suite.test_vectors.values()}

        if (
            len(unique_sources) == 1
            and len(test_suite.test_vectors) > 1
            and is_extractable(filename_from_url(next(iter(unique_sources))))
        ):
            # Multiple test vectors all from the same archive.
            print(f"Downloading test suite {test_suite.name} using 1 job (single archive)")
            first_tv = next(iter(test_suite.test_vectors.values()))
            shared_archive_path = self.get(first_tv.source, first_tv.source_checksum)
            dwork_single = DownloadWorkSingleArchive(
                out_dir,
                extract_all,
                test_suite.name,
                test_suite.test_vectors,
                shared_archive_path,
                first_tv.source,
                self,
            )
            _download_single_archive(dwork_single)
        elif len(unique_sources) == 1 and len(test_suite.test_vectors) == 1:
            # Single test vector (extractable or raw).
            print(f"Downloading test suite {test_suite.name} using 1 job (single file)")
            single_tv = next(iter(test_suite.test_vectors.values()))
            single_tv_archive_path = self.get(single_tv.source, single_tv.source_checksum)
            dwork = DownloadWork(
                out_dir,
                extract_all,
                test_suite.name,
                single_tv_archive_path,
                single_tv,
            )
            try:
                _download_single_test_vector(dwork)
            except _CorruptCacheError as exc:
                self.invalidate(exc.source_url)
                raise BadArchiveError(
                    f"corrupt cache for {exc.source_url} (invalidated, re-run to retry)"
                ) from exc.original
            # The worker move()s non-extractable raw sources out of the cache
            # into the suite dir. Tell the manager so cleanup() doesn't later
            # try to remove a path it no longer owns.
            if not is_extractable(single_tv_archive_path):
                self.release(single_tv.source)
        else:
            # Multiple test vectors from distinct archives: pre-download all
            # unique URLs in parallel, then extract concurrently.
            source_paths: Dict[str, str] = {}
            unique_source_list = list(unique_sources)
            url_checksum: Dict[str, str] = {}
            for tv in test_suite.test_vectors.values():
                url_checksum.setdefault(tv.source, tv.source_checksum)

            # Fast path: every URL already cached (e.g. cross-suite phase-2
            # pre-download in Fluster.download_test_suites warmed the cache).
            cached_paths = {url: self.cached_path(url) for url in unique_source_list}
            if all(p is not None for p in cached_paths.values()):
                source_paths = {url: p for url, p in cached_paths.items() if p is not None}
            else:
                successes, persistent_errors = self.get_many(url_checksum)
                source_paths.update(successes)
                if persistent_errors:
                    for err_url, err_exc in persistent_errors:
                        print(f"Error pre-downloading {err_url}: {err_exc}")
                    raise RuntimeError(
                        f"{len(persistent_errors)} URL(s) failed pre-download for suite {test_suite.name}"
                    )

            print(f"Downloading test suite {test_suite.name} using {jobs} parallel jobs")
            error_occurred = False
            # Defer manager.invalidate() out of the Pool's result-handler
            # thread; do the actual disk work after pool.join() to avoid
            # serializing all failures behind a single lock + os.remove.
            corrupted_urls: List[str] = []
            with Pool(jobs) as pool:

                def _callback_error(err: Any) -> None:
                    nonlocal error_occurred
                    error_occurred = True
                    if isinstance(err, _CorruptCacheError):
                        corrupted_urls.append(err.source_url)
                        print(
                            f"\nCorrupt cached archive {err.source_url} "
                            f"(will invalidate after job drain). "
                            f"({err.original})\n"
                        )
                    else:
                        print(f"\nError downloading -> {err}\n")
                    pool.terminate()

                downloads = []
                for tv in test_suite.test_vectors.values():
                    archive_path = source_paths[tv.source]
                    dwork = DownloadWork(
                        out_dir,
                        extract_all,
                        test_suite.name,
                        archive_path,
                        tv,
                    )
                    downloads.append(
                        pool.apply_async(
                            _download_single_test_vector,
                            args=(dwork,),
                            error_callback=_callback_error,
                        )
                    )

                pool.close()
                pool.join()

            for corrupt_url in corrupted_urls:
                self.invalidate(corrupt_url)

            if error_occurred:
                sys.exit("Some download failed")
            else:
                for job in downloads:
                    if not job.successful():
                        sys.exit("Some download failed")

        print("All downloads finished")
