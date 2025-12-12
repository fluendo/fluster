# Native meson.build for MPEG-2 Video Decoder (mpeg2decode)
# ISO/IEC 13818-5 Reference Software
# This replaces the original Makefile to integrate with the meson build system
#
# This file should be copied to contrib/video/ before running meson

project('mpeg2video', 'c',
  version: '1.2',
  default_options: [
    'c_std=c99',
    'default_library=static',
    'buildtype=release',
    'warning_level=0',
  ]
)

cc = meson.get_compiler('c')

# Source files for mpeg2decode
mpeg2decode_sources = [
  'decoder/mpeg2dec.c',
  'decoder/getpic.c',
  'decoder/motion.c',
  'decoder/getvlc.c',
  'decoder/gethdr.c',
  'decoder/getblk.c',
  'decoder/getbits.c',
  'decoder/store.c',
  'decoder/recon.c',
  'decoder/spatscal.c',
  'decoder/idct.c',
  'decoder/idctref.c',
  'decoder/display.c',
  'decoder/systems.c',
  'decoder/subspic.c',
  'decoder/verify.c',
]

# Compiler arguments
mpeg2_c_args = [
  '-DTRACE',
  '-DVERBOSE',
  '-DVERIFY',
  # Disable X11 display - not needed for conformance testing
  # '-DDISPLAY',
]

# Suppress warnings for legacy code
if cc.get_id() == 'gcc' or cc.get_id() == 'clang'
  mpeg2_c_args += [
    '-Wno-implicit-function-declaration',
    '-Wno-implicit-int',
    '-Wno-int-conversion',
    '-Wno-incompatible-pointer-types',
  ]
endif

# Math library
m_dep = cc.find_library('m', required: false)

# Build mpeg2decode executable
mpeg2decode = executable('mpeg2decode',
  mpeg2decode_sources,
  c_args: mpeg2_c_args,
  dependencies: [m_dep],
  install: false,
)
