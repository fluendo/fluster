# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import hashlib
import os
import shutil
import subprocess
import urllib.request
import zipfile
import platform


TARBALL_EXTS = ('tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'tar.xz')


def download(url: str, dest_dir: str):
    '''Downloads a file to a directory'''
    with urllib.request.urlopen(url) as response:
        dest_path = os.path.join(dest_dir, url.split('/')[-1])
        with open(dest_path, 'wb') as dest:
            shutil.copyfileobj(response, dest)


def file_checksum(path: str) -> str:
    '''Calculates the checksum of a file reading chunks of 64KiB'''
    md5 = hashlib.md5()
    with open(path, 'rb') as file:
        while True:
            data = file.read(65536)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def run_command(command: list, verbose: bool = False, check: bool = True, timeout: int = None):
    '''Runs a command'''
    sout = subprocess.DEVNULL if not verbose else None
    serr = subprocess.DEVNULL if not verbose else None
    if verbose:
        print(f'\nRunning command \"{" ".join(command)}\"')
    subprocess.run(command, stdout=sout, stderr=serr,
                   check=check, timeout=timeout)


def is_extractable(filepath: str) -> bool:
    '''Checks is a file can be extracted from the its extension'''
    return filepath.endswith(TARBALL_EXTS) or filepath.endswith('.zip')


def extract(filepath: str, output_dir: str, file: str = None):
    '''Extracts a file to a directory'''
    if filepath.endswith(TARBALL_EXTS):
        subprocess.run(['tar', '-C', output_dir, '-xf',
                        filepath, file], check=True)
    elif filepath.endswith('.zip'):
        with zipfile.ZipFile(filepath, "r") as zip_file:
            if file:
                zip_file.extract(file, path=output_dir)
            else:
                zip_file.extractall(path=output_dir)
    else:
        raise Exception("Unknown tarball format %s" % filepath)


def normalize_binary_cmd(cmd: str) -> str:
    '''Return the OS-form binary'''
    if platform.system() == 'Windows':
        return cmd if cmd.endswith('.exe') else cmd + '.exe'
    if cmd.endswith('.exe'):
        return cmd.replace('.exe', '')
    return cmd


def normalize_path(path: str) -> str:
    '''Normalize the path to make it Unix-like'''
    if platform.system() == 'Windows':
        return path.replace('\\', '/')
    return path
