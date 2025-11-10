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

# Fluster Docker Wrapper with Hardware Acceleration Support
# This script wraps Fluster commands to run them inside Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script and project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Docker image configuration
DOCKER_IMAGE="fluster:latest"

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Build Options:
  --ubuntu VERSION      Ubuntu version: 20.04, 22.04, or 24.04 (default: 24.04)
  --build-ffmpeg        Build FFmpeg from source (VAAPI, VDPAU, QuickSync - no NVDEC/CUDA)
  --ffmpeg-static       Use static FFmpeg binary (default version: 8.0)
  --ffmpeg-version      Specify FFmpeg version for --build-ffmpeg or --ffmpeg-static
  --build-gstreamer     Build GStreamer from source (useful for new versions on old distros)
  --gstreamer-version   Specify GStreamer version for --build-gstreamer (default: 1.24.2)
  --rebuild             Force rebuilding of Docker image
  --intel               Optimize for Intel GPU (VAAPI + QuickSync)
  --amd                 Optimize for AMD GPU (VAAPI + VDPAU)
  --nvidia              Enable NVIDIA GPU (NVDEC/CUDA on Ubuntu 24.04, VDPAU/VAAPI)

Environment Variables:
  LIBVA_DRIVER_NAME     Override VAAPI driver (e.g., i965, iHD, radeonsi, nouveau)
  VDPAU_DRIVER          Override VDPAU driver (e.g., va_gl, radeonsi, nvidia)

Commands:
  list [options]        List available decoders
  download SUITE        Download test vectors
  run [options]         Run conformance tests
  shell                 Start interactive bash shell
  hw-info               Display hardware acceleration info
  help                  Show this help message

Examples:
  $0 --rebuild list -c
  $0 --build-ffmpeg --rebuild list -c
  $0 --build-ffmpeg --ffmpeg-version 7.1 --rebuild list -c
  $0 --ffmpeg-static --rebuild list -c
  $0 --ffmpeg-static --ffmpeg-version 7.0 --rebuild list -c
  $0 --build-gstreamer --gstreamer-version 1.24.10 --rebuild list -c
  $0 --ubuntu 20.04 --build-gstreamer --rebuild list -c
  $0 --ubuntu 22.04 --rebuild list -c
  $0 --intel hw-info
  $0 --nvidia list -c
  $0 --intel --nvidia hw-info                                     # Dual GPU setup (Intel + NVIDIA)
  $0 --amd --nvidia list -c                                       # Dual GPU setup (AMD + NVIDIA)
  LIBVA_DRIVER_NAME=i965 $0 --intel hw-info                       # Use i965 instead of iHD
  $0 list -c
  $0 download JVT-AVC_V1
  $0 run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1 -k
  $0 --nvidia run -d FFmpeg-H.265-CUDA -ts JCT-VC-HEVC_V1 -k
  $0 shell

EOF
    exit 0
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi


# Parse options
UBUNTU_VERSION="24.04"
REBUILD=""
GPU_TYPES=()
FFMPEG_INSTALL_METHOD="system"
FFMPEG_VERSION="8.0"
GSTREAMER_INSTALL_METHOD="system"
GSTREAMER_VERSION="1.24.2"

while [[ $# -gt 0 ]]; do
    case $1 in
        --ubuntu)
            UBUNTU_VERSION="$2"
            shift 2
            ;;
        --build-ffmpeg)
            FFMPEG_INSTALL_METHOD="source"
            shift
            ;;
        --ffmpeg-version)
            FFMPEG_VERSION="$2"
            shift 2
            ;;
        --ffmpeg-static)
            FFMPEG_INSTALL_METHOD="static"
            FFMPEG_VERSION="${2:-8.0}"
            shift
            if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                shift
            fi
            ;;
        --build-gstreamer)
            GSTREAMER_INSTALL_METHOD="source"
            shift
            ;;
        --gstreamer-version)
            GSTREAMER_VERSION="$2"
            shift 2
            ;;
        --rebuild)
            REBUILD="--no-cache"
            shift
            ;;
        --intel)
            GPU_TYPES+=("intel")
            shift
            ;;
        --amd)
            GPU_TYPES+=("amd")
            shift
            ;;
        --nvidia)
            GPU_TYPES+=("nvidia")
            shift
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            # All remaining arguments are for fluster
            break
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Create necessary directories if they don't exist
mkdir -p resources test_suites

# Detect NVIDIA driver version from host if available
NVIDIA_DRIVER_ARG=""
if command -v nvidia-smi &> /dev/null; then
    NVIDIA_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | cut -d'.' -f1)
    if [ -n "$NVIDIA_VERSION" ]; then
        NVIDIA_DRIVER_ARG="--build-arg NVIDIA_DRIVER_VERSION=$NVIDIA_VERSION"
        echo -e "${BLUE}Detected NVIDIA driver version: $NVIDIA_VERSION${NC}"
    fi
fi

# Build image if it doesn't exist or rebuild requested
if [[ "$(docker images -q $DOCKER_IMAGE 2> /dev/null)" == "" ]] || [ -n "$REBUILD" ]; then
    echo -e "${YELLOW}Building Fluster Docker image...${NC}"
    echo -e "${BLUE}Ubuntu version: $UBUNTU_VERSION${NC}"
    if [ "$FFMPEG_INSTALL_METHOD" = "source" ]; then
        echo -e "${BLUE}Building FFmpeg ${FFMPEG_VERSION} from source with all backends...${NC}"
    elif [ "$FFMPEG_INSTALL_METHOD" = "static" ]; then
        echo -e "${BLUE}Using static FFmpeg ${FFMPEG_VERSION} binary...${NC}"
    else
        echo -e "${BLUE}Using system FFmpeg packages...${NC}"
    fi
    if [ "$GSTREAMER_INSTALL_METHOD" = "source" ]; then
        echo -e "${BLUE}Building GStreamer ${GSTREAMER_VERSION} from source...${NC}"
    else
        echo -e "${BLUE}Using system GStreamer packages...${NC}"
    fi
    docker build \
        --build-arg UBUNTU_VERSION="$UBUNTU_VERSION" \
        --build-arg FFMPEG_INSTALL_METHOD="$FFMPEG_INSTALL_METHOD" \
        --build-arg FFMPEG_VERSION="$FFMPEG_VERSION" \
        --build-arg GSTREAMER_INSTALL_METHOD="$GSTREAMER_INSTALL_METHOD" \
        --build-arg GSTREAMER_VERSION="$GSTREAMER_VERSION" \
        $NVIDIA_DRIVER_ARG \
        $REBUILD \
        -t "$DOCKER_IMAGE" \
        -f docker/Dockerfile \
        . || { echo -e "${RED}Build failed${NC}"; exit 1; }
    echo -e "${GREEN}Build complete!${NC}"
fi

# Set GPU-specific environment variables (respecting user overrides)
GPU_ENV=""
HAS_INTEL=0
HAS_AMD=0
HAS_NVIDIA=0

for gpu in "${GPU_TYPES[@]}"; do
    case "$gpu" in
        intel)
            HAS_INTEL=1
            ;;
        amd)
            HAS_AMD=1
            ;;
        nvidia)
            HAS_NVIDIA=1
            ;;
    esac
done

# Set VAAPI/VDPAU drivers based on GPU type (user env vars take precedence)
if [ $HAS_INTEL -eq 1 ]; then
    GPU_ENV="-e LIBVA_DRIVER_NAME=${LIBVA_DRIVER_NAME:-iHD}"
    GPU_ENV="$GPU_ENV -e VDPAU_DRIVER=${VDPAU_DRIVER:-va_gl}"
    echo -e "${BLUE}Optimizing for Intel GPU (VAAPI + QuickSync)${NC}"
elif [ $HAS_AMD -eq 1 ]; then
    GPU_ENV="-e LIBVA_DRIVER_NAME=${LIBVA_DRIVER_NAME:-radeonsi}"
    GPU_ENV="$GPU_ENV -e VDPAU_DRIVER=${VDPAU_DRIVER:-radeonsi}"
    echo -e "${BLUE}Optimizing for AMD GPU (VAAPI + VDPAU)${NC}"
fi

if [ $HAS_NVIDIA -eq 1 ]; then
    # For NVIDIA with nouveau/mesa drivers, set defaults if no other GPU configured
    if [ -z "$GPU_ENV" ]; then
        GPU_ENV="-e LIBVA_DRIVER_NAME=${LIBVA_DRIVER_NAME:-nouveau}"
    fi
    GPU_ENV="$GPU_ENV -e VDPAU_DRIVER=${VDPAU_DRIVER:-nvidia}"
    echo -e "${BLUE}Enabling NVIDIA GPU (NVDEC/CUDA on Ubuntu 24.04, VDPAU/VAAPI)${NC}"
fi

# Warn about dual GPU setups
if [ $((HAS_INTEL + HAS_AMD + HAS_NVIDIA)) -gt 1 ]; then
    echo -e "${YELLOW}Multi-GPU setup detected. All specified GPUs will be available.${NC}"
fi

# Pass user-defined environment variables even without GPU flags
if [ -z "$GPU_ENV" ]; then
    [ -n "$LIBVA_DRIVER_NAME" ] && GPU_ENV="-e LIBVA_DRIVER_NAME=$LIBVA_DRIVER_NAME"
    [ -n "$VDPAU_DRIVER" ] && GPU_ENV="$GPU_ENV -e VDPAU_DRIVER=$VDPAU_DRIVER"
fi

# Prepare docker run command with volumes and GPU access
DOCKER_RUN_OPTS="-it --rm --privileged --device=/dev/dri:/dev/dri"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -v $PROJECT_ROOT/resources:/fluster/resources"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -v $PROJECT_ROOT/test_suites:/fluster/test_suites"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -e TERM=xterm-256color"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -e LANG=C.UTF-8"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -e LC_ALL=C.UTF-8"
[ -n "$GPU_ENV" ] && DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS $GPU_ENV"
DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS --workdir /fluster"

# Detect -k/--keep for run command to persist outputs by mounting /tmp/fluster_output
FLUSTER_ARGS=("$@")
COMMAND="${FLUSTER_ARGS[0]:-}"  # may be empty
KEEP_FLAG=0
if [[ "$COMMAND" == "run" || "$COMMAND" == "r" ]]; then
    for arg in "${FLUSTER_ARGS[@]}"; do
        if [[ "$arg" == "-k" || "$arg" == "--keep" ]]; then
            KEEP_FLAG=1; break
        fi
    done
    if [[ $KEEP_FLAG -eq 1 ]]; then
        HOST_OUTPUT_DIR="$PROJECT_ROOT/fluster_output"
        CONTAINER_OUTPUT_DIR="/tmp/fluster_output"
        mkdir -p "$HOST_OUTPUT_DIR"
        DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -v $HOST_OUTPUT_DIR:$CONTAINER_OUTPUT_DIR"
        HOST_UID=$(id -u)
        HOST_GID=$(id -g)
        DOCKER_RUN_OPTS="$DOCKER_RUN_OPTS -e HOST_UID=$HOST_UID -e HOST_GID=$HOST_GID"
        POST_RUN_CHOWN="chown -R $HOST_UID:$HOST_GID $CONTAINER_OUTPUT_DIR >/dev/null 2>&1 || true"
        echo -e "${YELLOW}Persisting output files to host directory 'fluster_output/' (flag -k).${NC}"
    fi
fi

# Special command handling
if [ "$1" = "shell" ]; then
    echo -e "${BLUE}Starting Fluster interactive shell...${NC}"
    docker run $DOCKER_RUN_OPTS "$DOCKER_IMAGE" /bin/bash
    exit 0
elif [ "$1" = "hw-info" ]; then
    echo -e "${BLUE}Displaying hardware acceleration info...${NC}"
    docker run $DOCKER_RUN_OPTS "$DOCKER_IMAGE" hw-info
    exit 0
fi

# If no arguments, start interactive shell
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Starting Fluster interactive shell...${NC}"
    echo -e "${YELLOW}Tip: Run 'python3 fluster.py list -c' to see decoders with status${NC}"
    echo "======================================"
    docker run $DOCKER_RUN_OPTS "$DOCKER_IMAGE" /bin/bash
    exit 0
fi

# Run Fluster command
echo -e "${BLUE}Running Fluster command...${NC}"
if [[ $KEEP_FLAG -eq 1 ]]; then
    EXTRA_ARGS=("${FLUSTER_ARGS[@]:1}")
    docker run $DOCKER_RUN_OPTS "$DOCKER_IMAGE" bash -c "python3 fluster.py -tsd /fluster/test_suites -r /fluster/resources run ${EXTRA_ARGS[*]} ; $POST_RUN_CHOWN"
else
    docker run $DOCKER_RUN_OPTS "$DOCKER_IMAGE" \
        python3 fluster.py -tsd /fluster/test_suites -r /fluster/resources "$@"
fi
