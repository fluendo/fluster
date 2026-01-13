# Fluster Docker Setup

Docker configuration for Fluster with comprehensive codec support including **FFmpeg** and **GStreamer** with hardware acceleration support (**VAAPI**, **VDPAU**, **NVDEC**, **QuickSync**).

## Features

- **Customizable Ubuntu version**: 20.04, 22.04, or 24.04
- **Three FFmpeg installation options**:
  1. **System packages** (default) - Fast build, but older versions
  2. **Static binaries** (7.x) - Newer FFmpeg, but limited backend support
  3. **Build from source** (recommended) - Latest FFmpeg with all backends enabled
- **Hardware Acceleration Support**:
  - **VAAPI** (Intel, AMD, NVIDIA (only on Ubuntu 24.04))
  - **VDPAU** (Intel via VA-GL bridge, AMD, NVIDIA)
  - **NVDEC/NVENC** (NVIDIA) - Available with system packages on Ubuntu 24.04
  - **Intel QuickSync** (Intel Media SDK, Intel OneVPL)

## FFmpeg Installation Options

This Docker setup provides three ways to install FFmpeg, each with different trade-offs:

### Option 1: System Packages (Default)

**Use case**: Quick testing, CI/CD pipelines
**Pros**: Fast build time (~5 minutes)
**Cons**: Older FFmpeg versions, limited backend support

| Ubuntu | FFmpeg | Backend Support                           |
|--------|--------|-------------------------------------------|
| 20.04  | 4.2.x  | Limited (basic VAAPI, VDPAU)              |
| 22.04  | 4.4.x  | Good (VAAPI, VDPAU, some QuickSync)       |
| 24.04  | 6.1.x  | Best (VAAPI, VDPAU, NVDEC, QuickSync)     |

**Note**: Ubuntu 24.04's FFmpeg includes CUDA/NVDEC support in system packages.

```bash
# Build with system packages (default)
./run-docker.sh --rebuild list -c
```

### Option 2: Static Binaries

**Use case**: Testing specific FFmpeg versions quickly
**Pros**: Easy to use, newer FFmpeg versions available
**Cons**: Limited hardware backend support (no QuickSync/libmfx)

```bash
# Build with FFmpeg static binary
docker build --build-arg FFMPEG_INSTALL_METHOD=static -t fluster:ffmpeg-static -f docker/Dockerfile .
```

**Note**: Static binaries from johnvansickle.com lack libmfx (QuickSync) support.

### Option 3: Build from Source (Recommended)

**Use case**: Full hardware acceleration testing, production use
**Pros**: Latest FFmpeg 8.0 with ALL backends enabled (VAAPI, VDPAU, QuickSync)
**Cons**: Longer build time (~20-30 minutes), no CUDA/NVDEC support

```bash
# Build FFmpeg 8.0 from source with all backends
./run-docker.sh --build-ffmpeg --rebuild list -c

# Or manually specify version
docker build \
  --build-arg FFMPEG_INSTALL_METHOD=source \
  --build-arg FFMPEG_VERSION=8.0 \
  -t fluster:ffmpeg-full \
  -f docker/Dockerfile .
```

**Included backends when building from source:**
- ✅ VAAPI (Intel, AMD, NVIDIA on Ubuntu 24.04)
- ✅ VDPAU (Intel via VA-GL bridge, AMD, NVIDIA)
- ✅ QuickSync (Intel libmfx) - **Now included!**
- ✅ All software codecs (x264, x265, vpx, aom, dav1d, fdk-aac)
- ❌ NVDEC/NVENC (CUDA) - **Not available** (requires CUDA SDK installation)

**Note**: NVIDIA CUDA/NVDEC support is available with **system packages** (Ubuntu 24.04 default), but NOT when building FFmpeg from source. For NVDEC, use the default system packages. When building from source, NVIDIA hardware decoding is available via VDPAU and VAAPI (Ubuntu 24.04 only).

**Recommendation**: Use `--build-ffmpeg` for latest FFmpeg with comprehensive codec and hardware acceleration support.

## Software Versions by Ubuntu Release

| Ubuntu | FFmpeg (system) | FFmpeg (source) | GStreamer | Notes                |
|--------|-----------------|-----------------|-----------|----------------------|
| 20.04  | 4.2.x           | 8.0             | 1.16.x    | Legacy support       |
| 22.04  | 4.4.x           | 8.0             | 1.20.x    | Stable               |
| 24.04  | 6.1.x           | 8.0             | 1.24.x    | Latest (recommended) |

## Structure
```
docker/
├── Dockerfile           - Main Dockerfile with hardware support
├── run-docker.sh        - Build and run script with GPU support
└── README.md            - This documentation
```

## Quick Start

### Basic Usage (Default: Ubuntu 24.04)

From the `docker/` directory:
```bash
# Build and list available decoders with status checks (✔️/❌)
./run-docker.sh --rebuild list -c

# Show hardware acceleration info
./run-docker.sh hw-info

# List decoders for a specific codec
./run-docker.sh list -c -d H.265

# Download test vectors
./run-docker.sh download JVT-AVC_V1

# Run tests with hardware decoder (use -k to keep files)
./run-docker.sh run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1 -k

# Interactive shell
./run-docker.sh shell
```

### Custom Build Options

Build with specific Ubuntu version:

```bash
# Ubuntu 22.04
./run-docker.sh --ubuntu 22.04 --rebuild list -c

# Ubuntu 24.04 (default, recommended)
./run-docker.sh --ubuntu 24.04 --rebuild list -c

# Ubuntu 20.04 (legacy)
./run-docker.sh --ubuntu 20.04 --rebuild list -c
```

Build FFmpeg from source with all backends (recommended for production):

```bash
# Build FFmpeg 8.0 from source with all hardware acceleration backends
./run-docker.sh --build-ffmpeg --rebuild list -c

# Test with Intel QuickSync (requires building from source)
./run-docker.sh --build-ffmpeg --intel --rebuild run -d FFmpeg-H.264-QSV -ts JVT-AVC_V1 -k
```

**Note**: For NVIDIA CUDA/NVDEC decoders (FFmpeg-H.265-CUDA, etc.), use system packages (default, without `--build-ffmpeg` flag), as Ubuntu 24.04 includes CUDA support in system FFmpeg packages.


### FFmpeg Version Override

By default, FFmpeg from Ubuntu repositories is used. To test with newer FFmpeg versions (e.g., for future VVC support), use static binaries:

```bash
# Build with FFmpeg static binary
docker build --build-arg FFMPEG_INSTALL_METHOD=static -t fluster:ffmpeg-static -f docker/Dockerfile .

# Verify version
docker run --rm fluster:ffmpeg-static ffmpeg -version | head -1
```

**Note:** Static binaries may have limited hardware acceleration support compared to system packages. Use only when testing specific features not available in system FFmpeg.

### Hardware-Specific Optimization

```bash
# Intel GPU (VAAPI + QuickSync)
./run-docker.sh --intel hw-info
./run-docker.sh --intel list -c | grep -E "(VAAPI|VA|QSV|MSDK)"

# AMD GPU (VAAPI + VDPAU)
./run-docker.sh --amd hw-info
./run-docker.sh --amd list -c | grep VAAPI

# NVIDIA GPU (CUDA/NVDEC on Ubuntu 24.04)
./run-docker.sh --nvidia hw-info
./run-docker.sh --nvidia list -c | grep -E "CUDA|NVDEC"
```

## Included Decoders

This Docker image includes **FFmpeg** and **GStreamer** with comprehensive hardware acceleration support.

**Note on H.266/VVC:** H.266/VVC decoders are not available in system packages (FFmpeg 4.x-6.1.x, GStreamer 1.16.x-1.24.x) across Ubuntu 20.04, 22.04, and 24.04. Native VVC support requires FFmpeg 7.0+ with VVC libraries and GStreamer 1.26+ with appropriate plugins, which are not yet available in Ubuntu repositories. If you need VVC testing, consider building FFmpeg/GStreamer from source or waiting for future Ubuntu releases.

### FFmpeg Decoders

FFmpeg provides software decoders for all major codecs:
- H.264/AVC, H.265/HEVC
- VP8, VP9, AV1
- MPEG2, MPEG4

**Note:** H.266/VVC is not available in system FFmpeg packages. Native VVC support requires FFmpeg 7.0+ with VVC libraries, which is not yet available in Ubuntu repositories.

Use the pattern `FFmpeg-<CODEC>` (e.g., `FFmpeg-H.264`, `FFmpeg-H.265`)

### GStreamer Software Decoders

GStreamer with libav plugin exposes FFmpeg decoders through GStreamer:
- `GStreamer-<CODEC>-Libav-Gst1.0` (e.g., `GStreamer-H.264-Libav-Gst1.0`)

### GStreamer Hardware Decoders

#### VAAPI (Intel, AMD, NVIDIA on Ubuntu 24.04)
- `GStreamer-H.264-VAAPI-Gst1.0` (vaapih264dec)
- `GStreamer-H.265-VAAPI-Gst1.0` (vaapih265dec)
- `GStreamer-H.264-VA-Gst1.0` (vah264dec) - newer
- `GStreamer-H.265-VA-Gst1.0` (vah265dec) - newer
- `GStreamer-VP8-VAAPI-Gst1.0`
- `GStreamer-VP9-VAAPI-Gst1.0`
- `GStreamer-AV1-VAAPI-Gst1.0`

**Note:** H.266/VVC VAAPI decoder (vah266dec) requires GStreamer 1.26+ and is not available in current Ubuntu packages.

#### Intel QuickSync
- `GStreamer-H.264-QSV-Gst1.0` (qsvh264dec)
- `GStreamer-H.264-MSDK-Gst1.0` (msdkh264dec)
- `GStreamer-H.265-MSDK-Gst1.0` (msdkh265dec)

#### NVIDIA NVDEC (Ubuntu 24.04)
- `FFmpeg-H.264-CUDA` (h264_cuvid)
- `FFmpeg-H.265-CUDA` (hevc_cuvid)
- `FFmpeg-VP8-CUDA` (vp8_cuvid)
- `FFmpeg-VP9-CUDA` (vp9_cuvid)
- `GStreamer-H.264-NVDEC-Gst1.0` (nvh264dec)
- `GStreamer-H.265-NVDEC-Gst1.0` (nvh265dec)
- `GStreamer-VP8-NVDEC-Gst1.0` (nvvp8dec)
- `GStreamer-VP9-NVDEC-Gst1.0` (nvvp9dec)

## Hardware Acceleration Setup

### VAAPI

**Requirements:**
- GPU with VAAPI support (Intel, AMD, or NVIDIA on Ubuntu 24.04)
- Appropriate drivers installed on host
- User in `video` and `render` groups

**Test VAAPI:**
```bash
./run-docker.sh --intel hw-info
./run-docker.sh --intel run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1 -k
```

### Intel QuickSync

**Requirements:**
- Intel GPU with Quick Sync support (6th gen+)
- Intel Media SDK libraries (included in image)

**Packages included:**
- `libmfx1` - Intel Media SDK runtime
- `libmfx-gen1.2` - For newer Intel GPUs
- `libvpl2` - oneVPL runtime

**Test QuickSync:**
```bash
./run-docker.sh --intel run -d GStreamer-H.264-QSV-Gst1.0 -ts JVT-AVC_V1 -k
```

### NVIDIA NVDEC

**Requirements:**
- NVIDIA GPU with NVDEC support (compute capability >= 3.0)
- NVIDIA drivers installed on host (`nvidia-smi` working on host)
- **Ubuntu 24.04** (system packages include CUDA/NVDEC support)
- **No special Docker configuration needed** - uses `--privileged` mode

**How it works:**
The Docker container uses `--privileged` mode and mounts `/dev/dri` which gives automatic access to NVIDIA GPU for hardware decoding. Ubuntu 24.04's FFmpeg includes CUDA/NVDEC support in system packages. No nvidia-docker2 or nvidia-container-toolkit required!

**Driver Version Matching:**
The build script automatically detects your host NVIDIA driver version (e.g., 535, 550, 560) and installs matching VDPAU libraries inside the container. This ensures compatibility between the container and your host drivers.

**Test NVDEC:**
```bash
# Check NVIDIA GPU (also shows detected driver version)
./run-docker.sh --nvidia hw-info

# List NVDEC decoders
./run-docker.sh --nvidia list -c | grep -i "cuda\|nvdec"

# Download test vectors
./run-docker.sh download JCT-VC-HEVC_V1

# Run test with FFmpeg NVDEC
./run-docker.sh --nvidia run -d FFmpeg-H.265-CUDA -ts JCT-VC-HEVC_V1 -k

# Run test with GStreamer NVDEC
./run-docker.sh --nvidia run -d GStreamer-H.265-NVDEC-Gst1.0 -ts JCT-VC-HEVC_V1 -k
```

**Note:** CUDA/NVDEC support is only available with **system packages** (default). If you use `--build-ffmpeg`, NVDEC will NOT be available. Some test vectors may fail with hardware decoders due to specific features or edge cases. This is normal and expected.

## Mounted Volumes

The following directories are automatically mounted from your host to the container:
- `./resources/` - Downloaded test vectors (created automatically, persists on host)
- `./test_suites/` - Test suite definitions (must exist in repo)

### Output Files Behavior

By default, Fluster writes decoder outputs to an internal temp directory (`/tmp/fluster_output`) inside the container and they are discarded when the container exits.

Persistence is opt-in:
- Without `-k` (or `--keep`): output files are ephemeral (mirrors local non-Docker behavior).
- With `-k`: the host directory `./fluster_output/` is mounted at `/tmp/fluster_output` and all `.out` files are kept on your machine.

Examples:
```bash
# Ephemeral run (no outputs kept)
./run-docker.sh run -d FFmpeg-H.264 -ts JVT-AVC_V1 -tv AUD_MW_E

# Persistent run (-k creates ./fluster_output on host)
./run-docker.sh run -d FFmpeg-H.264 -ts JVT-AVC_V1 -tv AUD_MW_E -k

# Inspect persisted files
ls -lh fluster_output/JVT-AVC_V1/
```
Cleaning up:
```bash
rm -rf fluster_output   # remove all persisted outputs
```

Note: Large suites (e.g. HEVC) can consume multiple GB. Only use `-k` when you actually need the raw `.out` files.

### Inspecting Outputs Inside the Container
If you want to inspect outputs temporarily without persisting them:
```bash
./run-docker.sh shell
python3 fluster.py run -d FFmpeg-H.264 -ts JVT-AVC_V1 -tv AUD_MW_E -k
ls -lh /tmp/fluster_output/JVT-AVC_V1/
exit  # files are lost (not persisted) unless -k was used via wrapper
```

## Environment Variables

The following variables are set automatically in the container:
- `TERM=xterm-256color` - For emoji display ✔️/❌
- `LANG=C.UTF-8` - UTF-8 support
- `LC_ALL=C.UTF-8` - UTF-8 locale
- `LIBVA_DRIVER_NAME` - VAAPI driver (iHD, i965, radeonsi, nouveau)
- `VDPAU_DRIVER` - VDPAU driver (va_gl, radeonsi, nvidia)

To override the default driver selection, set the variable on the host:
```bash
# Use i965 driver instead of iHD for older Intel GPUs
LIBVA_DRIVER_NAME=i965 ./run-docker.sh --intel hw-info
```

## Usage Examples

### Testing Different Configurations

```bash
# Ubuntu 24.04 with latest software
./run-docker.sh --ubuntu 24.04 --rebuild list -c

# Ubuntu 22.04 for compatibility testing
./run-docker.sh --ubuntu 22.04 --rebuild list -c

# Ubuntu 20.04 for legacy support
./run-docker.sh --ubuntu 20.04 --rebuild list -c
```

### Hardware Decoder Testing

```bash
# Intel VAAPI (ephemeral)
./run-docker.sh --intel run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1
# Intel VAAPI (keep outputs)
./run-docker.sh --intel run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1 -k

# NVIDIA NVDEC (keep one output, Ubuntu 24.04)
./run-docker.sh --nvidia run -d FFmpeg-H.265-CUDA -ts JCT-VC-HEVC_V1 -tv AMP_A_Samsung_7 -k
```

### Interactive Development

```bash
# Start shell
./run-docker.sh shell

# Inside container:
vainfo                    # Check VAAPI
vdpauinfo                 # Check VDPAU
hw-info                   # Display all hardware info
gst-inspect-1.0 vaapi     # Check GStreamer VAAPI plugins
python3 fluster.py list -c # List decoders
```

## Manual Build

If you prefer to build manually without using `run-docker.sh`:

```bash
cd /path/to/fluster

# Default build (Ubuntu 24.04)
docker build -t fluster:latest -f docker/Dockerfile .

# Custom build with specific Ubuntu version
docker build --build-arg UBUNTU_VERSION=22.04 -t fluster:latest -f docker/Dockerfile .

# Force rebuild
docker build --no-cache -t fluster:latest -f docker/Dockerfile .
```

Then run manually:
```bash
docker run -it --rm --privileged \
    --device=/dev/dri:/dev/dri \
    -v $(pwd)/resources:/fluster/resources \
    -v $(pwd)/test_suites:/fluster/test_suites \
    -e TERM=xterm-256color \
    fluster:latest \
    python3 fluster.py list -c
```

**Note:** Output files are stored in `/tmp/fluster_output` inside the container (ephemeral, matching non-Docker behavior).

## Troubleshooting

### No hardware devices found

Check GPU access:
```bash
ls -la /dev/dri  # Should show card0, renderD128, etc.
```

Add your user to video/render groups:
```bash
sudo usermod -aG video $USER
sudo usermod -aG render $USER
# Log out and back in
```

### NVIDIA GPU not working

The container uses `--privileged` mode which gives automatic access to GPU. If NVIDIA decoders don't work:

1. Verify NVIDIA drivers are installed on host:
```bash
nvidia-smi  # Should show your GPU
lsmod | grep nvidia  # Should show nvidia modules loaded
```

2. Check GPU devices are accessible:
```bash
ls -la /dev/dri  # Should show renderD* devices
ls -la /dev/nvidia*  # Should show nvidia devices (if available)
```

3. Make sure you're using Ubuntu 24.04 (for CUDA/NVDEC support):
```bash
./run-docker.sh --ubuntu 24.04 --rebuild --nvidia hw-info
```

4. Run with --nvidia flag:
```bash
./run-docker.sh --nvidia hw-info
./run-docker.sh --nvidia list -c | grep -E "CUDA|NVDEC"
```

5. Test inside container:
```bash
./run-docker.sh --nvidia shell
# Inside container:
ffmpeg -hwaccels  # Should show 'cuda' in the list
```

**Note**: CUDA/NVDEC hardware acceleration is only available with **Ubuntu 24.04 system packages** (default). If you use `--build-ffmpeg`, NVDEC will not be available.

### Complete rebuild

```bash
cd /path/to/fluster
docker build --no-cache -t fluster:latest -f docker/Dockerfile .
```

Or using the script:
```bash
./run-docker.sh --rebuild list -c
```

## From Project Root

All commands also work from the project root:
```bash
docker/run-docker.sh list -c
docker/run-docker.sh --intel download JVT-AVC_V1
docker/run-docker.sh --intel run -d GStreamer-H.264-VAAPI-Gst1.0 -ts JVT-AVC_V1 -k
```
