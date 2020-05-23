# fluxion - testing framework for codecs
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


TARBALL_EXTS = ('tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'tar.xz')


def download(url: str, dest_dir: str):
    with urllib.request.urlopen(url) as response:
        dest_path = os.path.join(dest_dir, url.split('/')[-1])
        with open(dest_path, 'wb') as dest:
            shutil.copyfileobj(response, dest)


def file_checksum(path: str):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def is_extractable(filepath: str):
    return filepath.endswith(TARBALL_EXTS) or filepath.endswith('.zip')


def extract(filepath: str, output_dir: str):
    if filepath.endswith(TARBALL_EXTS):
        subprocess.run(['tar', '-C', output_dir, '-xf', filepath])
    elif filepath.endswith('.zip'):
        zf = zipfile.ZipFile(filepath, "r")
        zf.extractall(path=output_dir)
    else:
        raise Exception("Unknown tarball format %s" % filepath)
