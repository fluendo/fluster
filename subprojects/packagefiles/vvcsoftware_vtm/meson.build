# Native meson.build for VTM (VVC Test Model)
# This replaces the CMake build system to fix linking issues
project('VTM', 'cpp',
  version: '23.4',
  default_options: [
    'cpp_std=c++17',
    'default_library=static',
    'buildtype=release'
  ]
)

cpp = meson.get_compiler('cpp')

# Common compiler arguments
# JVET_AJ0151_DSC_SEI=0 disables OpenSSL dependency for digital signature verification
vtm_cpp_args = ['-DNDEBUG', '-DJVET_AJ0151_DSC_SEI=0']

if cpp.get_id() == 'gcc' or cpp.get_id() == 'clang'
  vtm_cpp_args += ['-Wall', '-Wno-sign-compare', '-Wno-unused-variable']
endif

# Check if we're on x86 architecture for SIMD support
host_cpu = host_machine.cpu_family()
is_x86 = host_cpu == 'x86' or host_cpu == 'x86_64'

# CommonLib sources (discovered from source tree)
commonlib_base_sources = [
  'source/Lib/CommonLib/AdaptiveLoopFilter.cpp',
  'source/Lib/CommonLib/AffineGradientSearch.cpp',
  'source/Lib/CommonLib/BitStream.cpp',
  'source/Lib/CommonLib/Buffer.cpp',
  'source/Lib/CommonLib/CacheModel.cpp',
  'source/Lib/CommonLib/ChromaFormat.cpp',
  'source/Lib/CommonLib/CodingStructure.cpp',
  'source/Lib/CommonLib/ConstraintInfo.cpp',
  'source/Lib/CommonLib/ContextModelling.cpp',
  'source/Lib/CommonLib/Contexts.cpp',
  'source/Lib/CommonLib/DeblockingFilter.cpp',
  'source/Lib/CommonLib/DepQuant.cpp',
  'source/Lib/CommonLib/dtrace.cpp',
  'source/Lib/CommonLib/dtrace_blockstatistics.cpp',
  'source/Lib/CommonLib/Hash.cpp',
  'source/Lib/CommonLib/HRD.cpp',
  'source/Lib/CommonLib/IbcHashMap.cpp',
  'source/Lib/CommonLib/InterpolationFilter.cpp',
  'source/Lib/CommonLib/InterPrediction.cpp',
  'source/Lib/CommonLib/IntraPrediction.cpp',
  'source/Lib/CommonLib/MatrixIntraPrediction.cpp',
  'source/Lib/CommonLib/MCTS.cpp',
  'source/Lib/CommonLib/Mv.cpp',
  'source/Lib/CommonLib/ParameterSetManager.cpp',
  'source/Lib/CommonLib/Picture.cpp',
  'source/Lib/CommonLib/PictureParameterSet.cpp',
  'source/Lib/CommonLib/PicYuvMD5.cpp',
  'source/Lib/CommonLib/ProfileTierLevel.cpp',
  'source/Lib/CommonLib/Quant.cpp',
  'source/Lib/CommonLib/QuantRDOQ.cpp',
  'source/Lib/CommonLib/RdCost.cpp',
  'source/Lib/CommonLib/RdCostWeightPrediction.cpp',
  'source/Lib/CommonLib/Reshape.cpp',
  'source/Lib/CommonLib/Rom.cpp',
  'source/Lib/CommonLib/RomLFNST.cpp',
  'source/Lib/CommonLib/RomTr.cpp',
  'source/Lib/CommonLib/SampleAdaptiveOffset.cpp',
  'source/Lib/CommonLib/SEI.cpp',
  'source/Lib/CommonLib/SEIColourTransform.cpp',
  'source/Lib/CommonLib/SEIDigitallySignedContent.cpp',
  'source/Lib/CommonLib/SEIFilmGrainSynthesizer.cpp',
  'source/Lib/CommonLib/SEINeuralNetworkPostFiltering.cpp',
  'source/Lib/CommonLib/SEIPackedRegionsInfoProcess.cpp',
  'source/Lib/CommonLib/SequenceParameterSet.cpp',
  'source/Lib/CommonLib/Slice.cpp',
  'source/Lib/CommonLib/TrQuant.cpp',
  'source/Lib/CommonLib/TrQuant_EMT.cpp',
  'source/Lib/CommonLib/Unit.cpp',
  'source/Lib/CommonLib/UnitPartitioner.cpp',
  'source/Lib/CommonLib/UnitTools.cpp',
  'source/Lib/CommonLib/VideoParameterSet.cpp',
  'source/Lib/CommonLib/WeightPrediction.cpp',
]

# x86 base sources (always included on x86)
commonlib_x86_base_sources = [
  'source/Lib/CommonLib/x86/CommonDefX86.cpp',
  'source/Lib/CommonLib/x86/InitX86.cpp',
]

# libmd5 sources
libmd5_sources = [
  'source/Lib/libmd5/libmd5.cpp',
]

# DecoderLib sources
decoderlib_sources = [
  'source/Lib/DecoderLib/AnnexBread.cpp',
  'source/Lib/DecoderLib/BinDecoder.cpp',
  'source/Lib/DecoderLib/CABACReader.cpp',
  'source/Lib/DecoderLib/DecCu.cpp',
  'source/Lib/DecoderLib/DecLib.cpp',
  'source/Lib/DecoderLib/DecSlice.cpp',
  'source/Lib/DecoderLib/NALread.cpp',
  'source/Lib/DecoderLib/SEIread.cpp',
  'source/Lib/DecoderLib/VLCReader.cpp',
]

# Utilities sources
utilities_sources = [
  'source/Lib/Utilities/program_options_lite.cpp',
  'source/Lib/Utilities/VideoIOYuv.cpp',
]

# DecoderApp sources
decoderapp_sources = [
  'source/App/DecoderApp/DecApp.cpp',
  'source/App/DecoderApp/DecAppCfg.cpp',
  'source/App/DecoderApp/decmain.cpp',
]

# Include directories
vtm_includes = include_directories(
  'source/Lib',
  'source/Lib/CommonLib',
  'source/Lib/CommonLib/x86',
  'source/Lib/DecoderLib',
  'source/Lib/Utilities',
  'source/Lib/libmd5',
)

# x86 SIMD sources (only on x86 architectures)
# Each SIMD level needs specific compiler flags and defines
if is_x86
  # SSE4.1 sources
  commonlib_sse41_sources = [
    'source/Lib/CommonLib/x86/sse41/AdaptiveLoopFilter_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/AffineGradientSearch_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/Buffer_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/InterpolationFilter_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/RdCost_sse41.cpp',
    'source/Lib/CommonLib/x86/sse41/TrQuantX86_sse41.cpp',
  ]
  
  # SSE4.2 sources
  commonlib_sse42_sources = [
    'source/Lib/CommonLib/x86/sse42/IbcHashmap_sse42.cpp',
  ]
  
  # AVX sources
  commonlib_avx_sources = [
    'source/Lib/CommonLib/x86/avx/AdaptiveLoopFilter_avx.cpp',
    'source/Lib/CommonLib/x86/avx/AffineGradientSearch_avx.cpp',
    'source/Lib/CommonLib/x86/avx/Buffer_avx.cpp',
    'source/Lib/CommonLib/x86/avx/InterpolationFilter_avx.cpp',
    'source/Lib/CommonLib/x86/avx/RdCost_avx.cpp',
    'source/Lib/CommonLib/x86/avx/TrQuantX86_avx.cpp',
  ]
  
  # AVX2 sources
  commonlib_avx2_sources = [
    'source/Lib/CommonLib/x86/avx2/AdaptiveLoopFilter_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/AffineGradientSearch_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/Buffer_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/InterpolationFilter_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/RdCost_avx2.cpp',
    'source/Lib/CommonLib/x86/avx2/TrQuantX86_avx2.cpp',
  ]
  
  # Compiler-specific SIMD flags
  if cpp.get_id() == 'msvc'
    sse41_args = vtm_cpp_args + ['-DUSE_SSE41']
    sse42_args = vtm_cpp_args + ['-DUSE_SSE42']
    avx_args = vtm_cpp_args + ['-DUSE_AVX', '/arch:AVX']
    avx2_args = vtm_cpp_args + ['-DUSE_AVX2', '/arch:AVX2']
  else
    sse41_args = vtm_cpp_args + ['-DUSE_SSE41', '-msse4.1']
    sse42_args = vtm_cpp_args + ['-DUSE_SSE42', '-msse4.2']
    avx_args = vtm_cpp_args + ['-DUSE_AVX', '-mavx']
    avx2_args = vtm_cpp_args + ['-DUSE_AVX2', '-mavx2']
  endif
  
  # Build SIMD object libraries
  CommonLib_sse41 = static_library('CommonLib_sse41',
    commonlib_sse41_sources,
    include_directories: vtm_includes,
    cpp_args: sse41_args,
  )
  
  CommonLib_sse42 = static_library('CommonLib_sse42',
    commonlib_sse42_sources,
    include_directories: vtm_includes,
    cpp_args: sse42_args,
  )
  
  CommonLib_avx = static_library('CommonLib_avx',
    commonlib_avx_sources,
    include_directories: vtm_includes,
    cpp_args: avx_args,
  )
  
  CommonLib_avx2 = static_library('CommonLib_avx2',
    commonlib_avx2_sources,
    include_directories: vtm_includes,
    cpp_args: avx2_args,
  )
  
  commonlib_sources = commonlib_base_sources + commonlib_x86_base_sources + libmd5_sources
  simd_libs = [CommonLib_sse41, CommonLib_sse42, CommonLib_avx, CommonLib_avx2]
else
  commonlib_sources = commonlib_base_sources + libmd5_sources
  simd_libs = []
endif

# Build CommonLib
CommonLib = static_library('CommonLib',
  commonlib_sources,
  include_directories: vtm_includes,
  cpp_args: vtm_cpp_args,
)

# Build DecoderLib
DecoderLib = static_library('DecoderLib',
  decoderlib_sources,
  include_directories: vtm_includes,
  cpp_args: vtm_cpp_args,
)

# Build Utilities
Utilities = static_library('Utilities',
  utilities_sources,
  include_directories: vtm_includes,
  cpp_args: vtm_cpp_args,
)

# Build DecoderApp executable
DecoderApp = executable('DecoderApp',
  decoderapp_sources,
  include_directories: vtm_includes,
  link_with: [CommonLib, DecoderLib, Utilities] + simd_libs,
  cpp_args: vtm_cpp_args,
  install: false,
)
