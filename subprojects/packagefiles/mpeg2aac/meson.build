# Native meson.build for MPEG-2 AAC Decoder (aacdec_mc)
# ISO/IEC 13818-7 Reference Software
# This replaces the original Makefile to integrate with the meson build system

project('mpeg2aac', 'c',
  version: '2.0',
  default_options: [
    'c_std=c99',
    'default_library=static',
    'buildtype=release',
    'warning_level=0',
  ]
)

cc = meson.get_compiler('c')
fs = import('fs')

# Get libtsp dependency (required for audio output)
libtsp_dep = dependency('libtsp', required: true)

# Common AAC decoder source files
mpeg2aac_common_sources = [
  'aacDec/src/bitinput.c',
  'aacDec/src/config.c',
  'aacDec/src/coupling.c',
  'aacDec/src/diagnose.c',
  'aacDec/src/drc.c',
  'aacDec/src/huffdec1.c',
  'aacDec/src/huffdec2.c',
  'aacDec/src/huffdec3.c',
  'aacDec/src/huffinit.c',
  'aacDec/src/hufftables.c',
  'aacDec/src/intensity.c',
  'aacDec/src/intrins.c',
  'aacDec/src/monopred.c',
  'aacDec/src/stereo.c',
  'aacDec/src/tns.c',
  # DOLBY imdct
  'aacDec/src/adifdec.c',
  'aacDec/src/block.c',
  'aacDec/src/dolby_adapt.c',
  'aacDec/src/transfo.c',
  # SONY gain control
  'aacDec/src/gc_unpac.c',
  'aacDec/src/gc_compensate.c',
  'aacDec/src/gc_common.c',
  'aacDec/src/gc_pqf_common.c',
  'aacDec/src/gc_ipqf.c',
  'aacDec/src/gc.c',
  'aacDec/src/gc_mdct_common.c',
  'aacDec/src/gc_imdct.c',
  # Coding Technologies SBR (Spectral Band Replication)
  'aacDec/src/ct_envcalc.c',
  'aacDec/src/ct_envdec.c',
  'aacDec/src/ct_envextr.c',
  'aacDec/src/ct_freqsca.c',
  'aacDec/src/ct_hfgen.c',
  'aacDec/src/ct_sbrbitb.c',
  'aacDec/src/ct_sbrcrc.c',
  'aacDec/src/ct_sbrdec.c',
  'aacDec/src/ct_sbrdecoder.c',
  'aacDec/src/ct_polyphase.c',
  # Parametric Stereo
  'aacDec/src/ct_psdec.c',
]

# Decoder main sources
mpeg2aac_decoder_sources = [
  'aacDec/src/decoder.c',
  'aacDec/src/audioout.c',
  'aacDec/src/aiff_support.c',
]

# Compiler definitions
mpeg2aac_c_args = [
  '-DNEW_ADTS',
  '-DWRITE_NEW_ADTS',
  '-DDRC',
  '-DBIGDECODER',  # Support up to 48 channels
  '-DCT_SBR',      # Enable SBR
  '-DPARAMETRICSTEREO',  # Enable Parametric Stereo
]

# Platform-specific compatibility
if host_machine.system() == 'darwin'
  # macOS needs compat headers for malloc.h
  # Use local compat directory within the subproject
  compat_include = include_directories('compat')
else
  compat_include = []
endif

# Include directories
mpeg2aac_inc = include_directories('aacDec/src')

# Build the AAC library
libisoaac = static_library('isoaac',
  mpeg2aac_common_sources,
  c_args: mpeg2aac_c_args,
  include_directories: [mpeg2aac_inc, compat_include],
  dependencies: [libtsp_dep],
  install: false,
)

# Build the decoder executable
aacdec_mc = executable('aacdec_mc',
  mpeg2aac_decoder_sources,
  c_args: mpeg2aac_c_args,
  include_directories: [mpeg2aac_inc, compat_include],
  link_with: [libisoaac],
  dependencies: [libtsp_dep],
  install: false,
)

# Declare dependency for other subprojects
mpeg2aac_dep = declare_dependency(
  link_with: [libisoaac],
  include_directories: [mpeg2aac_inc],
)

# Override the dependency so other subprojects can use it
meson.override_dependency('mpeg2aac', mpeg2aac_dep)
