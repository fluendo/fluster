# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.

project('fluster', 'c', 'cpp',
  version: '0.6.0',
  license: 'LGPL-3.0-or-later',
  meson_version: '>= 0.63.0',
  default_options: [
    'c_std=c99',
    'cpp_std=c++14',
  ],
)

python = import('python').find_installation('python3')
cmake = import('cmake')
fs = import('fs')
cc = meson.get_compiler('c')

# Directories
contrib_dir = meson.current_source_dir() / 'contrib'
decoders_dir = meson.current_source_dir() / 'decoders'
check_dir = meson.current_source_dir() / 'check'
tests_dir = meson.current_source_dir() / 'tests'
build_dir = meson.current_source_dir() / 'build'

# Platform detection
is_windows = host_machine.system() == 'windows'
is_linux = host_machine.system() == 'linux'
is_darwin = host_machine.system() == 'darwin'

# Set macOS deployment target to avoid linker warnings
if is_darwin
  add_project_arguments('-mmacosx-version-min=15.0', language: ['c', 'cpp'])
  add_project_link_arguments('-mmacosx-version-min=15.0', language: ['c', 'cpp'])
endif

# Check for required ISO reference software dependencies
# These must be downloaded first using build/download_deps.py
build_mpeg2_aac = get_option('mpeg2_aac_decoder')
build_mpeg4_aac = get_option('mpeg4_aac_decoder')
build_mpeg4_aac_er = get_option('mpeg4_aac_er_decoder')
build_mpeg2_video = get_option('mpeg2_video_decoder')

missing_deps = []

# Check MPEG-2 dependencies (needed for MPEG-2 AAC and MPEG-2 video)
if build_mpeg2_aac or build_mpeg2_video
  if not fs.is_dir(contrib_dir / 'mpeg2aac')
    missing_deps += ['contrib/mpeg2aac (MPEG-2 AAC decoder)']
  endif
  if not fs.is_dir(contrib_dir / 'video')
    missing_deps += ['contrib/video (MPEG-2 video decoder)']
  endif
endif

# Check MPEG-4 dependencies (needed for MPEG-4 AAC decoders)
if build_mpeg4_aac or build_mpeg4_aac_er
  if not fs.is_dir(contrib_dir / 'C050470e_Electronic_inserts')
    missing_deps += ['contrib/C050470e_Electronic_inserts (MPEG-4 AAC decoder)']
  endif
endif

# Check libtsp dependency (needed for all AAC decoders)
if build_mpeg2_aac or build_mpeg4_aac or build_mpeg4_aac_er
  if not fs.is_dir(contrib_dir / 'libtsp-v7r0')
    missing_deps += ['contrib/libtsp-v7r0 (audio library)']
  endif
endif

if missing_deps.length() > 0
  error_msg = '\n\nERROR: Required ISO reference software dependencies are missing:\n'
  foreach dep : missing_deps
    error_msg += '  - ' + dep + '\n'
  endforeach
  error_msg += '\nPlease run the download script first:\n'
  error_msg += '  python3 build/download_deps.py\n'
  error_msg += '\nThis will download all required ISO reference software.\n'
  error(error_msg)
endif

# Install Python dependencies
run_target('install-deps',
  command: [python, '-m', 'pip', 'install', '-r', meson.current_source_dir() / 'requirements-dev.txt'],
)

# Run Python unit tests
test('functional-tests',
  python,
  args: ['-m', 'unittest', 'discover', '-v', '-s', tests_dir, '-p', 'test_*.py'],
  workdir: meson.current_source_dir(),
  timeout: 300,
)

# Build options for reference decoders (disabled by default)
build_h264_decoder = get_option('h264_decoder')
build_h265_decoder = get_option('h265_decoder')
build_h266_decoder = get_option('h266_decoder')
build_h266_vvdec = get_option('h266_vvdec')

# Automatically enable isobmff if any AAC decoder is enabled
build_isobmff = build_mpeg2_aac or build_mpeg4_aac or build_mpeg4_aac_er

# H.264 Reference Decoder (JM)
jm_ldecod_tgt = disabler()
if build_h264_decoder
  jm_opts = cmake.subproject_options()
  cmake_c_flags = ''
  # GCC/Clang-specific warning flags (not supported by MSVC)
  if cc.get_id() != 'msvc'
    cmake_c_flags = '-Wno-stringop-truncation -Wno-stringop-overflow'
  endif
  if is_darwin
    cmake_c_flags += ' -mmacosx-version-min=15.0'
  endif
  jm_opts.add_cmake_defines({
    'CMAKE_BUILD_TYPE': 'Release',
    'CMAKE_C_FLAGS': cmake_c_flags,
  })
  jm_subproject = cmake.subproject('jm', options: jm_opts, required: false)
  if jm_subproject.found()
    jm_ldecod_tgt = jm_subproject.target('ldecod')
  else
    warning('H.264 reference decoder (JM) subproject not found')
  endif
endif

# H.265 Reference Decoder (HM)
hm_decoder_tgt = disabler()
if build_h265_decoder
  hm_subproject = subproject('hm', required: false)
  if hm_subproject.found()
    hm_decoder_tgt = hm_subproject.get_variable('TAppDecoder')
  else
    warning('H.265 reference decoder (HM) subproject not found')
  endif
endif

# H.266 Reference Decoder (VTM)
vtm_decoder_tgt = disabler()
if build_h266_decoder
  # Use native meson subproject (meson.build provided in packagefiles/vvcsoftware_vtm/)
  vtm_subproject = subproject('vvcsoftware_vtm', required: false)
  if vtm_subproject.found()
    vtm_decoder_tgt = vtm_subproject.get_variable('DecoderApp')
  else
    warning('H.266 reference decoder (VTM) subproject not found')
  endif
endif

# H.266 VVdeC Decoder
vvdec_decoder_tgt = disabler()
if build_h266_vvdec
  # Use native meson subproject (meson.build provided in packagefiles/vvdec/)
  vvdec_subproject = subproject('vvdec', required: false)
  if vvdec_subproject.found()
    vvdec_decoder_tgt = vvdec_subproject.get_variable('vvdecapp')
  else
    warning('H.266 VVdeC decoder subproject not found')
  endif
endif

# isobmff library (required for AAC decoders)
isobmff_lib = disabler()
if build_isobmff
  isobmff_opts = cmake.subproject_options()
  isobmff_cmake_defines = {'CMAKE_BUILD_TYPE': 'Release'}
  if is_darwin
    isobmff_cmake_defines += {
      'CMAKE_C_FLAGS': '-mmacosx-version-min=15.0',
      'CMAKE_CXX_FLAGS': '-mmacosx-version-min=15.0',
    }
  endif
  isobmff_opts.add_cmake_defines(isobmff_cmake_defines)
  isobmff_subproject = cmake.subproject('isobmff', options: isobmff_opts, required: false)
  if isobmff_subproject.found()
    isobmff_lib = isobmff_subproject.target('libisomediafile')
  else
    warning('isobmff subproject not found')
  endif
endif

# MPEG-2 Video Reference Decoder
mpeg2decode_tgt = disabler()
if build_mpeg2_video
  # Check if the mpeg2video subproject directory exists (symlinked from contrib/video)
  mpeg2video_dir = meson.current_source_dir() / 'subprojects' / 'mpeg2video'
  if fs.is_dir(mpeg2video_dir) or fs.is_symlink(mpeg2video_dir)
    mpeg2video_subproject = subproject('mpeg2video', required: false)
    if mpeg2video_subproject.found()
      mpeg2decode_tgt = mpeg2video_subproject.get_variable('mpeg2decode')
    else
      warning('MPEG-2 video decoder subproject configuration failed')
    endif
  else
    error('MPEG-2 video decoder: subprojects/mpeg2video symlink not found. Run: python3 build/download_deps.py')
  endif
endif

# libtsp library (required for AAC decoders)
libtsp_lib = disabler()
libtsp_inc = ''
if build_mpeg2_aac or build_mpeg4_aac or build_mpeg4_aac_er
  libtsp_subproject = subproject('libtsp', required: false)
  if libtsp_subproject.found()
    libtsp_lib = libtsp_subproject.get_variable('libtsp')
    # Get the library output path for use in shell scripts
    libtsp_lib_path = libtsp_lib.full_path()
    # Get include directory
    libtsp_inc = meson.current_source_dir() / 'subprojects' / 'libtsp-v7r0' / 'include'
  else
    warning('libtsp subproject not found')
  endif
endif

# MPEG-2 AAC Reference Decoder
aacdec_mc_tgt = disabler()
if build_mpeg2_aac
  # Check if the mpeg2aac subproject directory exists (symlinked from contrib/mpeg2aac)
  mpeg2aac_dir = meson.current_source_dir() / 'subprojects' / 'mpeg2aac'
  if fs.is_dir(mpeg2aac_dir) or fs.is_symlink(mpeg2aac_dir)
    mpeg2aac_subproject = subproject('mpeg2aac', required: false)
    if mpeg2aac_subproject.found()
      aacdec_mc_tgt = mpeg2aac_subproject.get_variable('aacdec_mc')
    else
      warning('MPEG-2 AAC decoder subproject configuration failed')
    endif
  else
    error('MPEG-2 AAC decoder: subprojects/mpeg2aac symlink not found. Run: python3 build/download_deps.py')
  endif
endif

# Extract compiler flags from meson's C compiler configuration
# This ensures ISO decoders use the same architecture as the main build
c_args_list = get_option('c_args')
c_link_args_list = get_option('c_link_args')

# Add macOS compat headers for ISO decoders
if host_machine.system() == 'darwin'
  c_args_list += ['-I' + build_dir / 'compat' / 'macos']
endif

# Join the args into space-separated strings for the shell script
iso_cflags = ' '.join(c_args_list)
iso_ldflags = ' '.join(c_link_args_list)

# Build list of MPEG-4 AAC decoders to build via shell script
# (MPEG-2 video and MPEG-2 AAC are now meson subprojects)
iso_decoders_list = []
if build_mpeg4_aac
  iso_decoders_list += ['mpeg4-aac']
endif
if build_mpeg4_aac_er
  iso_decoders_list += ['mpeg4-aac-er']
endif

iso_decoders_arg = ' '.join(iso_decoders_list)

# ISO reference decoders build target (builds by default)
# Only build MPEG-4 AAC decoders via shell script (MPEG-2 AAC is now a meson subproject)
if iso_decoders_list.length() > 0
  # Add libtsp and isobmff libraries as dependencies if AAC decoders are enabled
  iso_build_deps = []
  if build_mpeg2_aac or build_mpeg4_aac or build_mpeg4_aac_er
    iso_build_deps += [libtsp_lib, isobmff_lib]
  endif

  iso_decoders_target = custom_target('iso-reference-decoders',
    output: 'iso-decoders.stamp',
    input: iso_build_deps,
    command: [
      python,
      build_dir / 'build_iso_decoders.py',
      meson.current_build_dir(),
      iso_cflags,
      iso_ldflags,
      iso_decoders_arg,
      '&&',
      'touch',
      '@OUTPUT@',
    ],
    build_by_default: true,
    console: true,
  )
endif

# =============================================================================
# Create symlinks for decoders in decoders/ directory to be usable by fluster
# =============================================================================

# Helper script to create symlink with absolute path
# Note: @INPUT@ is relative to build dir, so we construct absolute path
link_script = '''
#!/bin/sh
builddir="$1"
src="$2"
dst="$3"
mkdir -p "$(dirname "$dst")"
rm -f "$dst"
ln -sf "$builddir/$src" "$dst"
'''

# H.264 decoder symlink (ldecod)
if not is_disabler(jm_ldecod_tgt)
  custom_target('link-ldecod',
    output: 'ldecod.link',
    input: jm_ldecod_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'ldecod'],
    build_by_default: true,
  )
endif

# H.265 decoder symlink (TAppDecoder)
if not is_disabler(hm_decoder_tgt)
  custom_target('link-TAppDecoder',
    output: 'TAppDecoder.link',
    input: hm_decoder_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'TAppDecoder'],
    build_by_default: true,
  )
endif

# H.266 VTM decoder symlink (DecoderApp)
if not is_disabler(vtm_decoder_tgt)
  custom_target('link-DecoderApp',
    output: 'DecoderApp.link',
    input: vtm_decoder_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'DecoderApp'],
    build_by_default: true,
  )
endif

# H.266 VVdeC decoder symlink (vvdecapp)
if not is_disabler(vvdec_decoder_tgt)
  custom_target('link-vvdecapp',
    output: 'vvdecapp.link',
    input: vvdec_decoder_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'vvdecapp'],
    build_by_default: true,
  )
endif

# MPEG-2 video decoder symlink (mpeg2decode)
if not is_disabler(mpeg2decode_tgt)
  custom_target('link-mpeg2decode',
    output: 'mpeg2decode.link',
    input: mpeg2decode_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'mpeg2decode'],
    build_by_default: true,
  )
endif

# MPEG-2 AAC decoder symlink (aacdec_mc)
if not is_disabler(aacdec_mc_tgt)
  custom_target('link-aacdec_mc',
    output: 'aacdec_mc.link',
    input: aacdec_mc_tgt,
    command: ['sh', '-c', link_script, '_', meson.current_build_dir(), '@INPUT@', decoders_dir / 'aacdec_mc'],
    build_by_default: true,
  )
endif

run_target('clean-contrib',
  command: ['rm', '-rf', contrib_dir],
)

# Summary
summary({
  'Python': python.full_path(),
  'C Compiler': cc.get_id(),
  'Platform': host_machine.system(),
}, section: 'Build Environment')

summary({
  'Check directory': check_dir,
  'Tests directory': tests_dir,
  'Contrib directory': contrib_dir,
  'Decoders directory': decoders_dir,
}, section: 'Directories')

summary({
  'H.264 decoder (JM)': build_h264_decoder,
  'H.265 decoder (HM)': build_h265_decoder,
  'H.266 decoder (VTM)': build_h266_decoder,
  'H.266 decoder (VVdeC)': build_h266_vvdec,
  'MPEG-2 video decoder': build_mpeg2_video,
  'MPEG-2 AAC decoder': build_mpeg2_aac,
  'isobmff library': build_isobmff,
}, section: 'Meson Subproject Decoders')

summary({
  'MPEG-4 AAC': build_mpeg4_aac,
  'MPEG-4 AAC-ER': build_mpeg4_aac_er,
  'CFLAGS': iso_cflags != '' ? iso_cflags : 'default',
  'LDFLAGS': iso_ldflags != '' ? iso_ldflags : 'default',
}, section: 'ISO Reference Decoders (MPEG-4 AAC only)')
