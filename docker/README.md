# Fluster Docker Setup
Docker configuration for Fluster with comprehensive codec support including **FFmpeg 7.1** and **GStreamer 1.24** with libav plugin.
## Structure
```
docker/
├── Dockerfile           - VVdeC + GStreamer
├── docker-compose.yml   - Service orchestration
├── run-docker.sh        - Script to run Fluster
└── README.md            - This documentation
```
## Quick Start
From the `docker/` directory:
```bash
# List available decoders with status checks (✔️/❌)
./run-docker.sh list -c

# List decoders for a specific codec (H.264, H.265, H.266, VP8, VP9, AV1, etc.)
./run-docker.sh list -c -d H.266
./run-docker.sh list -c -d H.265
./run-docker.sh list -c -d VP9

# Download test vectors (creates resources/ automatically)
./run-docker.sh download JVET-VVC_draft6      # H.266
./run-docker.sh download JVT-AVC_V1           # H.264
./run-docker.sh download JCT-VC-HEVC_V1       # H.265

# Run tests with different decoders (use -k to keep files and avoid Docker volume errors)
./run-docker.sh run -d FFmpeg-H.266 -ts JVET-VVC_draft6 -k
./run-docker.sh run -d FFmpeg-H.265 -ts JCT-VC-HEVC_V1 -k
./run-docker.sh run -d GStreamer-H.264-Libav-Gst1.0 -ts JVT-AVC_V1 -k

# Interactive shell
./run-docker.sh
```

Or from project root:
```bash
docker/run-docker.sh list -c
docker/run-docker.sh download JVET-VVC_draft6
docker/run-docker.sh run -d FFmpeg-H.266 -ts JVET-VVC_draft6 -k
```

## Included Decoders

This Docker image includes **FFmpeg 7.1** and **GStreamer 1.24** with libav plugin, providing comprehensive decoder support for all major video codecs.

### FFmpeg Decoders

FFmpeg 7.1 provides native decoders for:
- H.264/AVC, H.265/HEVC, **H.266/VVC**
- VP8, VP9, AV1
- MPEG2, MPEG4
- And many more...

Use the pattern `FFmpeg-<CODEC>` (e.g., `FFmpeg-H.264`, `FFmpeg-H.265`, `FFmpeg-H.266`)

### GStreamer Libav Decoders

GStreamer 1.24 with libav plugin exposes **422 decoders** from FFmpeg, supporting all major codecs through the `GStreamer-<CODEC>-Libav-Gst1.0` pattern.

Examples: `GStreamer-H.264-Libav-Gst1.0`, `GStreamer-H.265-Libav-Gst1.0`, `GStreamer-H.266-Libav-Gst1.0`

### Specialized Decoders

Additional standalone decoders:
- **VVdeC-H266** - Fraunhofer HHI VVC/H.266 decoder (vvdecapp 3.0.0)

Use `./run-docker.sh list -c` to see all available decoders with their current status.

## Mounted Volumes
The following directories are automatically mounted:
- `./resources/` - Downloaded test vectors (created automatically)
- `./test_suites/` - Test suite definitions (must exist in repo)
- `./fluster_output/` - Test execution results (created automatically)
## Environment Variables
- `TERM=xterm-256color` - For emoji display ✔️/❌
- `LANG=C.UTF-8` - UTF-8 support
- `LC_ALL=C.UTF-8` - UTF-8 locale
## Manual Build
```bash
cd docker
docker compose build
```
## Troubleshooting

### Docker volume error when running tests

If you see an error like `OSError: [Errno 16] Device or resource busy: '/fluster/fluster_output'`, this happens because fluster tries to remove the output directory after running tests, but it's mounted as a Docker volume.

**Solution**: Always use the `-k` flag (keep files) when running tests:
```bash
docker/run-docker.sh run -d VVdeC-H266 -ts JVET-VVC_draft6 -k
```
### Complete rebuild
```bash
docker compose -f docker/docker-compose.yml build --no-cache
```
### Verify vvdecapp installation
```bash
docker compose -f docker/docker-compose.yml run --rm fluster vvdecapp --version
```
