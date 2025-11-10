#!/bin/bash
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
  --build-ffmpeg        Build FFmpeg from source with all backends (VAAPI, VDPAU, NVDEC, QuickSync)
  --rebuild             Force rebuild the Docker image
  --intel               Optimize for Intel GPU (VAAPI + QuickSync)
  --amd                 Optimize for AMD GPU (VAAPI + VDPAU)
  --nvidia              Enable NVIDIA GPU (NVDEC/VDPAU)

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
  $0 --ubuntu 22.04 --rebuild list -c
  $0 --intel hw-info
  $0 --nvidia list -c
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
GPU_TYPE=""
BUILD_FFMPEG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --ubuntu)
            UBUNTU_VERSION="$2"
            shift 2
            ;;
        --build-ffmpeg)
            BUILD_FFMPEG="--build-arg BUILD_FFMPEG_FROM_SOURCE=1"
            shift
            ;;
        --rebuild)
            REBUILD="--no-cache"
            shift
            ;;
        --intel)
            GPU_TYPE="intel"
            shift
            ;;
        --amd)
            GPU_TYPE="amd"
            shift
            ;;
        --nvidia)
            GPU_TYPE="nvidia"
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

# Build image if it doesn't exist or rebuild requested
if [[ "$(docker images -q $DOCKER_IMAGE 2> /dev/null)" == "" ]] || [ -n "$REBUILD" ]; then
    echo -e "${YELLOW}Building Fluster Docker image...${NC}"
    echo -e "${BLUE}Ubuntu version: $UBUNTU_VERSION${NC}"
    if [ -n "$BUILD_FFMPEG" ]; then
        echo -e "${BLUE}Building FFmpeg from source with all backends...${NC}"
    fi
    docker build \
        --build-arg UBUNTU_VERSION="$UBUNTU_VERSION" \
        $BUILD_FFMPEG \
        $REBUILD \
        -t "$DOCKER_IMAGE" \
        -f docker/Dockerfile \
        . || { echo -e "${RED}Build failed${NC}"; exit 1; }
    echo -e "${GREEN}Build complete!${NC}"
fi

# Set GPU-specific environment variables
GPU_ENV=""
if [ "$GPU_TYPE" = "intel" ]; then
    GPU_ENV="-e LIBVA_DRIVER_NAME=iHD"
    echo -e "${BLUE}Optimizing for Intel GPU (VAAPI + QuickSync)${NC}"
elif [ "$GPU_TYPE" = "amd" ]; then
    GPU_ENV="-e LIBVA_DRIVER_NAME=radeonsi"
    echo -e "${BLUE}Optimizing for AMD GPU (VAAPI + VDPAU)${NC}"
elif [ "$GPU_TYPE" = "nvidia" ]; then
    echo -e "${BLUE}Enabling NVIDIA GPU (NVDEC/VDPAU)${NC}"
    # NVIDIA works automatically with --privileged and /dev/dri
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
