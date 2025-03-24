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
import hashlib
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from threading import Lock
from typing import List, Optional

TARBALL_EXTS = ("tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz")

download_lock = Lock()


def download(url: str, dest_dir: str, max_retries: int = 5) -> None:
    """Downloads a file to a directory with a mutex lock to avoid conflicts and retries with exponential backoff."""
    for attempt in range(max_retries):
        try:
            with download_lock:
                with urllib.request.urlopen(url) as response:
                    dest_path = os.path.join(dest_dir, url.split("/")[-1])
                    with open(dest_path, "wb") as dest:
                        shutil.copyfileobj(response, dest)
            break
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 2**attempt)
                time.sleep(wait_time)
            else:
                print(f"Failed to download {url} after {max_retries} attempts.")


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
            if file:
                zip_file.extract(file, path=output_dir)
            else:
                zip_file.extractall(path=output_dir)
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


def interleave_pcm_files(pcm_files: List[str], output_filepath: str) -> None:
    """
    Interleaves PCM files with multichannel patterns (_*) in the correct channel ordering:
    1. Front channels (f00-f0X) in numerical order
    2. Side channels (s00-s0X) in numerical order, if present
    3. Back channels (b00-b0X) in numerical order
    4. LFE channel (l00) if present
    """

    front_channels = [f for f in pcm_files if "_f" in os.path.basename(f).lower()]
    side_channels = [f for f in pcm_files if "_s" in os.path.basename(f).lower()]
    back_channels = [f for f in pcm_files if "_b" in os.path.basename(f).lower()]
    lfe_channels = [f for f in pcm_files if "_l" in os.path.basename(f).lower()]

    front_channels.sort(key=_get_channel_number)
    side_channels.sort(key=_get_channel_number)
    back_channels.sort(key=_get_channel_number)
    lfe_channels.sort(key=_get_channel_number)

    sorted_files = front_channels + side_channels + back_channels + lfe_channels

    pcm_files_handles = [open(pcm_file, "rb") for pcm_file in sorted_files]

    with open(output_filepath, "wb") as outfile:
        while True:
            # Read one block (2 bytes for 16-bit PCM) from each file
            data = [f.read(2) for f in pcm_files_handles]

            if all(block == b"" for block in data):
                break

            for block in data:
                if block:
                    outfile.write(block)

    for file_handle in pcm_files_handles:
        file_handle.close()


def _get_channel_number(filename: str) -> int:
    """Return channel number from filename"""
    match = re.search(r"_[fbsl](\d+)\.pcm$", filename.lower())
    if match:
        return int(match.group(1))
    return 0


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
