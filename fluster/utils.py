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
import shutil
import subprocess
import sys
import urllib.request
import zipfile
import platform
from typing import List, Optional


TARBALL_EXTS = ("tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz")


def download(url: str, dest_dir: str) -> None:
    """Downloads a file to a directory"""
    with urllib.request.urlopen(url) as response:
        dest_path = os.path.join(dest_dir, url.split("/")[-1])
        with open(dest_path, "wb") as dest:
            shutil.copyfileobj(response, dest)


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
) -> str:
    """Runs a command and returns std output trace"""
    serr = subprocess.DEVNULL if not verbose else subprocess.STDOUT
    if verbose:
        print(f'\nRunning command "{" ".join(command)}"')

    try:
        output = subprocess.check_output(
            command, stderr=serr, timeout=timeout, universal_newlines=True
        )
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
    """Checks is a file can be extracted from the its extension"""
    return filepath.endswith(TARBALL_EXTS) or filepath.endswith(".zip")


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
