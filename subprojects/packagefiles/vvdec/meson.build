# Native meson.build for vvdec (VVC Decoder)
# This replaces the CMake build system to fix linking issues
project('vvdec', 'cpp',
  version: '3.2.0',
  default_options: [
    'cpp_std=c++14',
    'default_library=static',
    'buildtype=release'
  ]
)

cpp = meson.get_compiler('cpp')
threads_dep = dependency('threads')

# Common compiler arguments
vvdec_cpp_args = ['-DNDEBUG', '-DVVDEC_SOURCE']

if cpp.get_id() == 'gcc' or cpp.get_id() == 'clang'
  vvdec_cpp_args += ['-Wall', '-Wno-sign-compare', '-Wno-unused-variable', '-fvisibility=hidden']
  if cpp.get_id() == 'clang'
    vvdec_cpp_args += ['-fno-lax-vector-conversions']
  endif
endif

# Check host architecture
host_cpu = host_machine.cpu_family()
is_x86 = host_cpu == 'x86' or host_cpu == 'x86_64'
is_arm = host_cpu == 'aarch64' or host_cpu == 'arm'

# Generate version.h and vvdec.h headers
# The code includes "vvdec/version.h" so we need to place headers in a vvdec/ subdir
# Meson doesn't allow subdirectories in configure_file or custom_target output,
# so we use a generator script that creates the directory structure

python = find_program('python3', 'python')

# Generator script to create headers in vvdec/ subdirectory
gen_headers = custom_target('gen_vvdec_headers',
  input: ['source/Lib/vvdec/version.h.in', 'include/vvdec/vvdec.h.in'],
  output: ['vvdec_headers_done'],
  command: [python, '-c', '''
import os
import sys

build_dir = os.path.dirname(sys.argv[3])
vvdec_dir = os.path.join(build_dir, "vvdec")
os.makedirs(vvdec_dir, exist_ok=True)

# Generate version.h
with open(sys.argv[1]) as f:
    content = f.read()
content = content.replace("${PROJECT_VERSION_MAJOR}", "3")
content = content.replace("${PROJECT_VERSION_MINOR}", "2")
content = content.replace("${PROJECT_VERSION_PATCH}", "0")
with open(os.path.join(vvdec_dir, "version.h"), "w") as f:
    f.write(content)

# Generate vvdec.h
with open(sys.argv[2]) as f:
    content = f.read()
content = content.replace("@VVDEC_USE_UNSTABLE_API@", "0")
with open(os.path.join(vvdec_dir, "vvdec.h"), "w") as f:
    f.write(content)

# Touch the marker file
with open(sys.argv[3], "w") as f:
    f.write("done")
''', '@INPUT0@', '@INPUT1@', '@OUTPUT@'],
)

# Include directory for generated headers (builddir/subprojects/vvdec/)
# This allows #include "vvdec/version.h" to work
gen_inc = include_directories('.')

# Include directories
vvdec_includes = include_directories(
  'include',
  'source/Lib',
  'source/Lib/CommonLib',
  'source/Lib/CommonLib/x86',
  'source/Lib/CommonLib/arm',
  'source/Lib/DecoderLib',
  'source/Lib/Utilities',
  'source/Lib/libmd5',
  'source/Lib/vvdec',
  'source/Lib/FilmGrain',
  'thirdparty',
)

# CommonLib base sources
commonlib_sources = [
  'source/Lib/CommonLib/AdaptiveLoopFilter.cpp',
  'source/Lib/CommonLib/BitStream.cpp',
  'source/Lib/CommonLib/Buffer.cpp',
  'source/Lib/CommonLib/ChromaFormat.cpp',
  'source/Lib/CommonLib/CodingStructure.cpp',
  'source/Lib/CommonLib/ContextModelling.cpp',
  'source/Lib/CommonLib/Contexts.cpp',
  'source/Lib/CommonLib/dtrace.cpp',
  'source/Lib/CommonLib/InterpolationFilter.cpp',
  'source/Lib/CommonLib/InterPrediction.cpp',
  'source/Lib/CommonLib/IntraPrediction.cpp',
  'source/Lib/CommonLib/LoopFilter.cpp',
  'source/Lib/CommonLib/MatrixIntraPrediction.cpp',
  'source/Lib/CommonLib/Mv.cpp',
  'source/Lib/CommonLib/ParameterSetManager.cpp',
  'source/Lib/CommonLib/PicListManager.cpp',
  'source/Lib/CommonLib/Picture.cpp',
  'source/Lib/CommonLib/PicYuvMD5.cpp',
  'source/Lib/CommonLib/Quant.cpp',
  'source/Lib/CommonLib/RdCost.cpp',
  'source/Lib/CommonLib/Reshape.cpp',
  'source/Lib/CommonLib/Rom.cpp',
  'source/Lib/CommonLib/RomLFNST.cpp',
  'source/Lib/CommonLib/RomTr.cpp',
  'source/Lib/CommonLib/SampleAdaptiveOffset.cpp',
  'source/Lib/CommonLib/SEI_internal.cpp',
  'source/Lib/CommonLib/Slice.cpp',
  'source/Lib/CommonLib/StatCounter.cpp',
  'source/Lib/CommonLib/TrQuant.cpp',
  'source/Lib/CommonLib/TrQuant_EMT.cpp',
  'source/Lib/CommonLib/Unit.cpp',
  'source/Lib/CommonLib/UnitPartitioner.cpp',
  'source/Lib/CommonLib/UnitTools.cpp',
  'source/Lib/CommonLib/WeightPrediction.cpp',
]

# DecoderLib sources
decoderlib_sources = [
  'source/Lib/DecoderLib/AnnexBread.cpp',
  'source/Lib/DecoderLib/BinDecoder.cpp',
  'source/Lib/DecoderLib/CABACReader.cpp',
  'source/Lib/DecoderLib/DecCu.cpp',
  'source/Lib/DecoderLib/DecLib.cpp',
  'source/Lib/DecoderLib/DecLibParser.cpp',
  'source/Lib/DecoderLib/DecLibRecon.cpp',
  'source/Lib/DecoderLib/DecSlice.cpp',
  'source/Lib/DecoderLib/HLSyntaxReader.cpp',
  'source/Lib/DecoderLib/NALread.cpp',
  'source/Lib/DecoderLib/SEIread.cpp',
  'source/Lib/DecoderLib/VLCReader.cpp',
]

# Utilities sources
utilities_sources = [
  'source/Lib/Utilities/ThreadPool.cpp',
]

# vvdec API sources
vvdec_api_sources = [
  'source/Lib/vvdec/vvdec.cpp',
  'source/Lib/vvdec/vvdecimpl.cpp',
]

# FilmGrain base sources
filmgrain_sources = [
  'source/Lib/FilmGrain/FilmGrain.cpp',
  'source/Lib/FilmGrain/FilmGrainImpl.cpp',
]

# All base sources
all_sources = commonlib_sources + decoderlib_sources + utilities_sources + vvdec_api_sources + filmgrain_sources

# ARM SIMD sources
if is_arm
  arm_sources = [
    'source/Lib/CommonLib/arm/CommonDefARM.cpp',
    'source/Lib/CommonLib/arm/InitARM.cpp',
    'source/Lib/CommonLib/arm/neon/AdaptiveLoopFilter_neon.cpp',
    'source/Lib/CommonLib/arm/neon/Buffer_neon.cpp',
    'source/Lib/CommonLib/arm/neon/InterpolationFilter_neon.cpp',
    'source/Lib/CommonLib/arm/neon/RdCost_neon.cpp',
  ]
  all_sources += arm_sources
endif

# x86 SIMD sources (via SIMDE on ARM)
if is_x86 or is_arm
  x86_sources = [
    'source/Lib/CommonLib/x86/InitX86.cpp',
  ]

  x86_sse41_sources = [
    'source/Lib/CommonLib/x86/sse41/AdaptiveLoopFilter_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/Buffer_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/InterpolationFilter_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/InterPred_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/IntraPred_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/LoopFilter_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/Picture_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/Quant_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/RdCost_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/SampleAdaptiveOffset_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/Trafo_sse41.cpp',
    'source/Lib/FilmGrain/FilmGrainImpl_sse41.cpp',
  ]

  x86_avx2_sources = [
    'source/Lib/CommonLib/x86/avx2/AdaptiveLoopFilter_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/Buffer_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/InterpolationFilter_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/InterPred_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/IntraPred_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/LoopFilter_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/Picture_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/Quant_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/RdCost_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/SampleAdaptiveOffset_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/Trafo_avx2.cpp',
    'source/Lib/FilmGrain/FilmGrainImpl_avx2.cpp',
  ]

  all_sources += x86_sources

  # SSE4.1 sources with USE_SSE41 define
  sse41_lib = static_library('vvdec_sse41',
    x86_sse41_sources, gen_headers,
    include_directories: [vvdec_includes, gen_inc],
    cpp_args: vvdec_cpp_args + ['-DUSE_SSE41'],
    dependencies: threads_dep,
  )

  # AVX2 sources with USE_AVX2 define
  avx2_lib = static_library('vvdec_avx2',
    x86_avx2_sources, gen_headers,
    include_directories: [vvdec_includes, gen_inc],
    cpp_args: vvdec_cpp_args + ['-DUSE_AVX2'],
    dependencies: threads_dep,
  )
endif

# Build vvdec library
vvdec_lib = static_library('vvdec',
  all_sources, gen_headers,
  include_directories: [vvdec_includes, gen_inc],
  cpp_args: vvdec_cpp_args,
  dependencies: threads_dep,
)

# Link all libraries together
if is_x86 or is_arm
  vvdec_link = [vvdec_lib, sse41_lib, avx2_lib]
else
  vvdec_link = [vvdec_lib]
endif

# DecoderApp sources
vvdecapp_sources = [
  'source/App/vvdecapp/vvdecapp.cpp',
]

# Build vvdecapp executable
vvdecapp = executable('vvdecapp',
  vvdecapp_sources, gen_headers,
  include_directories: [vvdec_includes, gen_inc, include_directories('source/Lib/libmd5')],
  link_with: vvdec_link,
  cpp_args: vvdec_cpp_args,
  dependencies: threads_dep,
  install: false,
)
