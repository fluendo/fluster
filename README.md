# Fluster

![fluster](https://github.com/fluendo/fluster/workflows/fluster/badge.svg)

Fluster is a testing framework written in Python for decoder conformance. It
is composed of a [CLI](https://en.wikipedia.org/wiki/Command-line_interface)
application that runs a number of test suites with the supported decoders. Its
purpose is to check different decoder implementations against known test suites
with known and proven results. It was originally designed to check the
conformance of H.265/HEVC decoders, but it also supports H.264/AVC, H.266/VVC,
VP8, VP9, AV1 and AAC. It can easily be extended to add more decoders and test
suites.

## Table of Contents

- [Fluster](#fluster)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [How to get started](#how-to-get-started)
  - [How to use](#how-to-use)
  - [Test Suites](#test-suites)
  - [Decoders](#decoders)
  - [CLI usage](#cli-usage)
    - [List](#list)
    - [Run](#run)
    - [Download](#download)
    - [Reference](#reference)
  - [Report](#report)
  - [FAQ](#faq)
    - [Where does the name come from?](#where-does-the-name-come-from)
    - [How can I add a new decoder?](#how-can-i-add-a-new-decoder)
    - [How can I create a new test suite?](#how-can-i-create-a-new-test-suite)
    - [How can I use it to test regressions?](#how-can-i-use-it-to-test-regressions)
    - [How can I contribute?](#how-can-i-contribute)
    - [How can I report an issue?](#how-can-i-report-an-issue)
  - [License](#license)

## Description

Fluster requires **Python 3.6+** to work. It has zero dependencies apart from
that. The [requirements.txt](requirements.txt) file includes Python's modules
used only for development.

The framework works with test suites. Each test suite is associated with one
codec and contains a number of test vectors. Each test vector consists of an
input file and and the expected result. The input file will be fed into each
decoder that supports the codec of the test suite. The file format is a JSON
file. You can find the ones included in the [test_suites](test_suites)
directory.

The decoders are the ones in charge of doing the decoding given an input file.
They implement two methods: `decode` which is mandatory and `check` which is
optional. Check out the [decoder class](fluster/decoder.py) for reference. The
`@register_decoder` decorator is used to ensure the framework takes them into
account. Fluster is agnostic as to how the decoding itself is done. So far, all
decoders are external processes that need to run with a number of parameters,
but they could actually be decoders written in Python as far as Fluster is
concerned. The [decoders](fluster/decoders) directory contains all supported
decoders.

In order to run the tests for the different test suites and decoders, a
`resources` directory containing all the input files for each test suite needs
to be collected first.

## How to get started

- Clone the repository: `git clone https://github.com/fluendo/fluster.git`

or

- [Release source code](https://github.com/fluendo/fluster/releases) assets are available in the following formats zip, tar.gz

Find more about how to use Fluster in the next section.

## How to use

1. Download the resources for the test suites. This will create the `resources`
   directory containing the input files for each test suite. `./fluster.py
   download` will spawn a number of processes to download and extract the
   files. You can change the number of parallel processes used with `-j`. It
   defaults to 2x number of logical cores.

2. (Optional) Build the reference decoders for AAC, H.264/AVC, H.265/HEVC,
   H.266/VVC running `make all_reference_decoders`. It assumes you have CMake
   and a native compiler such as gcc or clang installed so that they can be
   built. The resulting binaries will be moved to a new `decoders` directory in
   the root.

3. List the test suites, the decoders and which of them can run using
   `./fluster.py list -c`.

```bash
List of available test suites:

ISO_IEC_13818-4_2004
    Codec: AAC
    Description: ISO_IEC_13818-4_2004 ADTS conformance test suite
    Test vectors: 62

ISO_IEC_14496-26_2010
    Codec: AAC
    Description: ISO_IEC_14496-26_2010 ADTS conformance test suite
    Test vectors: 9

JCT-VC-HEVC_V1
    Codec: H.265
    Description: JCT-VC HEVC version 1
    Test vectors: 147

JVT-AVC_V1
    Codec: H.264
    Description: JVT AVC version 1
    Test vectors: 135

JVT-FR-EXT
    Codec: H.264
    Description: JVT Fidelity Range Extensions
    Test vectors: 69

JVET-VVC_draft6
    Codec: H.266
    Description: JVET VVC draft6
    Test vectors: 282

VP8-TEST-VECTORS
    Codec: VP8
    Description: VP8 Test Vector Catalogue from https://github.com/webmproject/vp8-test-vectors
    Test vectors: 61

VP9-TEST-VECTORS-HIGH
    Codec: VP9
    Description: VP9 High Bit Depth Test Vectors from https://storage.googleapis.com/downloads.webmproject.org/test_data/libvpx/
    Test vectors: 6

VP9-TEST-VECTORS
    Codec: VP9
    Description: VP9 Test Vector Catalogue from https://storage.googleapis.com/downloads.webmproject.org/test_data/libvpx/
    Test vectors: 305

AV1-TEST-VECTORS
    Codec: AV1
    Description: AV1 Test Vector Catalogue from https://storage.googleapis.com/aom-test-data
    Test vectors: 239

CHROMIUM-8bit-AV1-TEST-VECTORS
    Codec: AV1
    Description: AV1 Test Vector Catalogue from https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/tast-tests/src/chromiumos/tast/local/bundles/cros/video/data/test_vectors/av1/
    Test vectors: 13

CHROMIUM-10bit-AV1-TEST-VECTORS
    Codec: AV1
    Description: AV1 Test Vector Catalogue from https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/tast-tests/src/chromiumos/tast/local/bundles/cros/video/data/test_vectors/av1/
    Test vectors: 23

List of available decoders:

H264
    Chromium-H.264: Chromium H.264 decoder for Chromium... ❌
    FFmpeg-H.264: FFmpeg H.264 SW decoder... ✔️
    FFmpeg-H.264-D3D11VA: FFmpeg H.264 D3D11VA decoder... ❌
    FFmpeg-H.264-DXVA2: FFmpeg H.264 DXVA2 decoder... ❌
    FFmpeg-H.264-VAAPI: FFmpeg H.264 VAAPI decoder... ✔️
    FFmpeg-H.264-VDPAU: FFmpeg H.264 VDPAU decoder... ✔️
    FFmpeg-H.264-h264_v4l2m2m: FFmpeg H.264 h264_v4l2m2m decoder... ✔️
    Fluendo-H.264-HW-Gst1.0: Fluendo H.264 HW decoder for GStreamer 1.0... ❌
    Fluendo-H.264-HW-hwvah264dec-Gst1.0: Fluendo H.264 HW decoder for GStreamer 1.0... ❌
    Fluendo-H.264-SW-Gst0.10: Fluendo H.264 SW decoder for GStreamer 0.10... ❌
    Fluendo-H.264-SW-Gst1.0: Fluendo H.264 SW decoder for GStreamer 1.0... ❌
    GStreamer-H.264-D3D11-Gst1.0: GStreamer H.264 D3D11 decoder for GStreamer 1.0... ❌
    GStreamer-H.264-Libav-Gst1.0: GStreamer H.264 Libav decoder for GStreamer 1.0... ✔️
    GStreamer-H.264-MSDK-Gst1.0: GStreamer H.264 MSDK decoder for GStreamer 1.0... ❌
    GStreamer-H.264-NVDEC-Gst1.0: GStreamer H.264 NVDEC decoder for GStreamer 1.0... ❌
    GStreamer-H.264-NVDECSL-Gst1.0: GStreamer H.264 NVDECSL decoder for GStreamer 1.0... ❌
    GStreamer-H.264-V4L2-Gst1.0: GStreamer H.264 V4L2 decoder for GStreamer 1.0... ❌
    GStreamer-H.264-V4L2SL-Gst1.0: GStreamer H.264 V4L2SL decoder for GStreamer 1.0... ❌
    GStreamer-H.264-VA-Gst1.0: GStreamer H.264 VA decoder for GStreamer 1.0... ❌
    GStreamer-H.264-VAAPI-Gst1.0: GStreamer H.264 VAAPI decoder for GStreamer 1.0... ❌
    JCT-VT-H.264: JCT-VT H.264/AVC reference decoder... ✔️

DUMMY
    Dummy: This is a dummy implementation for the dummy codec... ✔️

AV1
    FFmpeg-AV1-VAAPI: FFmpeg AV1 VAAPI decoder... ✔️
    GStreamer-AV1-D3D11-Gst1.0: GStreamer AV1 D3D11 decoder for GStreamer 1.0... ❌
    GStreamer-AV1-V4L2SL-Gst1.0: GStreamer AV1 V4L2SL decoder for GStreamer 1.0... ❌
    GStreamer-AV1-VA-Gst1.0: GStreamer AV1 VA decoder for GStreamer 1.0... ❌
    GStreamer-AV1-VAAPI-Gst1.0: GStreamer AV1 VAAPI decoder for GStreamer 1.0... ❌
    libaom-AV1: libaom AV1 reference decoder... ✔️

H265
    FFmpeg-H.265: FFmpeg H.265 SW decoder... ✔️
    FFmpeg-H.265-D3D11VA: FFmpeg H.265 D3D11VA decoder... ❌
    FFmpeg-H.265-DXVA2: FFmpeg H.265 DXVA2 decoder... ❌
    FFmpeg-H.265-VAAPI: FFmpeg H.265 VAAPI decoder... ✔️
    FFmpeg-H.265-VDPAU: FFmpeg H.265 VDPAU decoder... ✔️
    Fluendo-H.265-HW-hwvah265dec-Gst1.0: Fluendo H.265 HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-SW-Gst0.10: Fluendo H.265 SW decoder for GStreamer 0.10... ❌
    Fluendo-H.265-SW-Gst1.0: Fluendo H.265 SW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-byte-stream-au-HW-Gst1.0: Fluendo H.265-byte-stream-au HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-byte-stream-nal-HW-Gst1.0: Fluendo H.265-byte-stream-nal HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-hev1-au-HW-Gst1.0: Fluendo H.265-hev1-au HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-hev1-nal-HW-Gst1.0: Fluendo H.265-hev1-nal HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-hvc1-au-HW-Gst1.0: Fluendo H.265-hvc1-au HW decoder for GStreamer 1.0... ❌
    Fluendo-H.265-hvc1-nal-HW-Gst1.0: Fluendo H.265-hvc1-nal HW decoder for GStreamer 1.0... ❌
    GStreamer-H.265-D3D11-Gst1.0: GStreamer H.265 D3D11 decoder for GStreamer 1.0... ❌
    GStreamer-H.265-Libav-Gst1.0: GStreamer H.265 Libav decoder for GStreamer 1.0... ✔️
    GStreamer-H.265-MSDK-Gst1.0: GStreamer H.265 MSDK decoder for GStreamer 1.0... ❌
    GStreamer-H.265-NVDEC-Gst1.0: GStreamer H.265 NVDEC decoder for GStreamer 1.0... ❌
    GStreamer-H.265-NVDECSL-Gst1.0: GStreamer H.265 NVDECSL decoder for GStreamer 1.0... ❌
    GStreamer-H.265-V4L2-Gst1.0: GStreamer H.265 V4L2 decoder for GStreamer 1.0... ❌
    GStreamer-H.265-V4L2SL-Gst1.0: GStreamer H.265 V4L2SL decoder for GStreamer 1.0... ❌
    GStreamer-H.265-VA-Gst1.0: GStreamer H.265 VA decoder for GStreamer 1.0... ❌
    GStreamer-H.265-VAAPI-Gst1.0: GStreamer H.265 VAAPI decoder for GStreamer 1.0... ❌
    JCT-VT-H.265: JCT-VT H.265/HEVC reference decoder... ✔️

VP8
    FFmpeg-VP8: FFmpeg VP8 SW decoder... ✔️
    FFmpeg-VP8-VAAPI: FFmpeg VP8 VAAPI decoder... ✔️
    FFmpeg-VP8-vp8_v4l2m2m: FFmpeg VP8 vp8_v4l2m2m decoder... ✔️
    GStreamer-VP8-D3D11-Gst1.0: GStreamer VP8 D3D11 decoder for GStreamer 1.0... ❌
    GStreamer-VP8-Libav-Gst1.0: GStreamer VP8 Libav decoder for GStreamer 1.0... ✔️
    GStreamer-VP8-NVDEC-Gst1.0: GStreamer VP8 NVDEC decoder for GStreamer 1.0... ❌
    GStreamer-VP8-NVDECSL-Gst1.0: GStreamer VP8 NVDECSL decoder for GStreamer 1.0... ❌
    GStreamer-VP8-V4L2-Gst1.0: GStreamer VP8 V4L2 decoder for GStreamer 1.0... ❌
    GStreamer-VP8-V4L2SL-Gst1.0: GStreamer VP8 V4L2SL decoder for GStreamer 1.0... ❌
    GStreamer-VP8-VA-Gst1.0: GStreamer VP8 VA decoder for GStreamer 1.0... ❌
    GStreamer-VP8-VAAPI-Gst1.0: GStreamer VP8 VAAPI decoder for GStreamer 1.0... ❌
    GStreamer-VP8-libvpx-Gst1.0: GStreamer VP8 libvpx decoder for GStreamer 1.0... ✔️
    libvpx-VP8: VP8 reference decoder... ✔️

VP9
    FFmpeg-VP9: FFmpeg VP9 SW decoder... ✔️
    FFmpeg-VP9-VAAPI: FFmpeg VP9 VAAPI decoder... ✔️
    FFmpeg-VP9-vp9_v4l2m2m: FFmpeg VP9 vp9_v4l2m2m decoder... ✔️
    GStreamer-VP9-D3D11-Gst1.0: GStreamer VP9 D3D11 decoder for GStreamer 1.0... ❌
    GStreamer-VP9-Libav-Gst1.0: GStreamer VP9 Libav decoder for GStreamer 1.0... ✔️
    GStreamer-VP9-NVDEC-Gst1.0: GStreamer VP9 NVDEC decoder for GStreamer 1.0... ❌
    GStreamer-VP9-NVDECSL-Gst1.0: GStreamer VP9 NVDECSL decoder for GStreamer 1.0... ❌
    GStreamer-VP9-V4L2SL-Gst1.0: GStreamer VP9 V4L2SL decoder for GStreamer 1.0... ❌
    GStreamer-VP9-VA-Gst1.0: GStreamer VP9 VA decoder for GStreamer 1.0... ❌
    GStreamer-VP9-VAAPI-Gst1.0: GStreamer VP9 VAAPI decoder for GStreamer 1.0... ❌
    GStreamer-VP9-libvpx-Gst1.0: GStreamer VP9 libvpx decoder for GStreamer 1.0... ✔️
    libvpx-VP9: VP9 reference decoder... ✔️

AAC
    Fluendo-AAC-SW-Gst1.0: Fluendo AAC SW decoder for GStreamer 1.0... ✔️
    ISO-MPEG4-AAC: ISO MPEG4 AAC reference decoder... ✔️

H266
    GStreamer-H.266-VVdeC-Gst1.0: GStreamer H.266 VVdeC decoder for GStreamer 1.0... ✔
    VVdeC-H266: VVdeC H.266/VVC reference decoder... ✔️

```

4. Run the test suite (or a number of them) for all decoders (or a number of
   them). By default, decoder tests are run in parallel. By default fluster uses the same
   amount of parallel jobs as number of cores, but it can be configured using
   the `-j` option. You can pass `-d` to filter only the decoders that you want
   to run, `-ts` for the test suites and `-tv` for the test vectors. Examples:

    - `./fluster.py run` runs all test suites for all decoders available that
      match each test suite's codec.
    - `./fluster.py run -ts JCT-VC-HEVC_V1` runs the *JCT-VC-HEVC_V1* test
      suite for all decoders that support H.265/HEVC.
    - `./fluster.py run -ts JCT-VC-HEVC_V1 -tv AMP_A_Samsung_7` runs only the
      test vector *AMP_A_Samsung_7* of the *JCT-VC-HEVC_V1* test suite.
    - `./fluster.py run -d FFmpeg-H.265` runs the *FFmpeg-H265* decoder on all
      test suites for H.265/HEVC.
    - `./fluster.py run -d FFmpeg-H.265 -j1` runs the *FFmpeg-H265* decoder on all
      test suites for H.265/HEVC using one job.

## Test Suites

- Dummy test suite for testing purposes.
- [AAC](https://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_IEC_13818-4_2004_Conformance_Testing/AAC/).
- [AAC](https://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_IEC_14496-26_2010_Bitstreams/DVD1/mpeg4audio-conformance/).
- [AV1](https://storage.googleapis.com/aom-test-data/).
- [AV1](https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:src/platform/tast-tests/src/chromiumos/tast/local/bundles/cros/video/data/test_vectors/av1/).
- [H.264/AVC](https://www.itu.int/wftp3/av-arch/jvt-site/draft_conformance/).
- [H.265/HEVC](https://www.itu.int/wftp3/av-arch/jctvc-site/bitstream_exchange/draft_conformance/).
- [H.266/VVC](https://www.itu.int/wftp3/av-arch/jvet-site/bitstream_exchange/VVC/draft_conformance/).
- [VP8](https://github.com/webmproject/vp8-test-vectors).
- [VP9](https://storage.googleapis.com/downloads.webmproject.org/test_data/libvpx).

## Decoders

- Dummy decoder for testing purposes.
- [JCT-VT H.264/AVC](https://vcgit.hhi.fraunhofer.de/jvet/JM) as reference
  decoder for H.264/AVC.
- [JCT-VT H.265/HEVC](https://vcgit.hhi.fraunhofer.de/jvet/HM) as reference
  decoder for H.265/HEVC.
- [JCT-VT H.266/VVC](https://vcgit.hhi.fraunhofer.de/jvet/VVCSoftware_VTM) as reference
  decoder for H.266/VVC.
- Fluendo's proprietary decoders for H.264/AVC and H.265/HEVC that are included
  in [Fluendo Codec
  Pack](https://fluendo.com/en/products/enterprise/fluendo-codec-pack/).
- [GStreamer's](https://gstreamer.freedesktop.org/) for H.266/VVC.
- [GStreamer's](https://gstreamer.freedesktop.org/) for H.265/HEVC.
- [GStreamer's](https://gstreamer.freedesktop.org/) for H.264/AVC.
- [FFmpeg's](https://FFmpeg.org) for H.265/HEVC.
- [FFmpeg's](https://FFmpeg.org) for H.264/AVC.
- [libvpx's](https://github.com/webmproject/libvpx/) for VP8.
- [libvpx's](https://github.com/webmproject/libvpx/) for VP9.
- [aom's](https://aomedia.googlesource.com/aom/) for AV1.

## CLI usage

```bash
./fluster.py --help

usage: fluster.py [-h] [-r RESOURCES] [-o OUTPUT] [-ne] [-tsd TEST_SUITES_DIR]
{list,l,run,r,download,d,reference,f} ...

optional arguments:
  -h, --help            show this help message and exit
  -r RESOURCES, --resources RESOURCES
                        set the directory where resources are taken from
  -o OUTPUT, --output OUTPUT
                        set the directory where decoder outputs will be stored
  -ne, --no-emoji       set to use plain text instead of emojis
  -tsd TEST_SUITES_DIR, --test-suites-dir TEST_SUITES_DIR
                        set directory where test suite will be read from, multiple directories are supported with OS path separator (:)

subcommands:
  {list,l,run,r,download,d,reference,f}
    list (l)            show list of available test suites and decoders
    run (r)             run test suites for decoders
    download (d)        downloads test suites resources
    reference (f)       use a specific decoder to set its results for the test
                        suites given
```

### List

```bash
./fluster.py list --help

usage: fluster.py list [-h] [-ts TESTSUITES [TESTSUITES ...]] [-tv] [-c] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -ts TESTSUITES [TESTSUITES ...], --testsuites TESTSUITES [TESTSUITES ...]
                        show only the test suites given
  -tv, --testvectors    show test vectors of test suites
  -c, --check           check which decoders can be run successfully. Reports ✔️ or ❌
  -v, --verbose         show stdout and stderr of commands executed
```

### Run

```bash
./fluster.py run --help

usage: fluster.py run [-h] [-j JOBS] [-t TIMEOUT] [-ff] [-q]
[-ts TESTSUITES [TESTSUITES ...]] [-tv TESTVECTORS [TESTVECTORS ...]]
[-sv SKIPVECTORS [SKIPVECTORS ...]] [-d DECODERS [DECODERS ...]] [-s]
[-so SUMMARY_OUTPUT] [-f {md,csv,junitxml}] [-k] [-th THRESHOLD]
[-tth TIME_THRESHOLD] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 1x logical cores by
                        default.0 means all logical cores
  -t TIMEOUT, --timeout TIMEOUT
                        timeout in secs for each decoding. Defaults to 30 secs
  -ff, --failfast       stop after first fail
  -q, --quiet           don't show every test run
  -ts TESTSUITES [TESTSUITES ...], --testsuites TESTSUITES [TESTSUITES ...]
                        run only the specific test suites
  -tv TESTVECTORS [TESTVECTORS ...], --testvectors TESTVECTORS [TESTVECTORS ...]
                        run only the specific test vectors
  -sv SKIPVECTORS [SKIPVECTORS ...], --skipvectors SKIPVECTORS [SKIPVECTORS ...]
                        skip the specific test vectors
  -d DECODERS [DECODERS ...], --decoders DECODERS [DECODERS ...]
                        run only the specific decoders
  -s, --summary         generate a summary in Markdown format for each test
                        suite
  -so SUMMARY_OUTPUT, --summary-output SUMMARY_OUTPUT
                        dump summary output to file
  -f {md,csv,junitxml}, --format {md,csv,junitxml}
                        specify the format for the summary file
  -k, --keep            keep output files generated during the test
  -th THRESHOLD, --threshold THRESHOLD
                        set exit code to 2 if threshold tests are not success.
                        exit code is 0 otherwise
  -tth TIME_THRESHOLD, --time-threshold TIME_THRESHOLD
                        set exit code to 3 if test suite takes longer than
                        threshold seconds. exit code is 0 otherwise
  -v, --verbose         show stdout and stderr of commands executed
```

### Download

```bash
./fluster.py download --help

usage: fluster.py download [-h] [-j JOBS] [-k] [testsuites [testsuites ...]]

positional arguments:
  testsuites            list of testsuites to download

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 2x logical cores by
                        default.0 means all logical cores
  -k, --keep            keep original downloaded file after extracting. Only
                        applicable to compressed files such as .zip, .tar.gz,
                        etc
```

### Reference

```bash
./fluster.py reference --help

usage: fluster.py reference [-h] [-j JOBS] [-t TIMEOUT] [-q] [-v]
decoder testsuites [testsuites ...]

positional arguments:
  decoder               decoder to run
  testsuites            list of testsuites to run the decoder with

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 1x logical cores by
                        default.0 means all logical cores
  -t TIMEOUT, --timeout TIMEOUT
                        timeout in secs for each decoding. Defaults to 30 secs
  -q, --quiet           don't show every test run
  -v, --verbose         show stdout and stderr of commands executed
```

## Report

[Go to report](REPORT.md)

## FAQ

### Where does the name come from?

Fluster in English means [to (cause to) become nervous or
confused](https://www.wordreference.com/definition/fluster). It looks like a
very appropriate name for testing decoders.

### How can I add a new decoder?

1. Create a new decoder in [fluster/decoders](fluster/decoders) directory.
2. Implement the `decode` method.
3. Use the `register_decoder` decorator.
4. Ensure to set `hw_acceleration = True` if it requires hardware.
5. Optionally, implement the `check` to know whether the decoder is available
   to be run.

### How can I create a new test suite?

Check out the JSON format they follow in the [test_suites](test_suites)
directory. Add a new json file within, Fluster will automatically pick it
up.

There is also a [generator script](scripts/gen_jct_vc.py) for the [conformance
test suites](#test_suites) that you can use as a base to generate automatically
new ones.

### How can I use it to test regressions?

We can easily use Fluster in a CI to test that our test suites for particular
decoders are still working as good as they were before. There are two arguments
to be used with the [run](#run) command that can help us achieve that. Both
commands work only when running a single test suite:

1. `-th/--threshold` sets the minimum number of tests that need to succeed
   in order to consider the command not a failure. In case of failure, the exit
   code is 2. Please notice that even if some tests fail, the exit code will
   still be 0 as long as the threshold is met.

2. `-tth/--time-threshold` sets the maximum amount of time for a test suite to
   run and still be considered a success. The exit code is 3 in case it takes
   longer and 0 otherwise. Please note that even if some tests fail, the exit
   code will still be 0 as long as the time it takes is less than the threshold.

However, in case we want to be even more explicit, ensuring exactly the same
results are obtained, we can do the following procedure:

1. Store well-known results in an expected file with the output of Fluster's
   run.
2. Run Fluster again and compare with the expected result using diff. The
   following command will return an `exitStatus` different from 0 in case
   there's any difference.

   ```bash
   diffParams='-uB -I"|Test|" --strip-trailing-cr'
   diff $diffParams expected.out current.out
   ```

   We recommend using the `--no-emoji` argument when running on the CI to
   ensure the log is properly displayed with no issues.

### How can I contribute?

1. Fork the repo.
2. Install the required Python modules for development using `pip3 install -r
   requirements.txt`.
3. Install the [git hook](scripts/install_git_hook.sh) that will run for every
   commit to ensure it works before pushing. [About git
   hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).
4. Modify the code. Make sure the git hook is properly checking that the basic
   functionality still works. You can also execute `make check` manually. Take
   into account that some basic tests are run to ensure that GStreamer, FFmpeg
   and libvpx decoders are working fine. Thus, you need to have them available.
   On an Ubuntu 20.04 the needed packages are:

   ```bash
   gstreamer1.0-tools gstreamer1.0-libav gstreamer1.0-plugins-bad ffmpeg
   vpx-tools aom-tools
   ```

5. Create a new PR with your changes.
6. Make sure the GitHub Actions is running and its result is a pass.

### How can I report an issue?

In case you find any problem or want to report something, don't hesitate to
search for similar [issues](issues). Only when the issue can't be found, a new
one should be created. Please try to provide as many details and context as
possible to help us diagnose it.

## License

**LGPLv3**

```none
Fluster - testing framework for decoders conformance
Copyright (C) 2020-2022, Fluendo, S.A.
  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library. If not, see <https://www.gnu.org/licenses/>.
```
