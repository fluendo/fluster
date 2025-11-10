#!/bin/bash
# Fluster Docker Wrapper
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
# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi
# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi
# Determine which docker compose command to use
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi
# Change to project root
cd "$PROJECT_ROOT"
# Create necessary directories if they don't exist
mkdir -p resources test_suites fluster_output
# Build image if it doesn't exist
if [[ "$(docker images -q fluster:latest 2> /dev/null)" == "" ]]; then
    echo -e "${YELLOW}Building Fluster Docker image...${NC}"
    $DOCKER_COMPOSE -f docker/docker-compose.yml build
    echo -e "${GREEN}Build complete!${NC}"
fi
# If no arguments, start interactive shell
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Starting Fluster interactive shell...${NC}"
    echo -e "${YELLOW}Tip: Run 'python3 fluster.py list -c' to see decoders with status${NC}"
    echo "======================================"
    $DOCKER_COMPOSE -f docker/docker-compose.yml run --rm \
        -v "$PROJECT_ROOT/resources:/fluster/resources" \
        -v "$PROJECT_ROOT/test_suites:/fluster/test_suites" \
        -v "$PROJECT_ROOT/fluster_output:/fluster/fluster_output" \
        fluster /bin/bash
    exit 0
fi
# Run Fluster command with directory options BEFORE user arguments
echo -e "${BLUE}Running Fluster command...${NC}"
$DOCKER_COMPOSE -f docker/docker-compose.yml run --rm \
    -v "$PROJECT_ROOT/resources:/fluster/resources" \
    -v "$PROJECT_ROOT/test_suites:/fluster/test_suites" \
    -v "$PROJECT_ROOT/fluster_output:/fluster/fluster_output" \
    fluster python3 fluster.py -tsd /fluster/test_suites -r /fluster/resources -o /fluster/fluster_output "$@"
