# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] (2025-08-05)
### Added
- GStreamer Vulkan AV1 VA decoder
- GStreamer Vulkan VP9 VA decoder
- NVidia Vulkan Video Samples VP9 VA decoder
- GStreamer Libav MPEG-4 SW video decoder
- Fluendo GStreamer MPEG-4 SW video decoder
- FFmpeg MPEG-4 SW video decoder
- ISO MPEG-4 video reference decoder (Microsoft implementation - vmdec)
- MPEG-4 video test suites for simple, advanced simple, simple scalable and simple studio profiles

### Changed
- Test execution summary report in markdown format now includes test results per profile, when available
- Wildcard(*) is now supported when setting a list of vectors to test
- H.264 test suites JVT-AVC_V1, JVT-FR-EXT and JVT-Professional_profiles now include profile for test vectors
- H.265 test suite JCT-VC-HEVC_V1 now includes profile for test vectors

### Fixed
- Prevent test suite execution when its resources are not found locally
- Nvidia Vulkan video samples decoder: use enablePostProcessFilter by default to support hardware with different queue for decoding and transferring, such as mesa drivers


## [0.3.0] (2025-04-17)
### Added
- Pixel-by-pixel output/reference frame comparison method with error tolerance is now available for codecs that 
do not require checksum match. MPEG-2 is an example of such codecs.
- MPEG-2 video test suites for main and 4:2:2 profiles
- GStreamer H.266 VA decoder
- ISO MPEG-4 reference decoder for test vectors of error resilient profiles
- GStreamer MPEG-2 SW video decoder
- Gstreamer Libva MPEG-2 SW video decoder

### Changed

### Fixed
- MPEG-4 AAC MP4 test suite was split in 2, error and not error-resilient ones
- MPEG-4 AAC MP4 test suites, error and not error-resilient now have correct md5 checksums
- ISO MPEG-4 AAC decoders, error and not error-resilient now generate output with interleaved channels, when required


## [0.2.0] - 2025-01-27
### Added
- Generate a test suite for H265 3D-HEVC functionality set.
- Generate a test suite for H265 SHVC functionality set.
- Create a test suite for H264 SVC group.
- Create a test suite for H264 professional profiles.
- Create a test suite for AV1 based on the Argon Streams.
- Create a test suite for MPEG-4 AAC adif files.
- Create a test suite for MPEG-4 AAC mp4 files.
- Add H264 FRExt test suite.
- Add H264 MVC test suite.
- Add MPEG-2 AAC adif test suite.
- Add MPEG4-AAC-ADTS test suite.
- Add basic AV1 tests for Makefile check target.
- Adapt AV1 AOM decoder so that it works correctly with some Argon test vectors.
- Add VVCSoftware_VTM H.266/VVC reference decoder.
- Add md5 checksum read/write feature to H266 test suite generator script.
- Create a test suite generator script for AAC.
- Add GStreamer libaom based AV1 decoder

### Changed
- Split test suites for H265 and H266.
- Adapt AAC test suite generator to omit md5 checksums of wav reference.
- Rename some AAC and H264 test suites to be more precise.
- Replace pylint and black with ruff linter and code formatter.
- Update README.md.
- Update REPORT.md.

### Fixed
- Fix bug #218: Argon AV1 test resource path don't match the downloaded resources path.
- Issue in JSON generation scripts (Some test suites are badly generated).


## [0.1.0] - 2022-12-20
### Added
- Add the H.264 reference decoder.
- Add libvpx-VP8 reference decoder.
- Add VP9 reference decoder.
- Add AAC reference decoder.
- Add AV1 reference decoder.
- Add VVdeC reference decoder.
- Create a test suite for H264 AVC-V1.
- Create a test suite for H264 RExt.
- Create a test suite for H265 HEVC_V1.
- Create a test suite for H265 MV-HEVC.
- Create a test suite for H265 SCC.
- Create a test suite for AV1 functionality set.
- Create a test suite for AV1 CHROMIUM-8bit.
- Create a test suite for AV1 CHROMIUM-10bit.
- Create a test suite for VP8-TEST-VECTORS.
- Create a test suite for VP9-TEST-VECTORS.
- Create a test suite for VP9-TEST-VECTORS-HIGH.
- Create a test suite for MPEG-2 AAC.
- Create a test suite for H.266 (VTT).
- Create README.md.
- Create REPORT.md.

## Notes
- For detailed usage and fluster modes, refer to the [README.md](README.md).
