# Fluster

![fluster](https://github.com/fluendo/fluster/workflows/fluster/badge.svg)

Fluster is a testing framework written in Python for decoders conformance. It
is composed of a [CLI](https://en.wikipedia.org/wiki/Command-line_interface)
application that runs a number of test suites with the supported decoders. Its
purpose is to check different decoder implementations against known test suites
with known and tested results. It has been originally designed to check the
conformance of H.265/HEVC decoders, but it also supports H.264/AVC and can be
easily extended to add more decoders and test suites.

## Table of Contents

- [Fluster](#fluster)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
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

## How to use

1. Download the resources for the test suites. This will create the `resources`
   directory containing the input files for each test suite. `./fluster.py
   download` will spawn a number of processes to download and extract the
   files. You can change the number of parallel processes used with `-j`. It
   defaults to 2x number of logical cores.

2. (Optional) Build the reference decoders for H.264/AVC and H.265/HEVC running
   `make decoders`. It assumes you have CMake and a native compiler such as gcc
   or clang installed so that they can be built. The resulting binaries will be
   moved to a new `decoders` directory in the root.

3. List the test suites, the decoders and which of them can run using
   `./fluster.py list -c`

```none
List of available test suites:

JVT-AVC_V1
    Codec: Codec.H264
    Description: JVT AVC version 1
    Test vectors: 135

JCT-VC-HEVC_V1
    Codec: Codec.H265
    Description: JCT-VC HEVC version 1
    Test vectors: 147

dummy
    Codec: Codec.Dummy
    Description: Dummy test suite
    Test vectors: 1

List of available decoders:

Dummy
    Dummy: This is a dummy implementation for the dummy codec ✔️
H264
    Fluendo-H.264-SW-Gst0.10: Fluendo H.264 SW decoder for GStreamer 0.10 ❌
    Fluendo-H.264-SW-Gst1.0: Fluendo H.264 SW decoder for GStreamer 1.0 ❌
    GStreamer-H.264-VA-API-Gst1.0: GStreamer H.264 VA-API decoder for GStreamer 1.0 ✔️
    JCT-VT-H264: JCT-VT H.264/AVC reference decoder ✔️
    ffmpeg-H264: ffmpeg H.264 decoder ✔️
H265
    Fluendo-H.265-HW-Gst1.0: Fluendo H.265 HW decoder for GStreamer 1.0 ✔️
    Fluendo-H.265-SW-Gst0.10: Fluendo H.265 SW decoder for GStreamer 0.10 ❌
    Fluendo-H.265-SW-Gst1.0: Fluendo H.265 SW decoder for GStreamer 1.0 ❌
    GStreamer-H.265-VA-API-Gst1.0: GStreamer H.265 VA-API decoder for GStreamer 1.0 ✔️
    JCT-VT-H265: JCT-VT H.265/HEVC reference decoder ✔️
    ffmpeg-H265: ffmpeg H.265 decoder ✔️
```

4. Run the test suite (or a number of them) for all decoders (or a number of
   them). By default, hardware-accelerated decoders run tests sequentially,
   while software decoders run them in parallel. By default it uses the same
   amount of parallel jobs as number of cores, but it can be configured using
   the `-j` option. You can pass `-d` to filter only the decoders that you want
   to run, `-ts` for the test suites and `-tv` for the test vectors. Examples:

    - `./fluster.py run` runs all test suites for all decoders available that
      match each test suite's codec
    - `./fluster.py run -ts JCT-VC-HEVC_V1` runs the *JCT-VC-HEVC_V1* test
      suite for all decoders that support H.265/HEVC
    - `./fluster.py run -ts JCT-VC-HEVC_V1 -tv AMP_A_Samsung_7` runs only the
      test vector *AMP_A_Samsung_7* of the *JCT-VC-HEVC_V1* test suite
    - `./fluster.py run -d ffmpeg-H265` runs the *ffmpeg-H265* decoder on all
      test suites for H.265/HEVC
    - `./fluster.py run -d ffmpeg-H265 -j1` runs the *ffmpeg-H265* decoder on all
      test suites for H.265/HEVC using one job

## Test Suites

- [H.264/AVC](https://www.itu.int/wftp3/av-arch/jctvc-site/bitstream_exchange/draft_conformance/)
- [H.265/HEVC](https://www.itu.int/wftp3/av-arch/jvt-site/draft_conformance/)
- Dummy test suite for testing purposes

## Decoders

- [JCT-VT H.264/AVC](https://vcgit.hhi.fraunhofer.de/jct-vc/JM) as reference
  decoder for H.264/AVC
- [JCT-VT H.265/HEVC](https://vcgit.hhi.fraunhofer.de/jct-vc/HM) as reference
  decoder for H.265/HEVC
- GStreamer's
  [vaapih265dec](https://gstreamer.freedesktop.org/documentation/vaapi/vaapih265dec.html)
  for H.265/HEVC
- GStreamer's
  [vaapih264dec](https://gstreamer.freedesktop.org/documentation/vaapi/vaapih264dec.html)
  for H.264/AVC
- [ffmpeg's](https://ffmpeg.org) H.265/HEVC
- [ffmpeg's](https://ffmpeg.org) H.264/AVC
- Fluendo's propietary decoders for H.264/AVC and H.265/HEVC that are included
  in [Fluendo Codec
  Pack](https://fluendo.com/en/products/enterprise/fluendo-codec-pack/)
- Dummy decoder for testing purposes

## CLI usage

```
usage: fluster.py [-h] [-v] {list,l,run,r,download,d,reference} ...

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity

subcommands:
  {list,l,run,r,download,d,reference}
    list (l)            show list of available test suites and decoders
    run (r)             run test suites for decoders
    download (d)        downloads test suites resources
    reference (r)       use a specific decoder to set its results for the test suites given
```

### List

```
/fluster.py list --help
usage: fluster.py list [-h] [-ts TESTSUITES [TESTSUITES ...]] [-tv] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -ts TESTSUITES [TESTSUITES ...], --testsuites TESTSUITES [TESTSUITES ...]
                        show only the test suites given
  -tv, --testvectors    show test vectors of test suites
  -c, --check           check which decoders can be run successfully. Reports ✔️ or ❌
```

### Run

```
./fluster.py run --help
usage: fluster.py run [-h] [-j JOBS] [-t TIMEOUT] [-ff] [-q] [-ts TESTSUITES [TESTSUITES ...]] [-tv TESTVECTORS [TESTVECTORS ...]] [-d DECODERS [DECODERS ...]] [-s] [-k]

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 1x logical cores by default.0 means all logical cores
  -t TIMEOUT, --timeout TIMEOUT
                        timeout in secs for each decoding. Defaults to 5 secs
  -ff, --failfast       stop after first fail
  -q, --quiet           don't show every test run
  -ts TESTSUITES [TESTSUITES ...], --testsuites TESTSUITES [TESTSUITES ...]
                        run only the specific test suites
  -tv TESTVECTORS [TESTVECTORS ...], --testvectors TESTVECTORS [TESTVECTORS ...]
                        run only the specific test vectors
  -d DECODERS [DECODERS ...], --decoders DECODERS [DECODERS ...]
                        run only the specific decoders
  -s, --summary         generate a summary in Markdown format for each test suite
  -k, --keep            keep output files generated during the test
```

### Download

```
./fluster.py download --help
usage: fluster.py download [-h] [-j JOBS] [-k] [testsuites [testsuites ...]]

positional arguments:
  testsuites            list of testsuites to download

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 2x logical cores by default.0 means all logical cores
  -k, --keep            keep downloaded file after extracting
```

### Reference

```
./fluster.py reference --help
usage: fluster.py reference [-h] [-j JOBS] [-t TIMEOUT] [-q] decoder testsuites [testsuites ...]

positional arguments:
  decoder               decoder to run
  testsuites            list of testsuites to run the decoder with

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  number of parallel jobs to use. 1x logical cores by default.0 means all logical cores
  -t TIMEOUT, --timeout TIMEOUT
                        timeout in secs for each decoding. Defaults to 5 secs
  -q, --quiet           don't show every test run
```

## Report

[Go to report](REPORT.md)

## FAQ

### Where does the name come from?

Fluster in English means [to (cause to) become nervous or
confused](https://www.wordreference.com/definition/fluster). It looks a very
appropriate name for testing decoders.

### How can I add a new decoder?

1. Create a new decoder in [fluster/decoders](fluster/decoders) directory
2. Implement the `decode` method
3. Use the `register_decoder` decorator
4. Ensure to set `hw_acceleration = True` if it requires hardware
5. Optionally, implement the `check` to know whether the decoder is available
   to be run

### How can I create a new test suite?

Check out the JSON format they follow in the [test_suites](test_suites)
directory. Add a new json file within and Fluster will automatically pick it
up.

There is also a [generator script](scripts/gen_jct_vc.py) for the [conformance
test suites](#test_suites) that you can use as a base to generate automatically
new ones.

### How can I contribute?

1. Fork the repo
2. Install the required Python modules for development using `pip3 install -r
   requirements.txt`
3. Install the [git hook](scripts/install_git_hook.sh) that will run for every
   commit to ensure it works before pushing. [About git
   hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
4. Modify the code . Make sure the git hook is properly checking that the
   basic functionality still works. You can also execute `make check` manually
5. Create a new PR with your changes
6. Make sure the GitHub Actions is running and its result is a pass

### How can I report an issue?

In case you find any problem or want to report something, don't hesitate to
search for similar [issues](issues). Only when the issue can't be found, a new
one should be created. Please try to provide as many details and context as
possible to help us diagnose it.

## License

**LGPLv3**

```none
Fluster - testing framework for decoders conformance
Copyright (C) 2020, Fluendo, S.A.
  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Library General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Library General Public
License along with this library; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
```
