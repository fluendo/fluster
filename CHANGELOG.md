# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased
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
- Create CI workflow for automated releases.

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
