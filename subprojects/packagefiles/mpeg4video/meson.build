# Native meson.build for the MPEG-4 Visual reference decoder (vm_dec)
# ISO/IEC 14496-5 Reference Software
# This replaces the original Makefile to integrate with the meson build system
#
# This file is copied to contrib/MPEG-4_video_refSoft/ by build/download_deps.py

project('mpeg4video', 'cpp',
  version: '2.5',
  default_options: [
    'cpp_std=gnu++98',
    'buildtype=release',
    'warning_level=0',
  ]
)

cc = meson.get_compiler('cpp')

# The reference software predates C++98: the pre-standard iostream headers and the names used
# without the std:: prefix are provided by Fluster's compatibility headers
compat_dir = meson.current_source_dir() / '..' / '..' / 'build' / 'compat' / 'mpeg4video'

vm_dec_cpp_args = [
  '-w',
  # Only the decoder is needed, with the features its Makefile enables. _VTC_DECODER_ is only
  # used by vtcdec.cpp, which defines the VTC globals, but the Makefile builds it separately
  '-D_VTC_DECODER_',
  '-D_ERSSP_',
  '-D__DOUBLE_PRECISION_',
  '-D_OBSS_',
  '-DFGSPOSTCLIP',
  '-I' + compat_dir,
  '-include', compat_dir / 'compat.h',
]

if cc.get_id() == 'clang'
  # What GCC accepts with -fpermissive is an error for clang, unless it is told that it is Microsoft code
  vm_dec_cpp_args += '-fms-extensions'
else
  vm_dec_cpp_args += ['-fpermissive', '-fno-operator-names']
endif

if host_machine.system() == 'darwin'
  # macOS has no malloc.h
  vm_dec_cpp_args += '-I' + meson.current_source_dir() / '..' / '..' / 'build' / 'compat' / 'macos'
endif

# Sources of the vm_dec target in the original Makefile
vm_dec_sources = files(
  'app/decoder/decoder.cpp',
  'sys/block.cpp',
  'sys/cae.cpp',
  'sys/dct.cpp',
  'sys/decoder/blkdec.cpp',
  'sys/decoder/bp_fgs_dec.cpp',
  'sys/decoder/errdec.cpp',
  'sys/decoder/mbdec.cpp',
  'sys/decoder/mbheaddec.cpp',
  'sys/decoder/mbinterlacedec.cpp',
  'sys/decoder/mcdec.cpp',
  'sys/decoder/mvdec.cpp',
  'sys/decoder/newpdec.cpp',
  'sys/decoder/rvlcdec.cpp',
  'sys/decoder/shpdec.cpp',
  'sys/decoder/sptdec.cpp',
  'sys/decoder/vopmbdec.cpp',
  'sys/decoder/vopsedec.cpp',
  'sys/error.cpp',
  'sys/gmc_motion.cpp',
  'sys/gmc_util.cpp',
  'sys/mb.cpp',
  'sys/mc.cpp',
  'sys/mcpad.cpp',
  'sys/mode.cpp',
  'sys/mv.cpp',
  'sys/newpred.cpp',
  'sys/rrv.cpp',
  'sys/shape.cpp',
  'sys/spt.cpp',
  'sys/tps_bfshape.cpp',
  'sys/tps_enhcbuf.cpp',
  'sys/vopses.cpp',
  'tools/entropy/bitstrm.cpp',
  'tools/entropy/huffman.cpp',
  'tools/sadct/sadct.cpp',
  'type/basic.cpp',
  'type/geom.cpp',
  'type/grayc.cpp',
  'type/grayf.cpp',
  'type/grayi.cpp',
  'type/svd.cpp',
  'type/typeapi.cpp',
  'type/vop.cpp',
  'type/warp.cpp',
  'type/yuvac.cpp',
  'type/yuvai.cpp',
  'vtc/main/seg.cpp',
  'vtc/main/vtcdec.cpp',
  'vtc/main/wavelet.cpp',
  'vtc/main/write_image.cpp',
  'vtc/pezw/PEZW_ac.cpp',
  'vtc/pezw/PEZW_globals.cpp',
  'vtc/pezw/PEZW_textureLayerBQ.cpp',
  'vtc/pezw/PEZW_utils.cpp',
  'vtc/pezw/wvtPEZW.cpp',
  'vtc/pezw/wvtpezw_tree_decode.cpp',
  'vtc/pezw/wvtpezw_tree_encode.cpp',
  'vtc/pezw/wvtpezw_tree_init_decode.cpp',
  'vtc/pezw/wvtpezw_tree_init_encode.cpp',
  'vtc/shape/BinArCodec.cpp',
  'vtc/shape/ShapeBaseCommon.cpp',
  'vtc/shape/ShapeBaseDecode.cpp',
  'vtc/shape/ShapeBaseEncode.cpp',
  'vtc/shape/ShapeDecoding.cpp',
  'vtc/shape/ShapeEncoding.cpp',
  'vtc/shape/ShapeEnhCommon.cpp',
  'vtc/shape/ShapeEnhDecode.cpp',
  'vtc/shape/ShapeEnhEncode.cpp',
  'vtc/shape/ShapeUtil.cpp',
  'vtc/wavelet/download_filter.cpp',
  'vtc/wavelet/dwt.cpp',
  'vtc/wavelet/dwt_aux.cpp',
  'vtc/wavelet/dwtmask.cpp',
  'vtc/wavelet/idwt.cpp',
  'vtc/wavelet/idwt_aux.cpp',
  'vtc/wavelet/idwtmask.cpp',
  'vtc/wavelet/imagebox.cpp',
  'vtc/zte/ac.cpp',
  'vtc/zte/bitpack.cpp',
  'vtc/zte/ztscanUtil.cpp',
  'vtc/zte/ztscan_dec.cpp',
  'vtc/ztq/QMInit.cpp',
  'vtc/ztq/QMUtils.cpp',
  'vtc/ztq/Utils.cpp',
  'vtc/ztq/decQM.cpp',
  'vtc/ztq/errorHandler.cpp',
  'vtc/ztq/msg.cpp',
  'vtc/ztq/quant.cpp',
)

# Math library
m_dep = cc.find_library('m', required: false)

vm_dec = executable('vm_dec',
  vm_dec_sources,
  include_directories: include_directories(
    'sys',
    'sys/encoder',
    'sys/decoder',
    'type',
    'tools',
    'tools/entropy',
    'vtc/include',
    'vtc/ztq',
    'vtc/zte',
    'vtc/wavelet',
    'vtc/pezw',
    'vtc/shape',
  ),
  cpp_args: vm_dec_cpp_args,
  dependencies: [m_dep],
  install: false,
)
