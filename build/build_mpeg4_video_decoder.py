#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#
# Helper script to build the ISO/IEC 14496-5 MPEG-4 Visual reference decoder (vm_dec)
# Usage: build_mpeg4_video_decoder.py <stamp_file>
#
# The source is downloaded and adapted for current compilers by download_deps.py, in contrib/MPEG-4_video_refSoft.
# This script runs its own Makefile and links the binary from the decoders directory.

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    stamp_file = Path(sys.argv[1]).resolve()
    root_dir = Path(__file__).parent.resolve().parent
    source_dir = root_dir / "contrib" / "MPEG-4_video_refSoft"
    decoders_dir = root_dir / "decoders"

    print()
    print("=== Building MPEG-4 Visual reference decoder (vm_dec) ===")
    if shutil.which("make") is None:
        print("Error: make not found")
        sys.exit(1)

    # The paths are relative to source_dir, where make runs, as make cannot handle spaces in the paths it receives
    compiler = os.environ.get("CXX", "g++")
    flags = ["-fpermissive", "-std=gnu++98", "-fno-operator-names", "-w", "-Ishims", "-include", "shims/compat.h"]
    if "clang" in subprocess.run([compiler, "--version"], capture_output=True, text=True, check=True).stdout:
        # What GCC accepts with -fpermissive is an error for clang, unless it is told that it is Microsoft code
        flags.append("-fms-extensions")
    if platform.system() == "Darwin":
        # macOS has no malloc.h
        flags.append("-I" + os.path.relpath(root_dir / "build" / "compat" / "macos", source_dir))
    compile_cmd = " ".join([compiler, *flags])
    subprocess.run(
        ["make", "-k", f"-j{os.cpu_count() or 1}", "vm_dec", f"CCC={compile_cmd}"], cwd=source_dir, check=True
    )

    # The extension varies by platform (vm_dec.exe with MinGW)
    binary = next((b for b in (source_dir / "vm_dec", source_dir / "vm_dec.exe") if b.is_file()), None)
    if binary is None:
        print("Error: vm_dec not found after the build")
        sys.exit(1)
    decoders_dir.mkdir(parents=True, exist_ok=True)
    link = decoders_dir / binary.name
    link.unlink(missing_ok=True)
    link.symlink_to(binary)
    stamp_file.touch()
    print("vm_dec built successfully!")


if __name__ == "__main__":
    main()
