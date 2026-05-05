#!/usr/bin/env python3
# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# Helper script to build ISO reference decoders
# Usage: build_iso_decoders.py <build_dir> <cflags> <ldflags> <decoders...>
#
# Arguments:
#   build_dir           - Meson build directory
#   cflags              - Extra CFLAGS to pass to compiler
#   ldflags             - Extra LDFLAGS to pass to linker
#   decoders...         - Space-separated list of decoders to build (or 'all')
#
# Supported decoders:
#   mpeg4-aac      - MPEG-4 AAC decoder (mp4audec_mc)
#   mpeg4-aac-er   - MPEG-4 AAC Error Resilient decoder (mp4audec)
#   all            - Build all decoders

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def find_file(search_dir, filename):
    """Find a file in directory tree"""
    for root, dirs, files in os.walk(search_dir):
        if filename in files:
            return Path(root) / filename
    return None


def should_build(decoder, decoders_list):
    """Check if a decoder should be built"""
    return "all" in decoders_list or decoder in decoders_list


def run_make(target, cwd, env):
    """Run make with the given target"""
    try:
        subprocess.run(["make", "clean"], cwd=cwd, env=env, check=False, capture_output=True)
        result = subprocess.run(
            ["make", target],
            cwd=cwd,
            env=env,
            check=True,
            capture_output=False,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error building {target}: {e}")
        return False


def build_mpeg4_aac(mpeg4_dir, decoders_dir, env):
    """Build MPEG-4 AAC decoder (mp4audec_mc)"""
    print()
    print("=== Building MPEG-4 AAC decoder (mp4audec_mc) ===")
    mp4mcdec_dir = mpeg4_dir / "mp4mcDec"
    env["MAKELEVEL"] = "0"
    if run_make("mp4audec_mc", mp4mcdec_dir, env):
        # Binary location varies by platform
        for binary in (mpeg4_dir / "bin").rglob("mp4audec_mc"):
            if binary.is_file():
                shutil.copy2(binary, decoders_dir / "mp4audec_mc")
                break
        print("mp4audec_mc built successfully!")
        return True
    else:
        print("Failed to build mp4audec_mc")
        return False


def build_mpeg4_aac_er(mpeg4_dir, decoders_dir, env):
    """Build MPEG-4 AAC Error Resilient decoder (mp4audec)"""
    print()
    print("=== Building MPEG-4 AAC Error Resilient decoder (mp4audec) ===")
    mp4audvm_dir = mpeg4_dir / "mp4AudVm_Rewrite"
    env["MAKELEVEL"] = "0"
    if run_make("mp4audec", mp4audvm_dir, env):
        # Binary location varies by platform
        for binary in (mpeg4_dir / "bin").rglob("mp4audec"):
            if binary.is_file():
                shutil.copy2(binary, decoders_dir / "mp4audec")
                break
        print("mp4audec built successfully!")
        return True
    else:
        print("Failed to build mp4audec")
        return False


def main():
    # Parse arguments
    if len(sys.argv) < 4:
        print("Usage: build_iso_decoders.py <build_dir> <cflags> <ldflags> <decoders...>")
        sys.exit(1)

    build_dir = Path(sys.argv[1]).resolve()
    cflags_extra = sys.argv[2]
    ldflags_extra = sys.argv[3]
    decoders_arg = sys.argv[4] if len(sys.argv) > 4 else "all"
    decoders_list = decoders_arg.split()

    # Get script directory and calculate paths
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent

    # Set directory paths
    contrib_dir = root_dir / "contrib"
    decoders_dir = root_dir / "decoders"
    isobmff_dir = root_dir / "subprojects" / "isobmff"

    # Auto-detect MP4OSMACROS_SUBDIR based on platform
    system = platform.system()
    if system == "Darwin":
        mp4osmacros_subdir = "macosx"
    elif system == "Linux":
        mp4osmacros_subdir = "linux"
    elif system == "Windows":
        mp4osmacros_subdir = "w32"
    else:
        mp4osmacros_subdir = "linux"

    # Create decoders directory
    decoders_dir.mkdir(parents=True, exist_ok=True)

    print("=== ISO Reference Decoders Build Script ===")
    print(f"Contrib directory: {contrib_dir}")
    print(f"Decoders directory: {decoders_dir}")
    print(f"isobmff directory: {isobmff_dir}")
    print(f"MP4OSMacros subdir: {mp4osmacros_subdir}")
    print(f"Build directory: {build_dir}")
    print(f"CFLAGS: {cflags_extra if cflags_extra else 'default'}")
    print(f"LDFLAGS: {ldflags_extra if ldflags_extra else 'default'}")
    print(f"Decoders to build: {' '.join(decoders_list)}")
    print()

    # Setup CFLAGS/LDFLAGS for MPEG-4 AAC dependencies
    mpeg4_dir = contrib_dir / "C050470e_Electronic_inserts" / "audio" / "natural"

    # ISOBMFF library
    if not isobmff_dir.exists():
        print(f"Error: isobmff subproject not found at {isobmff_dir}")
        print("Enable it with: meson configure builddir -Disobmff=true")
        sys.exit(1)

    # Add isobmff include paths (from source directory)
    cflags_extra += f" -I{isobmff_dir}/IsoLib/libisomediafile/src"
    cflags_extra += f" -I{isobmff_dir}/IsoLib/libisomediafile/{mp4osmacros_subdir}"

    # Find the built library in the build directory
    isobmff_build_dir = build_dir / "subprojects" / "isobmff"
    isobmff_lib = find_file(isobmff_build_dir, "liblibisomediafile.a")
    if not isobmff_lib:
        print("Error: isobmff library not found in build directory")
        print(f"Expected at: {isobmff_build_dir}/liblibisomediafile.a")
        sys.exit(1)
    print(f"Using isobmff library: {isobmff_lib}")

    isobmff_lib_dir = isobmff_lib.parent
    # Note: The library is named liblibisomediafile.a but we link with -lisomediafile
    # Create a symlink if needed
    libisomediafile_symlink = isobmff_lib_dir / "libisomediafile.a"
    if not libisomediafile_symlink.exists():
        try:
            libisomediafile_symlink.symlink_to("liblibisomediafile.a")
        except (OSError, NotImplementedError):
            # On Windows, copy instead of symlink
            shutil.copy2(isobmff_lib, libisomediafile_symlink)
    ldflags_extra += f" -L{isobmff_lib_dir}"

    # libtsp library
    # Find libtsp library built by meson
    libtsp_lib = find_file(build_dir / "subprojects" / "libtsp-v7r0", "libtsp.a")
    if not libtsp_lib:
        print("Error: libtsp library not found in build directory")
        print(f"Expected at: {build_dir}/subprojects/libtsp-v7r0/libtsp.a")
        sys.exit(1)
    print(f"Using libtsp library: {libtsp_lib}")

    # Find libtsp include directory
    libtsp_src = root_dir / "subprojects" / "libtsp-v7r0"
    if not (libtsp_src / "include").exists():
        print(f"Error: libtsp headers not found at {libtsp_src}/include")
        sys.exit(1)
    libtsp_inc = libtsp_src / "include"
    print(f"Using libtsp headers: {libtsp_inc}")

    # Add libtsp include paths
    cflags_extra += f" -I{libtsp_inc}"

    # Add libtsp library path
    libtsp_lib_dir = libtsp_lib.parent
    ldflags_extra += f" -L{libtsp_lib_dir}"

    # Setup environment for makefiles
    env = os.environ.copy()
    env["CFLAGS"] = cflags_extra.strip()
    env["LDFLAGS"] = ldflags_extra.strip()

    # Export MPEG-4 AAC makefile variables
    # These are expected by the ISO reference software makefiles
    env["ISOMP4_PATH"] = str(isobmff_lib_dir)
    env["ISOMP4_NAME"] = "isomediafile"
    env["AFSP_INCLUDE_PATH"] = str(libtsp_inc)
    env["AFSP_LIBRARY_PATH"] = str(libtsp_lib_dir)

    print(f"CFLAGS: {env['CFLAGS']}")
    print(f"LDFLAGS: {env['LDFLAGS']}")
    print(f"ISOMP4_PATH: {env['ISOMP4_PATH']}")
    print(f"ISOMP4_NAME: {env['ISOMP4_NAME']}")
    print(f"AFSP_INCLUDE_PATH: {env['AFSP_INCLUDE_PATH']}")
    print(f"AFSP_LIBRARY_PATH: {env['AFSP_LIBRARY_PATH']}")

    print()
    print("=== Preparing MPEG-4 AAC build environment ===")

    # Create output directories
    (mpeg4_dir / "lib").mkdir(parents=True, exist_ok=True)
    (mpeg4_dir / "bin").mkdir(parents=True, exist_ok=True)

    # Build decoders
    if should_build("mpeg4-aac", decoders_list):
        if not build_mpeg4_aac(mpeg4_dir, decoders_dir, env):
            sys.exit(1)

    if should_build("mpeg4-aac-er", decoders_list):
        if not build_mpeg4_aac_er(mpeg4_dir, decoders_dir, env):
            sys.exit(1)

    print()
    print("=== ISO Reference Decoders build complete ===")


if __name__ == "__main__":
    main()
