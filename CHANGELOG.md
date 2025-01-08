# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased
### Added
- Generate a test suite in fluster for H265 3D-HEVC functionality set.
- Generate a test suite in fluster for H265 SHVC functionality set.
- Create a test suite for H264 SVC group.
- Create a test suite in fluster for H264 professional profiles.
- Create a test suite for AV1 based on the Argon Streams.
- Create a test suite for MPEG-4 AAC adif files.
- Create a test suite for MPEG-4 AAC mp4 files.
- Add H264 FRExt test suite generator to fluster.
- Add H264 MVC test suite to fluster.
- Add MPEG-2 AAC adif test suite to fluster.
- Add and test the MPEG4-AAC-ADTS generator in fluster.
- Add basic AV1 tests for Makefile check target.
- Adapt AV1 AOM decoder so that it works correctly with some Argon test vectors.
- Add md5 checksum read/write feature to H266 test suite generator script.
- Create a test suite generator script for AAC in fluster.
- Create CI workflow for automated fluster releases.

### Changed
- Split test suites for H265 and H266.
- Adapt AAC test suite generator to omit md5 checksums of wav reference.
- Rename some AAC and H264 test suites to be more precise.
- Replace pylint and black with ruff linter and code formatter.
- Update README.md
- Update REPORT.md

### Fixed
- Fix bug #218: Argon AV1 test resource path don't match the downloaded resources path.
- Check out and fix av1 argon vector path issues.
- Issue in JSON generation scripts (Some test suites are badly generated).

## [0.1.0] - 2022-12-20
### Added
- Refactor list as a subcommand.
- Consolidate test suites and decoder arg into list.
- Add copyright to every source file.
- Add decoder argument.
- Add running given test suites and decoders.
- Add script use autopep8 and pylint.
- Add a command to download test suites.
- Add a new script that generates test suites from JCT-VT.
- Add the JCT-VC-HEVC-V1 test suite.
- Use md5 checksums instead of sha256.
- Store raw decoder outputs from tests.
- Add the JCT-VT decoder implementation.
- gen_jct_vc: generate the H264 conformance test suite.
- Add the H.264 reference decoder implementation.
- Add the H264 decoder conformance test suite.
- decoders: add Fluendo's H264 software decoders.
- Run smoke tests with the dummy decoder.
- Add run check for decoders.
- Register vaapih265dec H265 decoder.
- Remove community VA-API decoder for GStreamer 0.10.
- Add AVC/HEVC decoder from the new VA plugin.
- Add avdec_h264 decoder.
- Add fluvah265dec decoder.
- Add hev1 and hvc1 decoder.
- Add FFmpeg vdpau decoder.
- Add fluvah264dec decoder.
- Add V4L2 stateless decoder support.
- Add VP8-TEST-VECTORS.
- Add libvpx-VP8 reference decoder.
- Add VP9 reference decoder and test vectors.
- Add VP9 FFmpeg decoder.
- Add v4l2slvp8dec decoder.
- gstreamer: Add vavp8dec support.
- ffmpeg: Add VAAPI VP9 decoder.
- gstreamer: Add VP9 decoders.
- gstreamer: Add D3D11 and Libav VP8/VP9 decoders.
- Upgrade to Python 3.7 after adding annotations.
- Add AAC reference decoder.
- Add support in Fluster for Windows.
- CI: Run CI in linux and Windows.
- Add minimal tests for GStreamer, FFmpeg and libvpx.
- gstreamer: Add Nvidia hevc VDPAU decoder.
- Add GStreamer NVDEC decoders to fluster.
- Add H.266 (VTT) test suite and VVdeC reference decoder.
- Add AV1 reference decoder and test vectors.
- gstreamer: Add H264, H265 and VP8 V4L2 stateful decoder.
- Add support for V4L2Codecs AV1 decoder.
- Add support for vaapi based AV1 decoders.
- Add AV1 gstreamer-vaapi decoder as well.
- gstreamer: Add D3D11 AV1 decoder.
- Add support for generating JUnit XML summary.
- av1: add chromium 8bit and 10bit test vectors.
- Update AV1 10bits test suites.
- Add support for generating CSV summaries.
- Add FFMPEG V4L2 stateful M2M decoder for VP8, VP9 and H264.
- Add JVT Fidelity Range Extensions tests.
- Add pyproject.toml.
- Add 422 10bit support.
- Add VP9 libvpx high bit depth test vectors.
- Add VP9 libvpx 422 and 444 leftovers.
- Create README.md.
- Create REPORT.md.

### Fixed
- Fix test suites to pass tests.
- Fix filtering of test suites and decoders to run.
- Fix deserialization of the codec field.
- Fix exit code in case no tests are run.
- Fix summary file when running multiple suites.
- Fix JVT-FR-EXT output formats.
- Fix GA CI failures due to distro upgrade from Ubuntu 20.04 to 22.04.

## Notes
- For detailed usage and fluster modes, refer to the [README.md](README.md).
