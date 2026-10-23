#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#
# Helper script to build the ISO/IEC 14496-5 MPEG-4 Visual reference decoder (vm_dec)
# Usage: build_mpeg4_video_decoder.py <stamp_file>
#
# The source is downloaded by download_deps.py to contrib/MPEG-4_video_refSoft. It predates C++98, so it does not
# build as is with a current compiler. Instead of shipping a patched copy of the ISO sources, this script adapts the
# downloaded tree before running its own Makefile: line endings, the pre-standard iostream headers, and a few
# declarations that clash with the standard library. The binary is linked from the decoders directory.

import os
import re
import subprocess
import sys
from pathlib import Path

# Pre-standard headers that the sources include, mapped to their standard replacement
SHIM_HEADERS = {
    "fstream.h": "fstream",
    "iostream.h": "iostream",
    "istream.h": "istream",
    "ostream.h": "ostream",
    "iomanip.h": "iomanip",
    "ios.h": "ios",
    "strstream.h": "strstream",
}

# Force-included in every translation unit: the old sources use iostream names without the std:: prefix
COMPAT_HEADER = """\
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <strstream>

class CVideoObjectDecoder;
class CVideoObjectDecoderTPS;
class CEnhcBufferEncoder;

using std::cerr;
using std::cin;
using std::cout;
using std::dec;
using std::endl;
using std::ends;
using std::fixed;
using std::flush;
using std::fstream;
using std::hex;
using std::ifstream;
using std::ios;
using std::iostream;
using std::istream;
using std::istrstream;
using std::left;
using std::ofstream;
using std::oct;
using std::ostream;
using std::ostrstream;
using std::right;
using std::scientific;
using std::setfill;
using std::setprecision;
using std::setw;
using std::streambuf;
using std::streamoff;
using std::streampos;
using std::strstream;
using std::strstreambuf;
using std::ws;
"""

TEXT_SUFFIXES = {".c", ".cpp", ".h", ".hpp"}
TEXT_NAMES = {"Makefile", "unixmake"}

# Forward declarations that would clash with the std:: names brought in by the compat header
FORWARD_DECLARATION = re.compile(rb"^[ \t]*class[ \t]+(istream|ostream|ifstream|strstreambuf)[ \t]*;[ \t]*\n", re.M)
# "ios::bin" is the pre-standard spelling of "ios::binary"
IOS_BIN = re.compile(rb"\bios::bin\b")
CRLF = re.compile(rb"\r$", re.M)


def adapt_sources(source_dir):
    """Rewrite in place the files that do not build as downloaded. It is safe to run it more than once."""
    for path in source_dir.rglob("*"):
        if not path.is_file() or (path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_NAMES):
            continue
        original = path.read_bytes()
        data = CRLF.sub(b"", original)
        if path.suffix in TEXT_SUFFIXES:
            data = IOS_BIN.sub(b"ios::binary", FORWARD_DECLARATION.sub(b"", data))
        if data != original:
            path.write_bytes(data)


def write_shims(shims_dir):
    """Create the replacement headers and the compat header in shims_dir, which is added to the include path"""
    shims_dir.mkdir(exist_ok=True)
    for old_name, std_name in SHIM_HEADERS.items():
        (shims_dir / old_name).write_text(f"#include <{std_name}>\n")
    (shims_dir / "compat.h").write_text(COMPAT_HEADER)


def main():
    stamp_file = Path(sys.argv[1]).resolve()
    root_dir = Path(__file__).parent.resolve().parent
    source_dir = root_dir / "contrib" / "MPEG-4_video_refSoft"
    decoders_dir = root_dir / "decoders"

    print()
    print("=== Building MPEG-4 Visual reference decoder (vm_dec) ===")
    adapt_sources(source_dir)
    # The paths are relative to source_dir, where make runs, as make cannot handle spaces in the paths it receives
    write_shims(source_dir / "shims")
    (source_dir / "obj").mkdir(exist_ok=True)

    compiler = os.environ.get("CXX", "g++")
    compile_cmd = f"{compiler} -fpermissive -std=gnu++98 -fno-operator-names -w -Ishims -include shims/compat.h"
    subprocess.run(
        ["make", "-k", f"-j{os.cpu_count() or 1}", "vm_dec", f"CCC={compile_cmd}"], cwd=source_dir, check=True
    )

    binary = source_dir / "vm_dec"
    if not binary.is_file():
        print("Error: vm_dec not found after the build")
        sys.exit(1)
    decoders_dir.mkdir(parents=True, exist_ok=True)
    link = decoders_dir / "vm_dec"
    link.unlink(missing_ok=True)
    link.symlink_to(binary)
    stamp_file.touch()
    print("vm_dec built successfully!")


if __name__ == "__main__":
    main()
