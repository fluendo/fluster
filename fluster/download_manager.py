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

import hashlib
import os
import shutil
import sys
from dataclasses import dataclass, field
from multiprocessing import Pool
from typing import Any, Dict, List, Optional, Set

from fluster.utils import download, extract, file_checksum, filename_from_url, is_extractable


@dataclass
class _Destination:
    """A test vector that needs a downloaded source.

    ``suite_root`` is True for suites that share a single archive between
    several test vectors and extract it at the suite level
    (``resources/<suite>/<input_file>``); otherwise the source is extracted
    per test vector in ``resources/<suite>/<test_vector>/``.
    """

    suite_name: str
    test_vector_name: str
    input_file: str
    suite_root: bool = False


@dataclass
class _DownloadTask:
    """A unique source URL to download, with all destinations that need it."""

    source_url: str
    source_checksum: str
    destinations: List[_Destination] = field(default_factory=list)


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
        mirror: Optional[str] = None,
    ):
        self.out_dir = out_dir
        self.verify = verify
        self.extract_all = extract_all
        self.keep_file = keep_file
        self.retries = retries
        self.mirror = mirror

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
        suite_sources: Dict[str, Set[str]] = {}
        suite_vector_count: Dict[str, int] = {}
        for test_suite in test_suites:
            suite_sources[test_suite.name] = {tv.source for tv in test_suite.test_vectors.values()}
            suite_vector_count[test_suite.name] = len(test_suite.test_vectors)

        # Suites with a single source shared by several test vectors extract
        # the archive at the suite level. The decision is per suite: a source
        # shared between suites can be suite-level for one and per-vector for
        # another.
        root_suites = {
            name for name, sources in suite_sources.items() if len(sources) == 1 and suite_vector_count[name] > 1
        }

        source_map: Dict[str, _DownloadTask] = {}
        checksum_conflicts: Dict[str, List[str]] = {}
        for test_suite in test_suites:
            for tv_name, tv in test_suite.test_vectors.items():
                source = tv.source
                if source not in source_map:
                    source_map[source] = _DownloadTask(
                        source_url=source,
                        source_checksum=tv.source_checksum,
                    )
                else:
                    known_checksum = source_map[source].source_checksum
                    if known_checksum == "__skip__" and tv.source_checksum != "__skip__":
                        # Prefer a real checksum over an unset/__skip__ one.
                        source_map[source].source_checksum = tv.source_checksum
                    elif tv.source_checksum not in ("__skip__", known_checksum):
                        checksum_conflicts.setdefault(source, []).append(tv.source_checksum)
                source_map[source].destinations.append(
                    _Destination(
                        suite_name=test_suite.name,
                        test_vector_name=tv_name,
                        input_file=tv.input_file,
                        suite_root=test_suite.name in root_suites,
                    )
                )

        if checksum_conflicts:
            for source, others in checksum_conflicts.items():
                kept = source_map[source].source_checksum
                conflicts = ", ".join(sorted(set(others)))
                print(
                    f"ERROR: conflicting checksums for {source}: {kept} vs {conflicts} - "
                    f"the test-suite definitions disagree."
                )
            sys.exit(f"{len(checksum_conflicts)} URL(s) have conflicting checksums across the selected suites")

        if not source_map:
            print("No test vectors to download")
            return

        tasks = list(source_map.values())
        suite_names = sorted({ts.name for ts in test_suites})
        print(f"Downloading resources for test suites: {', '.join(suite_names)}")
        num_jobs = max(1, min(jobs, len(tasks)))
        print(f"Unique sources: {len(tasks)}, using {num_jobs} parallel job(s)")

        # Download all unique sources in parallel
        error_occurred = False

        with Pool(num_jobs) as pool:

            def _callback_error(err: Any) -> None:
                nonlocal error_occurred
                error_occurred = True
                # Do not call pool.terminate() here: this callback runs in the
                # result handler thread and terminating from it deadlocks
                # pool.join(). Let the remaining tasks finish, then bail out.
                print(f"\nError downloading -> {err}\n")

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
        """Download a unique source and distribute it to all its destinations.

        Extractable sources are extracted from the cached archive, either at
        the suite level or per test vector depending on each destination.
        Plain files are copied to every destination's test vector directory.
        Skips the download entirely if all destinations already have their
        files.

        Args:
            task: The download task with source URL and destination list.
        """
        source_filename = filename_from_url(task.source_url)
        is_extractable_file = is_extractable(source_filename)

        # Skip if all destinations already have their files
        if self.verify and self._all_destinations_satisfied(task, is_extractable_file):
            return

        # Use a hash of the URL to create a unique cache directory, avoiding
        # collisions when different URLs share the same filename basename.
        url_hash = hashlib.md5(task.source_url.encode()).hexdigest()
        cache_dir = os.path.join(self.cache_dir, url_hash)
        cache_path = os.path.join(cache_dir, source_filename)
        os.makedirs(cache_dir, exist_ok=True)

        if is_extractable_file:
            self._process_archive(task, cache_path, source_filename)
        else:
            self._process_plain_file(task, cache_path, source_filename)

    def _all_destinations_satisfied(self, task: _DownloadTask, is_extractable_file: bool) -> bool:
        """Check if all destinations for a task already have their files.

        Args:
            task: The download task to check.
            is_extractable_file: Whether the source file is extractable.

        Returns:
            True if all destinations are already satisfied and download can be skipped.
        """
        source_filename = filename_from_url(task.source_url)
        return all(
            self._destination_satisfied(task, destination, is_extractable_file, source_filename)
            for destination in task.destinations
        )

    def _destination_satisfied(
        self,
        task: _DownloadTask,
        destination: _Destination,
        is_extractable_file: bool,
        source_filename: str,
    ) -> bool:
        """Check if a destination already has the file(s) the source provides.

        Extractable destinations can only be verified when the expected
        archive member is known: with ``extract_all`` or an empty
        ``input_file`` the set of extracted files is unknown without
        re-extracting the archive, so the destination is never considered
        satisfied.

        Args:
            task: The download task.
            destination: Destination to check.
            is_extractable_file: Whether the source file is extractable.
            source_filename: Basename of the source URL.

        Returns:
            True if the destination is already satisfied.
        """
        if is_extractable_file:
            if self.extract_all or not destination.input_file:
                return False
            dest_dir = os.path.join(self.out_dir, destination.suite_name)
            if not destination.suite_root:
                dest_dir = os.path.join(dest_dir, destination.test_vector_name)
            return os.path.exists(os.path.join(dest_dir, destination.input_file))

        dest_path = os.path.join(
            self.out_dir,
            destination.suite_name,
            destination.test_vector_name,
            source_filename,
        )
        if not os.path.exists(dest_path):
            return False
        if task.source_checksum == "__skip__":
            return True
        return task.source_checksum == file_checksum(dest_path)

    def _download_to_cache(self, task: _DownloadTask, cache_path: str) -> bool:
        """Download a source file to the cache directory, with verification.

        Skips download if the file already exists in cache and checksum matches.

        Args:
            task: The download task.
            cache_path: Destination path in the cache.

        Returns:
            True once the file is present in the cache, either downloaded or reused.
        """
        if self.verify and os.path.exists(cache_path) and task.source_checksum == file_checksum(cache_path):
            return True

        # Remove corrupt cached file if present
        if os.path.exists(cache_path):
            os.remove(cache_path)

        print(f"\tDownloading source from {task.source_url}")
        cache_dir = os.path.dirname(cache_path)
        download(task.source_url, cache_dir, self.retries, mirror=self.mirror)

        # Verify checksum
        if task.source_checksum != "__skip__":
            checksum = file_checksum(cache_path)
            if task.source_checksum != checksum:
                raise Exception(
                    f"Checksum mismatch for {filename_from_url(task.source_url)}: "
                    f"{checksum} instead of '{task.source_checksum}'"
                )

        return True

    def _process_archive(self, task: _DownloadTask, cache_path: str, source_filename: str) -> None:
        """Process an archive source shared by one or more test vectors.

        Downloads the archive once and extracts it from the cache: at the
        suite level for destinations that need it there, and per test vector
        otherwise. The cached archive is removed at the end unless
        ``keep_file`` is set.

        Args:
            task: The download task.
            cache_path: Path to the cached archive file.
            source_filename: Basename of the source URL.
        """
        self._download_to_cache(task, cache_path)

        print(f"\tExtracting test vectors from {source_filename}")
        extracted_suite_roots: Set[str] = set()
        for destination in task.destinations:
            if self.verify and self._destination_satisfied(task, destination, True, source_filename):
                continue

            if destination.suite_root:
                # With extract_all the whole archive is extracted once per
                # suite, no matter how many test vectors share it.
                if self.extract_all and destination.suite_name in extracted_suite_roots:
                    continue
                extracted_suite_roots.add(destination.suite_name)
                self._extract_to_suite_root(destination, cache_path, source_filename)
            else:
                self._extract_to_test_vector(destination, cache_path)

        # Remove the archive from cache unless keep_file is set
        if not self.keep_file and os.path.exists(cache_path):
            os.remove(cache_path)

    def _extract_to_suite_root(self, destination: _Destination, cache_path: str, source_filename: str) -> None:
        """Extract an archive member into the test suite directory.

        Args:
            destination: Destination to extract to.
            cache_path: Path to the cached archive.
            source_filename: Basename of the source URL.
        """
        dest_dir = os.path.join(self.out_dir, destination.suite_name)
        os.makedirs(dest_dir, exist_ok=True)
        try:
            extract(cache_path, dest_dir, file=None if self.extract_all else destination.input_file)
        except FileNotFoundError:
            print(f"WARNING: test vector {destination.input_file} not found inside {source_filename}")

    def _extract_to_test_vector(self, destination: _Destination, cache_path: str) -> None:
        """Extract an archive member into its test vector directory.

        Args:
            destination: Destination to extract to.
            cache_path: Path to the cached archive.
        """
        dest_dir = os.path.join(self.out_dir, destination.suite_name, destination.test_vector_name)
        os.makedirs(dest_dir, exist_ok=True)
        print(f"\tExtracting test vector {destination.test_vector_name} to {dest_dir}")
        extract(
            cache_path,
            dest_dir,
            file=None if self.extract_all else destination.input_file,
        )

    def _process_plain_file(self, task: _DownloadTask, cache_path: str, source_filename: str) -> None:
        """Process a non-extractable source file (one per test vector).

        Downloads the file to the cache, then copies it to each destination's
        test vector directory.

        Args:
            task: The download task.
            cache_path: Path to the cached file.
            source_filename: Basename of the source URL.
        """
        self._download_to_cache(task, cache_path)

        for destination in task.destinations:
            if self.verify and self._destination_satisfied(task, destination, False, source_filename):
                continue
            dest_dir = os.path.join(self.out_dir, destination.suite_name, destination.test_vector_name)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(cache_path, os.path.join(dest_dir, source_filename))

        # Remove from cache
        if os.path.exists(cache_path):
            os.remove(cache_path)
