#!/bin/bash
# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# Helper script to download all ISO reference decoder dependencies
# Downloads: MPEG-2 AAC, MPEG-2 video, MPEG-4 AAC, and libtsp

set -e

# Get script directory and subprojects directory before changing directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SUBPROJECTS_DIR="$(cd "$SCRIPT_DIR/../subprojects" && pwd)"

# Make CONTRIB_DIR absolute
CONTRIB_DIR="${1:-$SCRIPT_DIR/../contrib}"
CONTRIB_DIR="$(cd "$(dirname "$CONTRIB_DIR")" && pwd)/$(basename "$CONTRIB_DIR")"

# Check if curl is available
if ! which curl > /dev/null 2>&1; then
    echo "Error: curl is required but not installed."
    exit 1
fi

mkdir -p "$CONTRIB_DIR"

echo "=== Fluster Dependencies Download Script ==="
echo "This script will download ISO reference software for:"
echo "  - MPEG-2 AAC decoder"
echo "  - MPEG-2 video decoder"
echo "  - MPEG-4 AAC decoders"
echo "  - libtsp audio library"
echo ""

# Check if already downloaded
ALREADY_DOWNLOADED=true
if [ ! -d "$CONTRIB_DIR/mpeg2aac" ]; then
    ALREADY_DOWNLOADED=false
fi
if [ ! -d "$CONTRIB_DIR/video" ]; then
    ALREADY_DOWNLOADED=false
fi
if [ ! -d "$CONTRIB_DIR/C050470e_Electronic_inserts" ]; then
    ALREADY_DOWNLOADED=false
fi
if [ ! -d "$CONTRIB_DIR/libtsp-v7r0" ]; then
    ALREADY_DOWNLOADED=false
fi

if [ "$ALREADY_DOWNLOADED" = true ]; then
    echo "All dependencies already downloaded in $CONTRIB_DIR"

    # Copy meson.build files to contrib directories if not present
    PACKAGEFILES_DIR="$(cd "$SCRIPT_DIR/../subprojects/packagefiles" && pwd)"

    if [ ! -f "$CONTRIB_DIR/video/meson.build" ]; then
        echo "Copying meson.build for MPEG-2 video"
        cp "$PACKAGEFILES_DIR/mpeg2video/meson.build" "$CONTRIB_DIR/video/meson.build"
    fi

    if [ ! -f "$CONTRIB_DIR/mpeg2aac/meson.build" ]; then
        echo "Copying meson.build for MPEG-2 AAC"
        cp "$PACKAGEFILES_DIR/mpeg2aac/meson.build" "$CONTRIB_DIR/mpeg2aac/meson.build"
        # Copy compat headers for macOS
        if [ -d "$PACKAGEFILES_DIR/mpeg2aac/compat" ]; then
            cp -r "$PACKAGEFILES_DIR/mpeg2aac/compat" "$CONTRIB_DIR/mpeg2aac/"
        fi
    fi

    if [ ! -f "$CONTRIB_DIR/libtsp-v7r0/meson.build" ]; then
        echo "Copying meson.build for libtsp"
        cp "$PACKAGEFILES_DIR/libtsp/meson.build" "$CONTRIB_DIR/libtsp-v7r0/meson.build"
    fi

    # Create symlinks for meson subprojects
    if [ ! -e "$SUBPROJECTS_DIR/mpeg2video" ]; then
        echo "Creating symlink: subprojects/mpeg2video -> contrib/video"
        ln -sf "../contrib/video" "$SUBPROJECTS_DIR/mpeg2video"
    fi
    if [ ! -e "$SUBPROJECTS_DIR/mpeg2aac" ]; then
        echo "Creating symlink: subprojects/mpeg2aac -> contrib/mpeg2aac"
        ln -sf "../contrib/mpeg2aac" "$SUBPROJECTS_DIR/mpeg2aac"
    fi
    if [ ! -e "$SUBPROJECTS_DIR/libtsp-v7r0" ]; then
        echo "Creating symlink: subprojects/libtsp-v7r0 -> contrib/libtsp-v7r0"
        ln -sf "../contrib/libtsp-v7r0" "$SUBPROJECTS_DIR/libtsp-v7r0"
    fi
    echo "Dependencies are ready!"
    exit 0
fi

cd "$CONTRIB_DIR"

# Download MPEG-2 dependencies
if [ ! -d "mpeg2aac" ] || [ ! -d "video" ]; then
    echo ""
    echo "=== Downloading MPEG-2 reference software ==="
    rm -f iso_cookies.txt
    curl -sL -c iso_cookies.txt \
        'https://standards.iso.org/ittf/PubliclyAvailableStandards/c039486_ISO_IEC_13818-5_2005_Reference_Software.zip' > /dev/null
    curl -L -b iso_cookies.txt -d 'ok=I+accept' \
        'https://standards.iso.org/ittf/PubliclyAvailableStandards/c039486_ISO_IEC_13818-5_2005_Reference_Software.zip' \
        -o c039486_ISO_IEC_13818-5_2005_Reference_Software.zip
    unzip -oq c039486_ISO_IEC_13818-5_2005_Reference_Software.zip
    rm -f iso_cookies.txt c039486_ISO_IEC_13818-5_2005_Reference_Software.zip ipmp.zip mpeg2audio.zip systems.zip

    echo "Extracting MPEG-2 AAC..."
    unzip -oq mpeg2aac.zip
    rm -f mpeg2aac.zip

    echo "Extracting MPEG-2 video..."
    unzip -oq video.zip
    rm -f video.zip
fi

# Download MPEG-4 dependencies
if [ ! -d "C050470e_Electronic_inserts" ]; then
    echo ""
    echo "=== Downloading MPEG-4 reference software ==="
    rm -f iso_cookies.txt
    curl -sL -c iso_cookies.txt \
        'https://standards.iso.org/ittf/PubliclyAvailableStandards/c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip' > /dev/null
    curl -L -b iso_cookies.txt -d 'ok=I+accept' \
        'https://standards.iso.org/ittf/PubliclyAvailableStandards/c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip' \
        -o c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip
    unzip -oq c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip
    rm -f iso_cookies.txt c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip
fi

# Download libtsp
if [ ! -d "libtsp-v7r0" ]; then
    echo ""
    echo "=== Downloading libtsp audio library ==="
    curl -kL https://www-mmsp.ece.mcgill.ca/Documents/Downloads/libtsp/libtsp-v7r0.tar.gz -o libtsp-v7r0.tar.gz
    tar -zxf libtsp-v7r0.tar.gz
    chmod -R ugo=rwx libtsp-v7r0/
    rm -f libtsp-v7r0.tar.gz
fi

# Copy meson.build files to contrib directories
echo ""
echo "=== Setting up meson build files ==="
PACKAGEFILES_DIR="$(cd "$SCRIPT_DIR/../subprojects/packagefiles" && pwd)"

if [ ! -f "$CONTRIB_DIR/video/meson.build" ]; then
    echo "Copying meson.build for MPEG-2 video"
    cp "$PACKAGEFILES_DIR/mpeg2video/meson.build" "$CONTRIB_DIR/video/meson.build"
fi

if [ ! -f "$CONTRIB_DIR/mpeg2aac/meson.build" ]; then
    echo "Copying meson.build for MPEG-2 AAC"
    cp "$PACKAGEFILES_DIR/mpeg2aac/meson.build" "$CONTRIB_DIR/mpeg2aac/meson.build"
    # Copy compat headers for macOS
    if [ -d "$PACKAGEFILES_DIR/mpeg2aac/compat" ]; then
        cp -r "$PACKAGEFILES_DIR/mpeg2aac/compat" "$CONTRIB_DIR/mpeg2aac/"
    fi
fi

if [ ! -f "$CONTRIB_DIR/libtsp-v7r0/meson.build" ]; then
    echo "Copying meson.build for libtsp"
    cp "$PACKAGEFILES_DIR/libtsp/meson.build" "$CONTRIB_DIR/libtsp-v7r0/meson.build"
fi

# Create symlinks for meson subprojects
echo ""
echo "=== Creating symlinks for meson subprojects ==="
if [ ! -e "$SUBPROJECTS_DIR/mpeg2video" ]; then
    echo "Creating symlink: subprojects/mpeg2video -> contrib/video"
    ln -sf "../contrib/video" "$SUBPROJECTS_DIR/mpeg2video"
fi
if [ ! -e "$SUBPROJECTS_DIR/mpeg2aac" ]; then
    echo "Creating symlink: subprojects/mpeg2aac -> contrib/mpeg2aac"
    ln -sf "../contrib/mpeg2aac" "$SUBPROJECTS_DIR/mpeg2aac"
fi
if [ ! -e "$SUBPROJECTS_DIR/libtsp-v7r0" ]; then
    echo "Creating symlink: subprojects/libtsp-v7r0 -> contrib/libtsp-v7r0"
    ln -sf "../contrib/libtsp-v7r0" "$SUBPROJECTS_DIR/libtsp-v7r0"
fi

echo ""
echo "=== All dependencies downloaded successfully! ==="
echo "You can now run: meson setup builddir"
