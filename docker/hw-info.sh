#!/bin/bash

# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#  Author: Ruben Sanchez Sanchez <rsanchez@fluendo.com>, Fluendo, S.A.
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

set -e

echo "=== Hardware Acceleration Info ==="
echo ""

echo "FFmpeg version:"
ffmpeg -version 2>&1 | head -1
echo ""

echo "FFmpeg hardware accelerations:"
ffmpeg -hwaccels 2>&1 | tail -n +2 | grep -v "^ffmpeg" | grep -v "^built" | grep -v "^configuration" | grep -v "^lib"
echo ""

echo "GStreamer version:"
gst-launch-1.0 --version 2>&1 | grep "GStreamer" | head -1
echo ""

echo "Available /dev/dri devices:"
if find /dev/dri -maxdepth 1 \( -name 'card*' -o -name 'renderD*' \) 2>/dev/null | grep -q .; then
    find /dev/dri -maxdepth 1 \( -name 'card*' -o -name 'renderD*' \) 2>/dev/null | head -5
else
    echo "No DRI devices found"
fi
echo ""

echo "GPU Detection:"
echo ""

# NVIDIA detection
echo "  NVIDIA:"
if lspci 2>/dev/null | grep -iq "NVIDIA\|GeForce\|Quadro\|Tesla"; then
    echo "    ✓ NVIDIA GPU detected"
    if [ -c /dev/nvidia0 ] || [ -c /dev/nvidiactl ]; then
        echo "    ✓ NVIDIA devices available in /dev (drivers from host)"
        if command -v nvidia-smi &>/dev/null; then
            nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null || true
        else
            echo "    (nvidia-smi not in container, using host drivers via --privileged)"
        fi
    else
        echo "    ⚠ NVIDIA GPU detected but no /dev/nvidia* devices found"
    fi
else
    echo "    ✗ No NVIDIA GPU detected"
fi
echo ""

# Intel detection
echo "  Intel:"
if grep -q "0x8086" /sys/class/drm/card*/device/vendor 2>/dev/null; then
    echo "    ✓ Intel GPU detected (vendor ID 0x8086)"
    vainfo_output=$(vainfo 2>&1)
    if [ $? -eq 0 ] && echo "$vainfo_output" | grep -q "iHD\|i965"; then
        echo "    ✓ VA-API driver loaded successfully"
    else
        echo "    ✗ VA-API driver failed to load"
    fi
else
    echo "    ✗ No Intel GPU detected"
fi
echo ""

# AMD detection
echo "  AMD:"
if grep -q "0x1002" /sys/class/drm/card*/device/vendor 2>/dev/null; then
    echo "    ✓ AMD GPU detected (vendor ID 0x1002)"
else
    echo "    ✗ No AMD GPU detected"
fi
echo ""

# VAAPI info
echo "VAAPI:"
if command -v vainfo &>/dev/null; then
    VAAPI_OUTPUT=$(vainfo 2>&1)
    if echo "$VAAPI_OUTPUT" | grep -q "VA-API version"; then
        DRIVER_INFO=$(echo "$VAAPI_OUTPUT" | grep -E "(Driver version|VAProfile)" | head -5)
        if [ -n "$DRIVER_INFO" ]; then
            echo "  Driver info:"
            while IFS= read -r line; do
                echo "    $line"
            done <<< "$DRIVER_INFO"
        else
            echo "  Driver loaded but no profile info available"
        fi
    else
        echo "  No VAAPI devices initialized"
    fi
else
    echo "  vainfo not available"
fi
echo ""

# VDPAU info
echo "VDPAU:"
if command -v vdpauinfo &>/dev/null; then
    if vdpauinfo 2>&1 | grep -q "display:"; then
        echo "  Available decoders:"
        while IFS= read -r line; do
            echo "    $line"
        done < <(vdpauinfo 2>&1 | grep "Decoder" | head -5)
    else
        echo "  Not available (requires display, but decoding may work)"
    fi
else
    echo "  vdpauinfo not available"
fi
echo ""

# QuickSync info
echo "Intel QuickSync (QSV/MSDK):"
if [ -d /opt/intel/mediasdk ] || command -v sample_decode &>/dev/null; then
    echo "  ✓ Intel Media SDK detected"
elif ls /usr/lib/x86_64-linux-gnu/libmfx*.so* &>/dev/null; then
    echo "  ✓ libmfx libraries available"
else
    echo "  ✗ No Intel Media SDK found"
fi
