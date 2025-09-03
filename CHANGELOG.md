# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0-rc.1] - 2025-09-03
                
### Added
- Add vp9 decoder for vulkan ffmpeg
### Changed
- Automatic CHANGELOG.md updates with python-semantic-release and custom templates
- Rename h26x to h.26x in test_suites
- Update release workflow to update CHANGELOG.md automatically
- Remove is_single_archive argument and related functions
### Fixed
- Set method pixel in MPEG4 video test suites
- Add av1parse element for low rank GStreamer av1 decoders
- Add missing output formats to GStreamer mapping
- Do not fail when output format is not mapped (GStreamer decoders)
- Add pixel method to generators for mpeg2/4 video
- Do not fail when output_format is None

## [0.4.1] - 2025-08-06
                
### Fixed
- Correct upload of CHANGELOG.md to pypi

## [0.4.0] - 2025-08-05
                
### Added
- Add mpeg4 video test suite for simple scalable profile
- Add mpeg4 video test suite for simple studio profile
- Add mpeg4 video test suite for advanced simple profile
- Add mpeg4 video test suite for simple profile
- Add per profile test results to markdown summary report
- Add support for test vector profile as optional parameter
- Add vp9 decoder for VKVS
- Add vulkan vp9 decoder for GStreamer
- Add gst vulkan AV1 decoder
- Support wildcard in list of tests
### Changed
- Add GStreamer Libav "avdec_mpeg4" decoder to gstreamer.py
- Add "flumpeg4vdec" decoder to gstreamer.py
- Add iso_mpeg4_video.py to pass tests with reference decoder (only binary)
- Adapt gen_mpeg4_video.py for simple scalable profile
- Adapt gen_mpeg4_video.py for simple studio profile
- Adapt gen_mpeg4_video.py for advance simple profile
- Add MPEG4 video generator script
- Add FFMpeg mpeg4 video decoder
- Update H.265 test suites with profile information
- Add profile information to H.265 test suite generator
- Add profiles for H.265 test vectors
- Add output format exceptions for some H.264 test vectors
- Update H.264 test suites with profile information
- Add profile information to H.264 test suite generator
- CHANGELOG.md and pyproject.toml updated manually to new 0.4.0 release
- Update documentation for a new release 0.4.0
- Add MPEG4_VIDEO info to README.md
- Update README.md with latest test suites and minor fixes
### Fixed
- Add provider "Fluendo" to FluendoMPEG4VideoDecoder
- Remove handle_terms from MPEG4 video test suites
- Adapt code related to handle_terms parameter
- Fix freeze bug when generating test suite with limited available RAM
- Prevent test suite execution when missing resources
- Vkvs use enablePostProcessFilter

## [0.3.0] - 2025-04-17
                
### Added
- Add a pixel comparison method for codecs that don’t generate identical outputs
- Add vah266dec gstreamer decoder
- Add ISO IEC 13818-4 MPEG2 test suites
### Changed
- Change Pypi version to deploy in a new 0.3.0 release from master
- Add mpeg2v test suites to pyproject.toml
- Add mpeg4 aac mp4 error test suite for aac decoder
- Adds the helper script to generate the test suites
- Add reference decoder mpeg2dec installation to Makefile.
- Remove depedencies from pyproject.toml
- Add some gstreamer mpeg2video decoders
- Omit VP8, VP9 and AV1 Makefile check tests when MacOS
- Rename requirements.txt to requirements-dev.txt
- Remove mypy and ruff from Makefile
- Remove ruff and mypy packages from project requirements
- Replace ubuntu 20.04 with 22.04 in GHA runners due to deprecation
- Change ruff pre-commit hook to automated fix mode
- Add mypy as pre-commit hook in .pre-commit-config.yaml
- Add mpeg2 video decoders information to README.md
- Add "ISO-MPEG2-VIDEO: ISO MPEG2 Video reference" decoder to README.md
- Add test suite for mpeg4 aac mp4 error test vectors
- Update README.md
### Fixed
- Update MPEG4_AAC-MP4-ER.json with new md5sum generated and update iso_mpeg4_aac-er.py for generate interleave multichannel
- Update MPEG4_AAC-MP4.json with new md5sum generated and update iso_mpeg4_aac.py for generate interleave multichannel
- Add new line to the json file
- Split mpeg4 aac test suite into error and non error resilient test vectors
- Create mpeg4 reference decoder for error resilient test vectors

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
