#!/bin/bash
# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# Helper script to build ISO reference decoders
# Usage: build_iso_decoders.sh <contrib_dir> <decoders_dir> <isobmff_dir> <mp4osmacros_subdir> <scripts_dir> <build_dir> <cflags> <ldflags> [decoders...]
#
# Supported decoders:
#   mpeg4-aac      - MPEG-4 AAC decoder (mp4audec_mc)
#   mpeg4-aac-er   - MPEG-4 AAC Error Resilient decoder (mp4audec)
#   all            - Build all decoders
#

set -e

# Convert relative paths to absolute paths
CONTRIB_DIR="$(cd "$1" && pwd)"
DECODERS_DIR="$(mkdir -p "$2" && cd "$2" && pwd)"
ISOBMFF_DIR="$(cd "$3" && pwd)"
MP4OSMACROS_SUBDIR="$4"
SCRIPTS_DIR="$(cd "$5" && pwd)"
BUILD_DIR="$(cd "$6" && pwd)"
CFLAGS_EXTRA="$7"
LDFLAGS_EXTRA="$8"
shift 8

# Default to all if no decoders specified
if [ $# -eq 0 ]; then
    DECODERS="all"
else
    DECODERS="$*"
fi

# Check if a decoder is requested
should_build() {
    local decoder="$1"
    if [[ "$DECODERS" == *"all"* ]] || [[ "$DECODERS" == *"$decoder"* ]]; then
        return 0
    fi
    return 1
}

# Determine if we need AAC support (requires isobmff and libtsp)
needs_aac_support() {
    should_build "mpeg4-aac" || should_build "mpeg4-aac-er"
}

echo "=== ISO Reference Decoders Build Script ==="
echo "Contrib directory: $CONTRIB_DIR"
echo "Decoders directory: $DECODERS_DIR"
echo "isobmff directory: $ISOBMFF_DIR"
echo "Scripts directory: $SCRIPTS_DIR"
echo "Build directory: $BUILD_DIR"
echo "CFLAGS: ${CFLAGS_EXTRA:-default}"
echo "LDFLAGS: ${LDFLAGS_EXTRA:-default}"
echo "Decoders to build: $DECODERS"
echo ""

mkdir -p "$DECODERS_DIR"

# Check if libtsp library is available for AAC decoders
LIBTSP_LIB=""
LIBTSP_INC=""
if [ ! -d "$ISOBMFF_DIR" ]; then
    echo "Error: isobmff subproject not found at $ISOBMFF_DIR"
    echo "Enable it with: meson configure builddir -Disobmff=true"
    exit 1
fi

# Find libtsp library built by meson
LIBTSP_LIB=$(find "$BUILD_DIR/subprojects/libtsp-v7r0" -name "libtsp.a" 2>/dev/null | head -1)
if [ -z "$LIBTSP_LIB" ]; then
    echo "Error: libtsp library not found in build directory"
    echo "Expected at: $BUILD_DIR/subprojects/libtsp-v7r0/libtsp.a"
    exit 1
fi
echo "Using libtsp library: $LIBTSP_LIB"

# Find libtsp include directory
LIBTSP_SRC=$(dirname "$BUILD_DIR")/subprojects/libtsp-v7r0
if [ ! -d "$LIBTSP_SRC/include" ]; then
    echo "Error: libtsp headers not found at $LIBTSP_SRC/include"
    exit 1
fi
LIBTSP_INC="$LIBTSP_SRC/include"
echo "Using libtsp headers: $LIBTSP_INC"

# MPEG-4 AAC decoder
if should_build "mpeg4-aac"; then
    echo ""
    echo "=== Building MPEG-4 AAC decoder (mp4audec_mc) ==="

    MPEG4_DIR="$CONTRIB_DIR/C050470e_Electronic_inserts/audio/natural"
    MPEG4_IMPORT="$MPEG4_DIR/import"

    # Apply Darwin patches to MPEG-4 makefile system
    PLATFORM_MK="$MPEG4_DIR/general/makefile.platform"
    if [ -f "$PLATFORM_MK" ] && ! grep -q 'ifeq "$(SYSTEM_NAME)" "Darwin"' "$PLATFORM_MK"; then
        echo "Patching makefile.platform to add Darwin/macOS support..."
        patch -d "$MPEG4_DIR" -p1 < "$SCRIPTS_DIR/patches/mpeg4aac-darwin.patch" || true
    fi

    # Fix ar command and add directory creation to makefile.rules
    RULES_MK="$MPEG4_DIR/general/makefile.rules"
    if [ -f "$RULES_MK" ] && grep -q 'ar r \$(DIRTARGET) \$\^' "$RULES_MK"; then
        echo "Patching makefile.rules to fix ar command and directory creation..."
        patch -d "$MPEG4_DIR" -p1 < "$SCRIPTS_DIR/patches/mpeg4aac-ar-fix.patch" || true
    fi

    # Copy isobmff headers
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/src/ISOMovies.h" "$MPEG4_IMPORT/include/"
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/src/MP4Movies.h" "$MPEG4_IMPORT/include/"
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/$MP4OSMACROS_SUBDIR/MP4OSMacros.h" "$MPEG4_IMPORT/include/" 2>/dev/null || true

    # Copy libtsp files from meson build
    cp "$LIBTSP_LIB" "$MPEG4_IMPORT/lib/"
    cp "$LIBTSP_INC/libtsp.h" "$MPEG4_IMPORT/include/"
    mkdir -p "$MPEG4_IMPORT/include/libtsp/"
    cp "$LIBTSP_INC/libtsp/AFpar.h" "$MPEG4_IMPORT/include/libtsp/"
    cp "$LIBTSP_INC/libtsp/UTpar.h" "$MPEG4_IMPORT/include/libtsp/"

    # Setup mp4lib with isobmff library
    # The MPEG-4 makefiles expect the library at ../mp4lib/<platform>/libisomediafile/
    MP4LIB_DIR="$MPEG4_DIR/mp4lib"
    # Determine platform directory name (for MPEG-4 makefiles)
    case "$(uname -s)" in
        Darwin) PLTDIR="darwin" ;;
        Linux)  PLTDIR="linux" ;;
        *)      PLTDIR="unknown" ;;
    esac
    echo "Setting up mp4lib for platform: $PLTDIR"
    mkdir -p "$MP4LIB_DIR/$PLTDIR/libisomediafile"
    mkdir -p "$MP4LIB_DIR/src"
    # Copy headers
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/src/"*.h "$MP4LIB_DIR/src/"
    # Build isobmff library in its build directory
    # Note: isobmff uses 'macosx' for Darwin, 'linux' for Linux
    echo "Building isobmff library..."
    case "$(uname -s)" in
        Darwin) ISOBMFF_PLTDIR="macosx" ;;
        Linux)  ISOBMFF_PLTDIR="linux" ;;
        *)      ISOBMFF_PLTDIR="linux" ;;
    esac
    ISOBMFF_BUILD_DIR="$ISOBMFF_DIR/IsoLib/libisomediafile/$ISOBMFF_PLTDIR/libisomediafile"
    if [ -d "$ISOBMFF_BUILD_DIR" ]; then
        (cd "$ISOBMFF_BUILD_DIR" && make -s) || true
    fi
    # Find and copy the built library to mp4lib (expected by ISOMP4_PATH)
    find "$ISOBMFF_DIR" -name "libisomediafile.a" -exec cp {} "$MP4LIB_DIR/$PLTDIR/libisomediafile/" \; 2>/dev/null || true
    # Also copy to import/lib (expected when using REFSOFT_LIBRARY_PATH)
    find "$ISOBMFF_DIR" -name "libisomediafile.a" -exec cp {} "$MPEG4_IMPORT/lib/" \; 2>/dev/null || true

    # Create output directories
    mkdir -p "$MPEG4_DIR/lib"
    mkdir -p "$MPEG4_DIR/bin"

    # Build decoder
    cd "$MPEG4_DIR/mp4mcDec"
    MAKELEVEL=0 make mp4audec_mc REFSOFT_INCLUDE_PATH=../import/include REFSOFT_LIBRARY_PATH=../import/lib CFLAGS="$CFLAGS_EXTRA" LDFLAGS="$LDFLAGS_EXTRA"
    # Binary location varies by platform
    find "$MPEG4_DIR/bin" -name "mp4audec_mc" -type f -exec cp {} "$DECODERS_DIR/" \;
    echo "mp4audec_mc built successfully!"
fi

# MPEG-4 AAC Error Resilient decoder
if should_build "mpeg4-aac-er"; then
    echo ""
    echo "=== Building MPEG-4 AAC Error Resilient decoder (mp4audec) ==="

    MPEG4_DIR="$CONTRIB_DIR/C050470e_Electronic_inserts/audio/natural"
    MPEG4_IMPORT="$MPEG4_DIR/import"

    # Apply Darwin patches if not already done by mpeg4-aac
    PLATFORM_MK="$MPEG4_DIR/general/makefile.platform"
    if [ -f "$PLATFORM_MK" ] && ! grep -q 'ifeq "$(SYSTEM_NAME)" "Darwin"' "$PLATFORM_MK"; then
        echo "Patching makefile.platform to add Darwin/macOS support..."
        patch -d "$MPEG4_DIR" -p1 < "$SCRIPTS_DIR/patches/mpeg4aac-darwin.patch" || true
    fi

    # Fix ar command and add directory creation to makefile.rules (if not already done)
    RULES_MK="$MPEG4_DIR/general/makefile.rules"
    if [ -f "$RULES_MK" ] && grep -q 'ar r \$(DIRTARGET) \$\^' "$RULES_MK"; then
        echo "Patching makefile.rules to fix ar command..."
        patch -d "$MPEG4_DIR" -p1 < "$SCRIPTS_DIR/patches/mpeg4aac-ar-fix.patch" || true
    fi

    # Fix sed command for BSD sed compatibility (macOS)
    # BSD sed needs separate -e options instead of semicolon-separated commands
    if [ -f "$RULES_MK" ] && grep -q "sed -e's@######## library okay: @@;ta;d;:a;" "$RULES_MK"; then
        echo "Patching makefile.rules to fix sed command for BSD sed..."
        patch -d "$MPEG4_DIR" -p1 < "$SCRIPTS_DIR/patches/mpeg4aac-sed-fix.patch" || true
    fi

    # Copy isobmff headers (may already be done by mpeg4-aac)
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/src/ISOMovies.h" "$MPEG4_IMPORT/include/" 2>/dev/null || true
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/src/MP4Movies.h" "$MPEG4_IMPORT/include/" 2>/dev/null || true
    cp "$ISOBMFF_DIR/IsoLib/libisomediafile/$MP4OSMACROS_SUBDIR/MP4OSMacros.h" "$MPEG4_IMPORT/include/" 2>/dev/null || true

    # Copy libtsp files (may already be done by mpeg4-aac)
    cp "$CONTRIB_DIR/libtsp-v7r0/lib/libtsp.a" "$MPEG4_IMPORT/lib/" 2>/dev/null || true
    cp "$CONTRIB_DIR/libtsp-v7r0/include/libtsp.h" "$MPEG4_IMPORT/include/" 2>/dev/null || true
    mkdir -p "$MPEG4_IMPORT/include/libtsp/"
    cp "$CONTRIB_DIR/libtsp-v7r0/include/libtsp/AFpar.h" "$MPEG4_IMPORT/include/libtsp/" 2>/dev/null || true
    cp "$CONTRIB_DIR/libtsp-v7r0/include/libtsp/UTpar.h" "$MPEG4_IMPORT/include/libtsp/" 2>/dev/null || true

    # Create output directories
    mkdir -p "$MPEG4_DIR/lib"
    mkdir -p "$MPEG4_DIR/bin"

    # Build decoder
    cd "$MPEG4_DIR/mp4AudVm_Rewrite"
    MAKELEVEL=0 make mp4audec REFSOFT_INCLUDE_PATH=../import/include REFSOFT_LIBRARY_PATH=../import/lib CFLAGS="$CFLAGS_EXTRA" LDFLAGS="$LDFLAGS_EXTRA"
    find "$MPEG4_DIR/bin" -name "mp4audec" -type f -exec cp {} "$DECODERS_DIR/" \;
    echo "mp4audec built successfully!"
fi

echo ""
echo "=== ISO Reference Decoders build complete ==="
