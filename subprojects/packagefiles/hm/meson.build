# Native meson.build for HM (HEVC Test Model) H.265 reference decoder
# This replaces the auto-generated CMake conversion which has broken link_args

project('HM', 'cpp',
  version: '18.0',
  default_options: ['cpp_std=gnu++11', 'warning_level=0']
)

# Common include directories
common_inc = include_directories(
  'source/Lib/TLibCommon',
  'source/Lib/TLibDecoder',
  'source/Lib/TLibEncoder',
  'source/Lib/Utilities',
  'source/Lib/libmd5',
  'source/Lib',
  '.'
)

# Common compiler args
# JVET_AK0194_DSC_SEI=0 disables OpenSSL dependency for digital signature verification
common_cpp_args = [
  '-DJVET_AK0194_DSC_SEI=0',
  '-Wno-unknown-attributes',
  '-Wno-deprecated-register',
  '-Wno-pessimizing-move',
  '-Wno-absolute-value',
  '-Wno-unused-const-variable',
]

# TLibCommon static library
TLibCommon_src = files(
  'source/Lib/TLibCommon/ContextModel.cpp',
  'source/Lib/TLibCommon/ContextModel3DBuffer.cpp',
  'source/Lib/TLibCommon/Debug.cpp',
  'source/Lib/TLibCommon/ProfileLevelTierFeatures.cpp',
  'source/Lib/TLibCommon/SEI.cpp',
  'source/Lib/TLibCommon/SEIDigitallySignedContent.cpp',
  'source/Lib/TLibCommon/SEIFilmGrainAnalyzer.cpp',
  'source/Lib/TLibCommon/SEIFilmGrainSynthesizer.cpp',
  'source/Lib/TLibCommon/TComBitStream.cpp',
  'source/Lib/TLibCommon/TComCABACTables.cpp',
  'source/Lib/TLibCommon/TComChromaFormat.cpp',
  'source/Lib/TLibCommon/TComDataCU.cpp',
  'source/Lib/TLibCommon/TComInterpolationFilter.cpp',
  'source/Lib/TLibCommon/TComLoopFilter.cpp',
  'source/Lib/TLibCommon/TComMotionInfo.cpp',
  'source/Lib/TLibCommon/TComPattern.cpp',
  'source/Lib/TLibCommon/TComPic.cpp',
  'source/Lib/TLibCommon/TComPicSym.cpp',
  'source/Lib/TLibCommon/TComPicYuv.cpp',
  'source/Lib/TLibCommon/TComPicYuvMD5.cpp',
  'source/Lib/TLibCommon/TComPrediction.cpp',
  'source/Lib/TLibCommon/TComRdCost.cpp',
  'source/Lib/TLibCommon/TComRdCostWeightPrediction.cpp',
  'source/Lib/TLibCommon/TComRom.cpp',
  'source/Lib/TLibCommon/TComSampleAdaptiveOffset.cpp',
  'source/Lib/TLibCommon/TComSlice.cpp',
  'source/Lib/TLibCommon/TComTU.cpp',
  'source/Lib/TLibCommon/TComTrQuant.cpp',
  'source/Lib/TLibCommon/TComWeightPrediction.cpp',
  'source/Lib/TLibCommon/TComYuv.cpp',
  'source/Lib/libmd5/libmd5.cpp',
)

TLibCommon = static_library('TLibCommon',
  TLibCommon_src,
  include_directories: common_inc,
  cpp_args: common_cpp_args,
)

# TLibDecoder static library
TLibDecoder_src = files(
  'source/Lib/TLibDecoder/AnnexBread.cpp',
  'source/Lib/TLibDecoder/NALread.cpp',
  'source/Lib/TLibDecoder/SEIread.cpp',
  'source/Lib/TLibDecoder/SyntaxElementParser.cpp',
  'source/Lib/TLibDecoder/TDecBinCoderCABAC.cpp',
  'source/Lib/TLibDecoder/TDecCAVLC.cpp',
  'source/Lib/TLibDecoder/TDecConformance.cpp',
  'source/Lib/TLibDecoder/TDecCu.cpp',
  'source/Lib/TLibDecoder/TDecEntropy.cpp',
  'source/Lib/TLibDecoder/TDecGop.cpp',
  'source/Lib/TLibDecoder/TDecSbac.cpp',
  'source/Lib/TLibDecoder/TDecSlice.cpp',
  'source/Lib/TLibDecoder/TDecTop.cpp',
)

TLibDecoder = static_library('TLibDecoder',
  TLibDecoder_src,
  include_directories: common_inc,
  cpp_args: common_cpp_args,
  link_with: TLibCommon,
)

# Utilities static library
Utilities_src = files(
  'source/Lib/Utilities/TVideoIOYuv.cpp',
  'source/Lib/Utilities/program_options_lite.cpp',
)

Utilities = static_library('Utilities',
  Utilities_src,
  include_directories: common_inc,
  cpp_args: common_cpp_args,
)

# TAppDecoder executable (H.265 decoder)
TAppDecoder_src = files(
  'source/App/TAppDecoder/TAppDecCfg.cpp',
  'source/App/TAppDecoder/TAppDecTop.cpp',
  'source/App/TAppDecoder/decmain.cpp',
)

TAppDecoder_inc = include_directories(
  'source/App/TAppDecoder',
  'source/Lib/TLibCommon',
  'source/Lib/TLibDecoder',
  'source/Lib/Utilities',
  'source/Lib/libmd5',
  'source/Lib',
  '.'
)

TAppDecoder = executable('TAppDecoder',
  TAppDecoder_src,
  include_directories: TAppDecoder_inc,
  cpp_args: common_cpp_args,
  link_with: [TLibCommon, TLibDecoder, Utilities],
)
