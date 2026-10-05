#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#
# Helper script to build the ISO/IEC 23008-6 MPEG-H 3D Audio reference decoder (3DAudioDecoder)
# Usage: build_mpegh_decoder.py <stamp_file>
#
# The source is downloaded by download_deps.py to contrib/MPEG-H_3DA_refSoft. It is built with its own CMake
# project, in a build directory inside the source tree (its CMake only works that way), and the binary is linked
# from the decoders directory.

import subprocess
import sys
from pathlib import Path


def main():
    stamp_file = Path(sys.argv[1]).resolve()
    root_dir = Path(__file__).parent.resolve().parent
    source_dir = root_dir / "contrib" / "MPEG-H_3DA_refSoft"
    decoders_dir = root_dir / "decoders"
    build_dir = source_dir / "build"

    print()
    print("=== Building MPEG-H 3D Audio decoder (3DAudioDecoder) ===")
    subprocess.run(["cmake", "-S", str(source_dir), "-B", str(build_dir), "-DCMAKE_BUILD_TYPE=Release"], check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--parallel"], check=True)

    # Binary location and extension vary by platform
    binary = next((b for b in build_dir.rglob("3DAudioDecoder*") if b.is_file() and b.suffix in ("", ".exe")), None)
    if binary is None:
        print("Error: 3DAudioDecoder not found in the build directory")
        sys.exit(1)
    decoders_dir.mkdir(parents=True, exist_ok=True)
    # 3DAudioDecoder runs the other executables built next to it, so link it instead of copying it
    link = decoders_dir / binary.name
    link.unlink(missing_ok=True)
    link.symlink_to(binary)
    stamp_file.touch()
    print("3DAudioDecoder built successfully!")


if __name__ == "__main__":
    main()
