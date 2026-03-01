% FLUSTER(1)

<!---
To view the generated manpage:

$ pandoc debian/fluster.1.md -s -t man | man -l -
-->

# NAME

fluster – Testing framework for video decoder conformance

# SYNOPSIS

**fluster** [**-h**] [**-r** *RESOURCES*] [**-o** *OUTPUT*] [**-ne**] [**-tsd** *TEST_SUITES_DIR*] *{list,l,run,r,download,d,reference,f}*

# DESCRIPTION

**fluster** is a testing framework written in Python for video decoder
conformance. It is composed of a command-line application that runs a number of
test suites with the supported decoders. Its purpose is to check different
decoder implementations against known test suites with known and proven results.
It was originally designed to check the conformance of H.265/HEVC decoders, but
it also supports H.264/AVC, H.266/VVC, VP8, VP9, AV1 and AAC.

# OPTIONS

**\-h**, **\-\-help**
: Show help message and exit.

**\-r** *RESOURCES*, **\-\-resources** *RESOURCES*
: Set the directory where resources are taken from.

**\-o** *OUTPUT*, **\-\-output** *OUTPUT*
: Set the directory where test results will be stored.

**\-ne** *OUTPUT*, **\-\-no\-emoji**
: Set to use plain text instead of emojis.

**\-tsd** *TEST_SUITES_DIR*, **\-\-test\-suites\-dir** *TEST_SUITES_DIR*
: Set the directory where test suite will be read from.

# FLUSTER COMMANDS

**list** **\(l\)**
: Show a list of available test suites and decoders.

**run** **\(r\)**
: Run test suites for decoders.

    Options:
    : **\-j** *JOBS*, **\-\-jobs** *JOBS*
        : Number of parallel jobs to use. 1x logical cores by default. 0 means all logical cores.

    : **\-t** *TIMEOUT*, **\-\-timeout** *TIMEOUT*
        : Timeout in secs for each decoding. Defaults to 30 secs.

    : **\-ff**, **\-\-failfast**
        : Stop after first fail.

    : **\-q**, **\-\-quiet**
        : Don't show every test run.

    : **\-ts** *TESTSUITES*, **\-\-testsuites** *TESTSUITES*
        : Run only the specific test suites.

    : **\-tv** *TESTVECTORS*, **\-\-testvectors** *TESTVECTORS*
        : Run only the specific test vectors.

    : **\-d** *DECODERS*, **\-\-decoders** *DECODERS*
        : Run only the specific decoders.

    : **\-s**, **\-\-summary**
        : Generate a summary in Markdown format for each test suite.

    : **\-so** *SUMMARY_OUTPUT*, **\-\-summary\-output** *SUMMARY_OUTPUT*
        : Dump summary output to file.

    : **\-f** *\{md,csv,junitxml\}*, **\-\-format** *\{md,csv,junitxml\}*
        : Specify the format for the summary file.

    : **\-k**, **\-\-keep**
        : Keep output files generated during the test.

    : **\-th** *THRESHOLD*, **\-\-threshold** *THRESHOLD*
        : Set exit code to 2 if threshold tests are not success. Exit code is 0 otherwise.

    : **\-tth** *TIME_THRESHOLD*, **\-\-time\-threshold** *TIME_THRESHOLD*
        : Set exit code to 3 if test suite takes longer than threshold seconds.
        : Exit code is 0 otherwise.

    : **\-v**, **\-\-verbose**
        : Show stdout and stderr of commands executed.

**download** **\(d\)** *testsuites*
:   Downloads test suites resources.

    Arguments:
    : *testsuites* List of testsuites to download. Defaults to all.

    Options:
    : **\-j** *JOBS*, **\-\-jobs** *JOBS*
        : Number of parallel jobs to use. 2x logical cores by default. 0 means all logical cores.
    : **\-k**, **\-\-keep**
        : Keep original downloaded file after extracting. Only applicable to compressed files such as .zip, .tar.gz, etc

**reference** **\(r\)**
:   Use a specific decoder to set its results for the test suites given.

    Options:
    : **\-j** *JOBS*, **\-\-jobs** *JOBS*
        : Number of parallel jobs to use. 1x logical cores by default. 0 means all logical cores.

    : **\-t** *TIMEOUT*, **\-\-timeout** *TIMEOUT*
        : Timeout in secs for each decoding. Defaults to 30 secs.

    : **\-ff**, **\-\-failfast**
        : Stop after first fail.

    : **\-q**, **\-\-quiet**
        : Don't show every test run.

    : **\-ts** *TESTSUITES*, **\-\-testsuites** *TESTSUITES*
        : Run only the specific test suites.

    : **\-tv** *TESTVECTORS*, **\-\-testvectors** *TESTVECTORS*
        : Run only the specific test vectors.

    : **\-d** *DECODERS*, **\-\-decoders** *DECODERS*
        : Run only the specific decoders.

    : **\-s**, **\-\-summary**
        : Generate a summary in Markdown format for each test suite.

    : **\-so** *SUMMARY_OUTPUT*, **\-\-summary\-output** *SUMMARY_OUTPUT*
        : Dump summary output to file.

    : **\-f** *\{md,csv,junitxml\}*, **\-\-format** *\{md,csv,junitxml\}*
        : Specify the format for the summary file.

    : **\-k**, **\-\-keep**
        : Keep output files generated during the test.

    : **\-th** *THRESHOLD*, **\-\-threshold** *THRESHOLD*
        : Set exit code to 2 if threshold tests are not success. Exit code is 0 otherwise.

    : **\-tth** *TIME_THRESHOLD*, **\-\-time\-threshold** *TIME_THRESHOLD*
        : Set exit code to 3 if test suite takes longer than threshold seconds.
        : Exit code is 0 otherwise.

    : **\-v**, **\-\-verbose**
        : Show stdout and stderr of commands executed.

# AUTHORS

fluster is developed by Pablo Marcos Oltra, Andoni Morales Alastruey and
contributors.

This manual page was written by Christopher Obbard <obbardc@debian.org>
for the Debian GNU/Linux system (but may be used by others).
