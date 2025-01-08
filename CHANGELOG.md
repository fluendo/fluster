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
- Create test_suite for AV1 based on the Argon Streams.
- Create a new test suite for MPEG-4 AAC adif files.
- Create a new test suite for MPEG-4 AAC mp4 files.
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

### Fixed

## Notes
- For detailed usage and fluster modes, refer to the [README.md](README.md).
