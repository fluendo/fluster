# Report

## Table of Contents

- [Report](#report)
  - [Table of Contents](#table-of-contents)
  - [Intel environment](#intel-environment)
    - [H.266/VVC Intel](#h266vvc-intel)
    - [H.265/HEVC Intel](#h265hevc-intel)
    - [H.264/AVC Intel](#h264avc-intel)
  - [Nvidia environment](#nvidia-environment)
    - [H.266/VVC Nvidia](#h266vvc-nvidia)
    - [H.265/HEVC Nvidia](#h265hevc-nvidia)
    - [H.264/AVC Nvidia](#h264avc-nvidia)

## Intel environment

Lenovo ThinkPad T15p Gen 2i using iHD driver:

```
libva info: VA-API version 1.14.0
libva info: Trying to open /usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so
libva info: Found init function __vaDriverInit_1_14
libva info: va_openDriver() returns 0
vainfo: VA-API version: 1.14 (libva 2.12.0)
vainfo: Driver version: Intel iHD driver for Intel(R) Gen Graphics - 22.3.1 ()
vainfo: Supported profile and entrypoints
      VAProfileNone                   : VAEntrypointVideoProc
      VAProfileNone                   : VAEntrypointStats
      VAProfileMPEG2Simple            : VAEntrypointVLD
      VAProfileMPEG2Simple            : VAEntrypointEncSlice
      VAProfileMPEG2Main              : VAEntrypointVLD
      VAProfileMPEG2Main              : VAEntrypointEncSlice
      VAProfileH264Main               : VAEntrypointVLD
      VAProfileH264Main               : VAEntrypointEncSlice
      VAProfileH264Main               : VAEntrypointFEI
      VAProfileH264Main               : VAEntrypointEncSliceLP
      VAProfileH264High               : VAEntrypointVLD
      VAProfileH264High               : VAEntrypointEncSlice
      VAProfileH264High               : VAEntrypointFEI
      VAProfileH264High               : VAEntrypointEncSliceLP
      VAProfileVC1Simple              : VAEntrypointVLD
      VAProfileVC1Main                : VAEntrypointVLD
      VAProfileVC1Advanced            : VAEntrypointVLD
      VAProfileJPEGBaseline           : VAEntrypointVLD
      VAProfileJPEGBaseline           : VAEntrypointEncPicture
      VAProfileH264ConstrainedBaseline: VAEntrypointVLD
      VAProfileH264ConstrainedBaseline: VAEntrypointEncSlice
      VAProfileH264ConstrainedBaseline: VAEntrypointFEI
      VAProfileH264ConstrainedBaseline: VAEntrypointEncSliceLP
      VAProfileVP8Version0_3          : VAEntrypointVLD
      VAProfileHEVCMain               : VAEntrypointVLD
      VAProfileHEVCMain               : VAEntrypointEncSlice
      VAProfileHEVCMain               : VAEntrypointFEI
      VAProfileHEVCMain               : VAEntrypointEncSliceLP
      VAProfileHEVCMain10             : VAEntrypointVLD
      VAProfileHEVCMain10             : VAEntrypointEncSlice
      VAProfileHEVCMain10             : VAEntrypointEncSliceLP
      VAProfileVP9Profile0            : VAEntrypointVLD
      VAProfileVP9Profile1            : VAEntrypointVLD
      VAProfileVP9Profile2            : VAEntrypointVLD
      VAProfileVP9Profile3            : VAEntrypointVLD
      VAProfileHEVCMain12             : VAEntrypointVLD
      VAProfileHEVCMain12             : VAEntrypointEncSlice
      VAProfileHEVCMain422_10         : VAEntrypointVLD
      VAProfileHEVCMain422_10         : VAEntrypointEncSlice
      VAProfileHEVCMain422_12         : VAEntrypointVLD
      VAProfileHEVCMain422_12         : VAEntrypointEncSlice
      VAProfileHEVCMain444            : VAEntrypointVLD
      VAProfileHEVCMain444            : VAEntrypointEncSliceLP
      VAProfileHEVCMain444_10         : VAEntrypointVLD
      VAProfileHEVCMain444_10         : VAEntrypointEncSliceLP
      VAProfileHEVCMain444_12         : VAEntrypointVLD
      VAProfileHEVCSccMain            : VAEntrypointVLD
      VAProfileHEVCSccMain            : VAEntrypointEncSliceLP
      VAProfileHEVCSccMain10          : VAEntrypointVLD
      VAProfileHEVCSccMain10          : VAEntrypointEncSliceLP
      VAProfileHEVCSccMain444         : VAEntrypointVLD
      VAProfileHEVCSccMain444         : VAEntrypointEncSliceLP
      VAProfileAV1Profile0            : VAEntrypointVLD
      VAProfileHEVCSccMain444_10      : VAEntrypointVLD
      VAProfileHEVCSccMain444_10      : VAEntrypointEncSliceLP
```

GStreamer:

```
GStreamer version 1.20.3
```

FFmpeg:

```
ffmpeg version 7.1
```

### H.266/VVC Intel
#### Test suite: JVET-VVC_draft6

`./fluster.py run -d FFmpeg-H.266 VVCSoftware_VTM-H266 VVdeC-H266 -ts JVET-VVC_draft6 -s`

|Test|FFmpeg-H.266|VVCSoftware_VTM-H266|VVdeC-H266|
|-|-|-|-|
|10b400_A_Bytedance_2|✔️|✔️|✔️|
|10b400_B_Bytedance_2|⌛|⌛|✔️|
|10b422_A_Sony_4|✔️|✔️|❌|
|10b422_B_Sony_4|✔️|✔️|❌|
|10b422_C_Sony_4|✔️|✔️|❌|
|10b422_D_Sony_4|✔️|✔️|❌|
|10b422_E_Sony_4|✔️|✔️|❌|
|10b422_F_Sony_4|✔️|✔️|❌|
|10b422_G_Sony_4|☠|✔️|☠|
|10b422_H_Sony_4|☠|✔️|☠|
|10b422_I_Sony_4|❌|✔️|☠|
|10b422_J_Sony_4|❌|✔️|☠|
|10b422_K_Sony_4|❌|✔️|☠|
|10b422_L_Sony_4|❌|✔️|☠|
|10b444_A_Kwai_3|✔️|✔️|✔️|
|10b444_B_Kwai_3|⌛|⌛|✔️|
|8b400_A_Bytedance_2|✔️|✔️|✔️|
|8b400_B_Bytedance_2|✔️|✔️|✔️|
|8b420_A_Bytedance_2|✔️|✔️|✔️|
|8b420_B_Bytedance_2|✔️|✔️|✔️|
|8b422_A_Sony_4|✔️|✔️|❌|
|8b422_B_Sony_4|✔️|✔️|❌|
|8b422_C_Sony_4|✔️|✔️|❌|
|8b422_D_Sony_4|✔️|✔️|❌|
|8b422_E_Sony_4|✔️|✔️|❌|
|8b422_F_Sony_4|✔️|✔️|❌|
|8b422_G_Sony_4|☠|✔️|☠|
|8b422_H_Sony_4|☠|✔️|☠|
|8b422_I_Sony_4|❌|✔️|☠|
|8b422_J_Sony_4|❌|✔️|☠|
|8b422_K_Sony_4|❌|✔️|☠|
|8b422_L_Sony_4|❌|✔️|☠|
|8b444_A_Kwai_2|❌|✔️|☠|
|8b444_B_Kwai_2|☠|⌛|☠|
|ACT_A_Kwai_3|❌|✔️|☠|
|ACT_B_Kwai_3|☠|⌛|☠|
|ACTPIC_A_Huawei_3|✔️|✔️|✔️|
|ACTPIC_B_Huawei_3|✔️|✔️|✔️|
|ACTPIC_C_Huawei_3|✔️|✔️|✔️|
|AFF_A_HUAWEI_2|✔️|✔️|✔️|
|AFF_B_HUAWEI_2|✔️|✔️|✔️|
|ALF_A_Huawei_3|✔️|✔️|✔️|
|ALF_B_Huawei_3|✔️|✔️|✔️|
|ALF_C_KDDI_3|✔️|✔️|✔️|
|ALF_D_Qualcomm_2|✔️|✔️|✔️|
|AMVR_A_HHI_3|✔️|✔️|✔️|
|AMVR_B_HHI_3|✔️|⌛|✔️|
|APSALF_A_Qualcomm_2|✔️|✔️|✔️|
|APSLMCS_A_Dolby_3|✔️|⌛|✔️|
|APSLMCS_B_Dolby_3|✔️|⌛|✔️|
|APSLMCS_C_Dolby_2|⌛|⌛|✔️|
|APSLMCS_D_Dolby_1|✔️|✔️|✔️|
|APSLMCS_E_Dolby_1|✔️|✔️|✔️|
|APSMULT_A_MediaTek_4|✔️|✔️|✔️|
|APSMULT_B_MediaTek_4|✔️|✔️|✔️|
|AUD_A_Broadcom_3|✔️|✔️|✔️|
|BCW_A_MediaTek_4|✔️|✔️|✔️|
|BDOF_A_MediaTek_4|✔️|✔️|✔️|
|BDPCM_A_Orange_2|✔️|✔️|✔️|
|BOUNDARY_A_Huawei_3|❌|✔️|✔️|
|BUMP_A_LGE_2|✔️|✔️|✔️|
|BUMP_B_LGE_2|✔️|✔️|✔️|
|BUMP_C_LGE_2|✔️|✔️|✔️|
|CCALF_A_Sharp_3|✔️|✔️|✔️|
|CCALF_B_Sharp_3|✔️|✔️|✔️|
|CCALF_C_Sharp_3|✔️|✔️|✔️|
|CCALF_D_Sharp_3|✔️|✔️|✔️|
|CCLM_A_KDDI_2|✔️|✔️|✔️|
|CIIP_A_MediaTek_4|✔️|✔️|✔️|
|CodingToolsSets_A_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_B_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_C_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_D_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_E_Tencent_1|✔️|✔️|✔️|
|CROP_A_Panasonic_3|✔️|✔️|✔️|
|CROP_B_Panasonic_4|✔️|✔️|✔️|
|CST_A_MediaTek_4|✔️|✔️|✔️|
|CTU_A_MediaTek_4|✔️|✔️|✔️|
|CTU_B_MediaTek_4|✔️|✔️|✔️|
|CTU_C_MediaTek_4|✔️|✔️|✔️|
|CUBEMAP_A_MediaTek_3|✔️|⌛|✔️|
|CUBEMAP_B_MediaTek_3|✔️|⌛|✔️|
|CUBEMAP_C_MediaTek_3|⌛|⌛|✔️|
|DCI_A_Tencent_3|✔️|✔️|✔️|
|DCI_B_Tencent_3|✔️|✔️|✔️|
|DEBLOCKING_A_Sharp_3|✔️|✔️|✔️|
|DEBLOCKING_B_Sharp_2|✔️|✔️|✔️|
|DEBLOCKING_C_Huawei_3|✔️|✔️|✔️|
|DEBLOCKING_E_Ericsson_3|✔️|✔️|✔️|
|DEBLOCKING_F_Ericsson_2|✔️|✔️|✔️|
|DMVR_A_Huawei_3|✔️|✔️|✔️|
|DMVR_B_KDDI_4|✔️|✔️|✔️|
|DPB_A_Sharplabs_2|✔️|✔️|✔️|
|DPB_B_Sharplabs_2|✔️|✔️|✔️|
|DQ_A_HHI_3|✔️|✔️|✔️|
|DQ_B_HHI_3|⌛|⌛|⌛|
|ENT444HIGHTIER_A_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_B_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_C_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_D_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_A_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_B_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_C_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_D_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_A_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_B_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_C_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_D_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_A_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_B_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_C_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_D_Sony_3|✔️|✔️|✔️|
|ENTROPY_A_Chipsnmedia_2|⌛|⌛|⌛|
|ENTROPY_B_Sharp_2|✔️|✔️|✔️|
|ENTROPY_C_Qualcomm_1|✔️|✔️|✔️|
|ERP_A_MediaTek_3|✔️|✔️|✔️|
|FIELD_A_Panasonic_4|❌|✔️|✔️|
|FIELD_B_Panasonic_2|❌|✔️|✔️|
|FILLER_A_Bytedance_1|✔️|✔️|✔️|
|GDR_A_ERICSSON_2|✔️|✔️|✔️|
|GDR_B_NOKIA_2|✔️|✔️|✔️|
|GDR_C_NOKIA_2|✔️|✔️|✔️|
|GDR_D_ERICSSON_1|❌|☠|✔️|
|GPM_A_Alibaba_3|✔️|✔️|✔️|
|GPM_B_Alibaba_1|✔️|✔️|✔️|
|HLG_A_NHK_4|⌛|⌛|⌛|
|HLG_B_NHK_4|⌛|⌛|✔️|
|HRD_A_Fujitsu_3|✔️|✔️|✔️|
|HRD_B_Fujitsu_2|✔️|☠|✔️|
|IBC_A_Tencent_2|✔️|✔️|✔️|
|IBC_B_Tencent_2|✔️|✔️|✔️|
|IBC_C_Tencent_2|✔️|✔️|✔️|
|IBC_D_Tencent_2|✔️|✔️|✔️|
|ILRPL_A_Huawei_2|❌|☠|☠|
|IP_A_Huawei_2|✔️|✔️|✔️|
|IP_B_Nokia_1|✔️|✔️|✔️|
|ISP_A_HHI_3|✔️|✔️|✔️|
|ISP_B_HHI_3|⌛|⌛|✔️|
|JCCR_A_Nokia_2|✔️|✔️|✔️|
|JCCR_B_Nokia_2|✔️|✔️|✔️|
|JCCR_C_HHI_3|✔️|✔️|✔️|
|JCCR_D_HHI_3|⌛|⌛|⌛|
|JCCR_E_Nokia_1|✔️|✔️|✔️|
|JCCR_F_Nokia_1|✔️|✔️|✔️|
|LFNST_A_LGE_4|✔️|✔️|✔️|
|LFNST_B_LGE_4|✔️|✔️|✔️|
|LFNST_C_HHI_3|✔️|✔️|✔️|
|LFNST_D_HHI_3|⌛|⌛|⌛|
|LMCS_A_Dolby_3|✔️|✔️|✔️|
|LMCS_B_Dolby_2|✔️|⌛|✔️|
|LMCS_C_Dolby_1|✔️|✔️|✔️|
|LOSSLESS_A_HHI_3|✔️|✔️|✔️|
|LOSSLESS_B_HHI_3|✔️|✔️|✔️|
|LTRP_A_ERICSSON_3|✔️|✔️|✔️|
|MERGE_A_Qualcomm_2|✔️|✔️|✔️|
|MERGE_B_Qualcomm_2|✔️|✔️|✔️|
|MERGE_C_Qualcomm_2|✔️|✔️|✔️|
|MERGE_D_Qualcomm_2|✔️|✔️|✔️|
|MERGE_E_Qualcomm_2|✔️|✔️|✔️|
|MERGE_F_Qualcomm_2|⌛|⌛|✔️|
|MERGE_G_Qualcomm_2|⌛|⌛|✔️|
|MERGE_H_Qualcomm_2|⌛|⌛|✔️|
|MERGE_I_Qualcomm_2|⌛|⌛|✔️|
|MERGE_J_Qualcomm_2|⌛|⌛|✔️|
|MIP_A_HHI_3|✔️|✔️|✔️|
|MIP_B_HHI_3|✔️|✔️|✔️|
|MMVD_A_SAMSUNG_3|⌛|⌛|✔️|
|MNUT_A_Nokia_3|☠|✔️|✔️|
|MNUT_B_Nokia_2|☠|✔️|✔️|
|MPM_A_LGE_3|⌛|⌛|✔️|
|MRLP_A_HHI_2|✔️|✔️|✔️|
|MRLP_B_HHI_2|✔️|✔️|✔️|
|MTS_A_LGE_4|✔️|✔️|✔️|
|MTS_B_LGE_4|✔️|✔️|✔️|
|MTS_LFNST_A_LGE_4|✔️|✔️|✔️|
|MTS_LFNST_B_LGE_4|✔️|✔️|✔️|
|MVCOMP_A_Sharp_2|✔️|✔️|✔️|
|OLS_A_Tencent_4|❌|☠|☠|
|OLS_B_Tencent_4|❌|☠|☠|
|OLS_C_Tencent_4|❌|☠|☠|
|OPI_A_Nokia_1|✔️|✔️|✔️|
|OPI_B_Nokia_2|❌|☠|☠|
|PALETTE_A_Alibaba_2|❌|✔️|☠|
|PALETTE_B_Alibaba_2|☠|✔️|☠|
|PALETTE_C_Alibaba_2|☠|✔️|☠|
|PALETTE_D_Alibaba_2|☠|✔️|☠|
|PALETTE_E_Alibaba_2|❌|✔️|☠|
|PDPC_A_Qualcomm_3|✔️|✔️|✔️|
|PDPC_B_Qualcomm_3|✔️|✔️|✔️|
|PDPC_C_Qualcomm_2|✔️|✔️|✔️|
|PHSH_B_Sharp_1|✔️|✔️|✔️|
|PMERGE_A_MediaTek_1|✔️|✔️|✔️|
|PMERGE_B_MediaTek_1|✔️|✔️|✔️|
|PMERGE_C_MediaTek_1|✔️|✔️|✔️|
|PMERGE_D_MediaTek_1|✔️|✔️|✔️|
|PMERGE_E_MediaTek_1|✔️|✔️|✔️|
|POC_A_Nokia_1|✔️|✔️|✔️|
|POUT_A_Sharplabs_2|✔️|✔️|✔️|
|PPS_A_Bytedance_1|⌛|⌛|✔️|
|PPS_B_Bytedance_1|✔️|✔️|✔️|
|PPS_C_Bytedance_1|✔️|✔️|✔️|
|PQ_A_Dolby_1|⌛|⌛|✔️|
|PROF_A_Interdigital_3|✔️|✔️|✔️|
|PROF_B_Interdigital_3|✔️|✔️|✔️|
|PSEXT_A_Nokia_2|✔️|✔️|✔️|
|PSEXT_B_Nokia_2|✔️|✔️|✔️|
|QTBTT_A_MediaTek_4|✔️|✔️|✔️|
|QUANT_A_Huawei_2|✔️|✔️|✔️|
|QUANT_B_Huawei_2|✔️|✔️|✔️|
|QUANT_C_Huawei_2|✔️|✔️|✔️|
|QUANT_D_Huawei_4|✔️|✔️|✔️|
|QUANT_E_Interdigital_1|✔️|✔️|✔️|
|RAP_A_HHI_1|✔️|✔️|✔️|
|RAP_B_HHI_1|✔️|✔️|✔️|
|RAP_C_HHI_1|✔️|✔️|✔️|
|RAP_D_HHI_1|✔️|✔️|✔️|
|RPL_A_ERICSSON_2|✔️|✔️|✔️|
|RPR_A_Alibaba_4|❌|✔️|✔️|
|RPR_B_Alibaba_3|❌|✔️|✔️|
|RPR_C_Alibaba_3|❌|✔️|✔️|
|RPR_D_Qualcomm_1|❌|✔️|✔️|
|SAO_A_SAMSUNG_3|✔️|✔️|✔️|
|SAO_B_SAMSUNG_3|✔️|✔️|✔️|
|SAO_C_SAMSUNG_3|✔️|✔️|✔️|
|SBT_A_HUAWEI_2|✔️|✔️|✔️|
|SbTMVP_A_Bytedance_3|✔️|✔️|✔️|
|SbTMVP_B_Bytedance_3|✔️|✔️|✔️|
|SCALING_A_InterDigital_1|✔️|✔️|✔️|
|SCALING_B_InterDigital_1|✔️|✔️|✔️|
|SCALING_C_InterDigital_1|✔️|✔️|✔️|
|SDH_A_Dolby_2|✔️|✔️|✔️|
|SLICES_A_HUAWEI_2|✔️|✔️|✔️|
|SMVD_A_HUAWEI_2|✔️|✔️|✔️|
|SPATSCAL444_A_Qualcomm_2|❌|☠|☠|
|SPATSCAL_A_Qualcomm_3|❌|☠|☠|
|SPS_A_Bytedance_1|⌛|⌛|✔️|
|SPS_B_Bytedance_1|✔️|✔️|✔️|
|SPS_C_Bytedance_1|✔️|✔️|✔️|
|STILL444_A_KDDI_1|✔️|✔️|✔️|
|STILL444_B_ERICSSON_1|✔️|✔️|✔️|
|STILL_A_KDDI_1|✔️|✔️|✔️|
|STILL_B_ERICSSON_1|✔️|✔️|✔️|
|SUBPIC_A_HUAWEI_3|✔️|✔️|✔️|
|SUBPIC_B_HUAWEI_3|✔️|✔️|✔️|
|SUBPIC_C_ERICSSON_1|☠|✔️|✔️|
|SUBPIC_D_ERICSSON_1|☠|✔️|✔️|
|SUBPIC_E_MediaTek_1|✔️|✔️|✔️|
|SUFAPS_A_HHI_1|✔️|✔️|✔️|
|TEMPSCAL_A_Panasonic_4|✔️|⌛|✔️|
|TEMPSCAL_B_Panasonic_5|⌛|⌛|✔️|
|TEMPSCAL_C_Panasonic_3|⌛|⌛|✔️|
|TILE_A_Nokia_2|✔️|✔️|✔️|
|TILE_B_Nokia_2|✔️|✔️|✔️|
|TILE_C_Nokia_2|✔️|✔️|✔️|
|TILE_D_Nokia_2|✔️|✔️|✔️|
|TILE_E_Nokia_2|✔️|✔️|✔️|
|TILE_F_Nokia_2|✔️|✔️|✔️|
|TILE_G_Nokia_2|✔️|✔️|✔️|
|TMVP_A_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_B_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_C_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_D_Chipsnmedia_3|✔️|✔️|✔️|
|TRANS_A_Chipsnmedia_2|✔️|⌛|✔️|
|TRANS_B_Chipsnmedia_2|✔️|✔️|✔️|
|TRANS_C_Chipsnmedia_4|✔️|✔️|✔️|
|TRANS_D_Chipsnmedia_4|✔️|✔️|✔️|
|TREE_A_HHI_3|⌛|⌛|✔️|
|TREE_B_HHI_3|⌛|⌛|✔️|
|TREE_C_HHI_3|⌛|⌛|⌛|
|VIRTUAL_A_MediaTek_3|✔️|✔️|✔️|
|VIRTUAL_B_MediaTek_3|✔️|✔️|✔️|
|VPS_A_INTEL_3|❌|☠|☠|
|VPS_B_ERICSSON_1|❌|☠|☠|
|VPS_C_ERICSSON_1|☠|☠|☠|
|WP_A_InterDigital_3|✔️|✔️|✔️|
|WP_B_InterDigital_3|✔️|✔️|✔️|
|WPP_A_Sharp_3|✔️|✔️|✔️|
|WPP_B_Sharp_2|✔️|✔️|✔️|
|WRAP_A_InterDigital_4|✔️|✔️|✔️|
|WRAP_B_InterDigital_4|✔️|✔️|✔️|
|WRAP_C_InterDigital_4|✔️|✔️|✔️|
|WRAP_D_InterDigital_4|✔️|✔️|✔️|
|-|-|-|-|
|TOTAL|213/282|234/282|233/282|


### H.265/HEVC Intel
#### Test suite: JCT-VC-HEVC_V1

`./fluster.py run -d FFmpeg-H.265 FFmpeg-H.265-VAAPI GStreamer-H.265-VAAPI-Gst1.0 JCT-VT-H.265 -ts JCT-VC-HEVC_V1 -s`

|Test|FFmpeg-H.265|FFmpeg-H.265-VAAPI|GStreamer-H.265-VAAPI-Gst1.0|JCT-VT-H.265|
|-|-|-|-|-|
|AMP_A_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_B_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_D_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_E_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_F_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMVP_A_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_B_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_C_Samsung_7|✔️|✔️|✔️|✔️|
|BUMPING_A_ericsson_1|✔️|✔️|✔️|✔️|
|CAINIT_A_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_B_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_C_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_D_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_E_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_F_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_G_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_H_SHARP_3|✔️|✔️|✔️|✔️|
|CIP_A_Panasonic_3|✔️|✔️|✔️|✔️|
|cip_B_NEC_3|✔️|✔️|✔️|✔️|
|CIP_C_Panasonic_2|✔️|✔️|✔️|✔️|
|CONFWIN_A_Sony_1|✔️|✔️|❌|✔️|
|DBLK_A_MAIN10_VIXS_4|✔️|✔️|✔️|✔️|
|DBLK_A_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_B_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_C_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_D_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_E_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_F_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_G_VIXS_2|✔️|✔️|✔️|✔️|
|DELTAQP_A_BRCM_4|✔️|✔️|✔️|✔️|
|DELTAQP_B_SONY_3|✔️|✔️|✔️|✔️|
|DELTAQP_C_SONY_3|✔️|✔️|✔️|✔️|
|DSLICE_A_HHI_5|✔️|✔️|✔️|✔️|
|DSLICE_B_HHI_5|✔️|✔️|✔️|✔️|
|DSLICE_C_HHI_5|✔️|✔️|✔️|✔️|
|ENTP_A_QUALCOMM_1|✔️|✔️|✔️|✔️|
|ENTP_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|ENTP_C_Qualcomm_1|✔️|✔️|✔️|✔️|
|EXT_A_ericsson_4|✔️|✔️|✔️|✔️|
|FILLER_A_Sony_1|✔️|✔️|✔️|✔️|
|HRD_A_Fujitsu_3|✔️|✔️|✔️|✔️|
|INITQP_A_Sony_1|✔️|✔️|✔️|✔️|
|INITQP_B_Main10_Sony_1|✔️|✔️|✔️|✔️|
|ipcm_A_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_B_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_C_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_D_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_E_NEC_2|✔️|✔️|✔️|✔️|
|IPRED_A_docomo_2|✔️|✔️|✔️|✔️|
|IPRED_B_Nokia_3|✔️|✔️|☠|✔️|
|IPRED_C_Mitsubishi_3|✔️|✔️|✔️|✔️|
|LS_A_Orange_2|✔️|✔️|✔️|✔️|
|LS_B_Orange_4|✔️|✔️|✔️|✔️|
|LTRPSPS_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|MAXBINS_A_TI_5|✔️|✔️|✔️|✔️|
|MAXBINS_B_TI_5|✔️|✔️|✔️|✔️|
|MAXBINS_C_TI_5|✔️|✔️|✔️|✔️|
|MERGE_A_TI_3|✔️|✔️|✔️|✔️|
|MERGE_B_TI_3|✔️|✔️|✔️|✔️|
|MERGE_C_TI_3|✔️|✔️|✔️|✔️|
|MERGE_D_TI_3|✔️|✔️|✔️|✔️|
|MERGE_E_TI_3|✔️|✔️|✔️|✔️|
|MERGE_F_MTK_4|✔️|✔️|✔️|✔️|
|MERGE_G_HHI_4|✔️|✔️|✔️|✔️|
|MVCLIP_A_qualcomm_3|✔️|✔️|✔️|✔️|
|MVDL1ZERO_A_docomo_4|✔️|✔️|✔️|✔️|
|MVEDGE_A_qualcomm_3|✔️|✔️|✔️|✔️|
|NoOutPrior_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|NoOutPrior_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|NUT_A_ericsson_5|✔️|✔️|✔️|✔️|
|OPFLAG_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|OPFLAG_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|OPFLAG_C_Qualcomm_1|✔️|✔️|✔️|✔️|
|PICSIZE_A_Bossen_1|✔️|✔️|✔️|✔️|
|PICSIZE_B_Bossen_1|✔️|✔️|✔️|✔️|
|PICSIZE_C_Bossen_1|✔️|✔️|✔️|✔️|
|PICSIZE_D_Bossen_1|✔️|✔️|✔️|✔️|
|PMERGE_A_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_B_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_C_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_D_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_E_TI_3|✔️|✔️|✔️|✔️|
|POC_A_Bossen_3|✔️|✔️|✔️|✔️|
|PPS_A_qualcomm_7|✔️|✔️|✔️|✔️|
|PS_B_VIDYO_3|✔️|✔️|✔️|✔️|
|RAP_A_docomo_6|✔️|✔️|✔️|✔️|
|RAP_B_Bossen_2|✔️|✔️|✔️|✔️|
|RPLM_A_qualcomm_4|✔️|✔️|✔️|✔️|
|RPLM_B_qualcomm_4|✔️|✔️|✔️|✔️|
|RPS_A_docomo_5|✔️|✔️|✔️|✔️|
|RPS_B_qualcomm_5|✔️|✔️|✔️|✔️|
|RPS_C_ericsson_5|✔️|✔️|✔️|✔️|
|RPS_D_ericsson_6|✔️|✔️|✔️|✔️|
|RPS_E_qualcomm_5|✔️|✔️|✔️|✔️|
|RPS_F_docomo_2|✔️|✔️|✔️|✔️|
|RQT_A_HHI_4|✔️|✔️|✔️|✔️|
|RQT_B_HHI_4|✔️|✔️|✔️|✔️|
|RQT_C_HHI_4|✔️|✔️|✔️|✔️|
|RQT_D_HHI_4|✔️|✔️|✔️|✔️|
|RQT_E_HHI_4|✔️|✔️|✔️|✔️|
|RQT_F_HHI_4|✔️|✔️|✔️|✔️|
|RQT_G_HHI_4|✔️|✔️|✔️|✔️|
|SAO_A_MediaTek_4|✔️|✔️|✔️|✔️|
|SAO_B_MediaTek_5|✔️|✔️|✔️|✔️|
|SAO_C_Samsung_5|✔️|✔️|✔️|✔️|
|SAO_D_Samsung_5|✔️|✔️|✔️|✔️|
|SAO_E_Canon_4|✔️|✔️|✔️|✔️|
|SAO_F_Canon_3|✔️|✔️|✔️|✔️|
|SAO_G_Canon_3|✔️|✔️|✔️|✔️|
|SAO_H_Parabola_1|✔️|✔️|✔️|✔️|
|SAODBLK_A_MainConcept_4|❌|✔️|✔️|✔️|
|SAODBLK_B_MainConcept_4|❌|✔️|✔️|✔️|
|SDH_A_Orange_4|✔️|✔️|✔️|✔️|
|SLICES_A_Rovi_3|✔️|✔️|✔️|✔️|
|SLIST_A_Sony_5|✔️|✔️|✔️|✔️|
|SLIST_B_Sony_9|✔️|✔️|✔️|✔️|
|SLIST_C_Sony_4|✔️|✔️|✔️|✔️|
|SLIST_D_Sony_9|✔️|✔️|✔️|✔️|
|SLPPLP_A_VIDYO_2|✔️|✔️|✔️|✔️|
|STRUCT_A_Samsung_7|✔️|✔️|✔️|✔️|
|STRUCT_B_Samsung_7|✔️|✔️|✔️|✔️|
|TILES_A_Cisco_2|✔️|✔️|✔️|✔️|
|TILES_B_Cisco_1|✔️|✔️|✔️|✔️|
|TMVP_A_MS_3|✔️|✔️|✔️|✔️|
|TSCL_A_VIDYO_5|✔️|✔️|✔️|✔️|
|TSCL_B_VIDYO_4|✔️|✔️|✔️|✔️|
|TSKIP_A_MS_3|✔️|✔️|✔️|✔️|
|TSUNEQBD_A_MAIN10_Technicolor_2|☠|☠|❌|✔️|
|TUSIZE_A_Samsung_1|✔️|✔️|✔️|✔️|
|VPSID_A_VIDYO_2|✔️|✔️|✔️|✔️|
|VPSSPSPPS_A_MainConcept_1|❌|❌|❌|✔️|
|WP_A_MAIN10_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_A_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_B_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_MAIN10_B_Toshiba_3|✔️|✔️|✔️|✔️|
|WPP_A_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_A_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_B_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_B_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_C_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_C_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_D_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_D_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_E_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_E_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_F_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_F_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|-|-|-|-|-|
|TOTAL|143/147|145/147|143/147|147/147|


### H.264/AVC Intel
#### Test suite: JVT-AVC_V1

`./fluster.py run -d FFmpeg-H.264 FFmpeg-H.264-VAAPI GStreamer-H.264-VAAPI-Gst1.0 JCT-VT-H.264 -ts JVT-AVC_V1 -s`

|Test|FFmpeg-H.264|FFmpeg-H.264-VAAPI|GStreamer-H.264-VAAPI-Gst1.0|JCT-VT-H.264|
|-|-|-|-|-|
|AUD_MW_E|✔️|✔️|✔️|✔️|
|BA1_FT_C|✔️|✔️|✔️|✔️|
|BA1_Sony_D|✔️|✔️|✔️|✔️|
|BA2_Sony_F|✔️|✔️|✔️|✔️|
|BA3_SVA_C|✔️|☠|☠|✔️|
|BA_MW_D|✔️|✔️|✔️|✔️|
|BAMQ1_JVC_C|✔️|✔️|✔️|✔️|
|BAMQ2_JVC_C|✔️|✔️|✔️|✔️|
|BANM_MW_D|✔️|✔️|✔️|✔️|
|BASQP1_Sony_C|✔️|✔️|✔️|✔️|
|CABA1_Sony_D|✔️|✔️|✔️|✔️|
|CABA1_SVA_B|✔️|✔️|✔️|✔️|
|CABA2_Sony_E|✔️|✔️|✔️|✔️|
|CABA2_SVA_B|✔️|✔️|✔️|✔️|
|CABA3_Sony_C|✔️|✔️|✔️|✔️|
|CABA3_SVA_B|✔️|✔️|✔️|✔️|
|CABA3_TOSHIBA_E|✔️|✔️|✔️|✔️|
|cabac_mot_fld0_full|✔️|✔️|✔️|✔️|
|cabac_mot_frm0_full|✔️|✔️|✔️|✔️|
|cabac_mot_mbaff0_full|✔️|✔️|✔️|✔️|
|cabac_mot_picaff0_full|✔️|✔️|✔️|✔️|
|CABACI3_Sony_B|✔️|✔️|✔️|✔️|
|CABAST3_Sony_E|✔️|✔️|✔️|✔️|
|CABASTBR3_Sony_B|✔️|✔️|✔️|✔️|
|CABREF3_Sand_D|✔️|✔️|✔️|✔️|
|CACQP3_Sony_D|✔️|✔️|✔️|✔️|
|CAFI1_SVA_C|✔️|✔️|✔️|✔️|
|CAMA1_Sony_C|✔️|✔️|✔️|✔️|
|CAMA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|cama1_vtc_c|✔️|✔️|✔️|✔️|
|cama2_vtc_b|✔️|✔️|✔️|✔️|
|CAMA3_Sand_E|✔️|✔️|✔️|✔️|
|cama3_vtc_b|✔️|✔️|✔️|✔️|
|CAMACI3_Sony_C|✔️|✔️|✔️|✔️|
|CAMANL1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAMANL2_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAMANL3_Sand_E|✔️|✔️|✔️|✔️|
|CAMASL3_Sony_B|✔️|✔️|✔️|✔️|
|CAMP_MOT_MBAFF_L30|✔️|✔️|✔️|✔️|
|CAMP_MOT_MBAFF_L31|✔️|✔️|✔️|✔️|
|CANL1_Sony_E|✔️|✔️|✔️|✔️|
|CANL1_SVA_B|✔️|✔️|✔️|✔️|
|CANL1_TOSHIBA_G|✔️|✔️|✔️|✔️|
|CANL2_Sony_E|✔️|✔️|✔️|✔️|
|CANL2_SVA_B|✔️|✔️|✔️|✔️|
|CANL3_Sony_C|✔️|✔️|✔️|✔️|
|CANL3_SVA_B|✔️|✔️|✔️|✔️|
|CANL4_SVA_B|✔️|✔️|✔️|✔️|
|CANLMA2_Sony_C|✔️|✔️|✔️|✔️|
|CANLMA3_Sony_C|✔️|✔️|✔️|✔️|
|CAPA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAPAMA3_Sand_F|✔️|✔️|✔️|✔️|
|CAPCM1_Sand_E|✔️|✔️|✔️|✔️|
|CAPCMNL1_Sand_E|✔️|✔️|✔️|✔️|
|CAPM3_Sony_D|✔️|✔️|✔️|✔️|
|CAQP1_Sony_B|✔️|✔️|✔️|✔️|
|cavlc_mot_fld0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_frm0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_mbaff0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_picaff0_full_B|✔️|✔️|✔️|✔️|
|CAWP1_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CAWP5_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CI1_FT_B|✔️|✔️|✔️|✔️|
|CI_MW_D|✔️|✔️|✔️|✔️|
|CVBS3_Sony_C|✔️|✔️|✔️|✔️|
|CVCANLMA2_Sony_C|✔️|✔️|✔️|✔️|
|CVFC1_Sony_C|✔️|✔️|❌|✔️|
|CVFI1_Sony_D|✔️|✔️|✔️|✔️|
|CVFI1_SVA_C|✔️|✔️|✔️|✔️|
|CVFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVFI2_SVA_C|✔️|✔️|✔️|✔️|
|CVMA1_Sony_D|✔️|✔️|✔️|✔️|
|CVMA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL2_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMAPAQP3_Sony_E|✔️|✔️|✔️|✔️|
|CVMAQP2_Sony_G|✔️|✔️|✔️|✔️|
|CVMAQP3_Sony_D|✔️|✔️|✔️|✔️|
|CVMP_MOT_FLD_L30_B|✔️|✔️|✔️|✔️|
|CVMP_MOT_FRM_L31_B|✔️|✔️|✔️|✔️|
|CVNLFI1_Sony_C|✔️|✔️|✔️|✔️|
|CVNLFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVPA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVPCMNL1_SVA_C|✔️|✔️|✔️|✔️|
|CVPCMNL2_SVA_C|✔️|✔️|✔️|✔️|
|CVSE2_Sony_B|✔️|✔️|✔️|✔️|
|CVSE3_Sony_H|✔️|✔️|✔️|✔️|
|CVSEFDFT3_Sony_E|✔️|✔️|✔️|✔️|
|CVWP1_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP2_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP3_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP5_TOSHIBA_E|✔️|✔️|✔️|✔️|
|FI1_Sony_E|✔️|✔️|✔️|✔️|
|FM1_BT_B|☠|☠|☠|✔️|
|FM1_FT_E|❌|☠|❌|✔️|
|FM2_SVA_C|☠|☠|☠|✔️|
|HCBP1_HHI_A|✔️|✔️|✔️|✔️|
|HCBP2_HHI_A|✔️|✔️|✔️|✔️|
|HCMP1_HHI_A|✔️|✔️|✔️|✔️|
|LS_SVA_D|✔️|✔️|✔️|✔️|
|MIDR_MW_D|✔️|✔️|✔️|✔️|
|MPS_MW_A|✔️|✔️|✔️|✔️|
|MR1_BT_A|✔️|✔️|✔️|✔️|
|MR1_MW_A|✔️|✔️|✔️|✔️|
|MR2_MW_A|✔️|✔️|✔️|✔️|
|MR2_TANDBERG_E|✔️|☠|✔️|✔️|
|MR3_TANDBERG_B|✔️|☠|✔️|✔️|
|MR4_TANDBERG_C|✔️|☠|✔️|✔️|
|MR5_TANDBERG_C|✔️|☠|✔️|✔️|
|MR6_BT_B|✔️|☠|☠|✔️|
|MR7_BT_B|✔️|☠|☠|✔️|
|MR8_BT_B|✔️|☠|☠|✔️|
|MR9_BT_B|✔️|✔️|✔️|✔️|
|MV1_BRCM_D|✔️|✔️|✔️|✔️|
|NL1_Sony_D|✔️|✔️|✔️|✔️|
|NL2_Sony_H|✔️|✔️|✔️|✔️|
|NL3_SVA_E|✔️|✔️|✔️|✔️|
|NLMQ1_JVC_C|✔️|✔️|✔️|✔️|
|NLMQ2_JVC_C|✔️|✔️|✔️|✔️|
|NRF_MW_E|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_1_B|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_2_B|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_3_B|✔️|✔️|✔️|✔️|
|Sharp_MP_PAFF_1r2|✔️|✔️|✔️|✔️|
|Sharp_MP_PAFF_2r|✔️|✔️|✔️|✔️|
|SL1_SVA_B|✔️|✔️|✔️|✔️|
|SP1_BT_A|❌|☠|☠|❌|
|sp2_bt_b|❌|☠|☠|❌|
|SVA_BA1_B|✔️|✔️|✔️|✔️|
|SVA_BA2_D|✔️|✔️|✔️|✔️|
|SVA_Base_B|✔️|✔️|✔️|✔️|
|SVA_CL1_E|✔️|✔️|✔️|✔️|
|SVA_FM1_E|✔️|✔️|✔️|✔️|
|SVA_NL1_B|✔️|✔️|✔️|✔️|
|SVA_NL2_E|✔️|✔️|✔️|✔️|
|-|-|-|-|-|
|TOTAL|130/135|122/135|125/135|133/135|


## Nvidia environment

Lenovo ThinkPad T15p Gen 2i using Nvidia 535.183.01 driver:

```
Information string: NVIDIA VDPAU Driver Shared Library  535.183.01  Sun May 12 19:29:09 UTC 2024

Video surface:

name   width height types
-------------------------------------------
420     8192  8192  NV12 YV12
422     8192  8192  UYVY YUYV
444     8192  8192  NV24 YV24
420_16  8192  8192  P010 P016
422_16  8192  8192  UYVY YUYV
444_16  8192  8192  Y_U_V_444_16

Decoder capabilities:

name                        level macbs width height
----------------------------------------------------
MPEG1                           0 65536  4096  4096
MPEG2_SIMPLE                    3 65536  4096  4096
MPEG2_MAIN                      3 65536  4096  4096
H264_BASELINE                  51 65536  4096  4096
H264_MAIN                      51 65536  4096  4096
H264_HIGH                      51 65536  4096  4096
VC1_SIMPLE                      1  8190  2048  2048
VC1_MAIN                        2  8190  2048  2048
VC1_ADVANCED                    4  8190  2048  2048
MPEG4_PART2_SP                  3  8192  2048  2048
MPEG4_PART2_ASP                 5  8192  2048  2048
DIVX4_QMOBILE                   0  8192  2048  2048
DIVX4_MOBILE                    0  8192  2048  2048
DIVX4_HOME_THEATER              0  8192  2048  2048
DIVX4_HD_1080P                  0  8192  2048  2048
DIVX5_QMOBILE                   0  8192  2048  2048
DIVX5_MOBILE                    0  8192  2048  2048
DIVX5_HOME_THEATER              0  8192  2048  2048
DIVX5_HD_1080P                  0  8192  2048  2048
H264_CONSTRAINED_BASELINE      51 65536  4096  4096
H264_EXTENDED                  51 65536  4096  4096
H264_PROGRESSIVE_HIGH          51 65536  4096  4096
H264_CONSTRAINED_HIGH          51 65536  4096  4096
H264_HIGH_444_PREDICTIVE       51 65536  4096  4096
VP9_PROFILE_0                   1 262144  8192  8192
VP9_PROFILE_1                  --- not supported ---
VP9_PROFILE_2                   1 262144  8192  8192
VP9_PROFILE_3                  --- not supported ---
HEVC_MAIN                      153 262144  8192  8192
HEVC_MAIN_10                   153 262144  8192  8192
HEVC_MAIN_STILL                --- not supported ---
HEVC_MAIN_12                   153 262144  8192  8192
HEVC_MAIN_444                  153 262144  8192  8192
HEVC_MAIN_444_10               153 262144  8192  8192
HEVC_MAIN_444_12               153 262144  8192  8192

Output surface:

name              width height nat types
----------------------------------------------------
B8G8R8A8         32768 32768    y  Y8U8V8A8 V8U8Y8A8 A4I4 I4A4 A8I8 I8A8
R10G10B10A2      32768 32768    y  Y8U8V8A8 V8U8Y8A8 A4I4 I4A4 A8I8 I8A8

Bitmap surface:

name              width height
------------------------------
B8G8R8A8         32768 32768
R8G8B8A8         32768 32768
R10G10B10A2      32768 32768
B10G10R10A2      32768 32768
A8               32768 32768

Video mixer:

feature name                    sup
------------------------------------
DEINTERLACE_TEMPORAL             y
DEINTERLACE_TEMPORAL_SPATIAL     y
INVERSE_TELECINE                 y
NOISE_REDUCTION                  y
SHARPNESS                        y
LUMA_KEY                         y
HIGH QUALITY SCALING - L1        y
HIGH QUALITY SCALING - L2        -
HIGH QUALITY SCALING - L3        -
HIGH QUALITY SCALING - L4        -
HIGH QUALITY SCALING - L5        -
HIGH QUALITY SCALING - L6        -
HIGH QUALITY SCALING - L7        -
HIGH QUALITY SCALING - L8        -
HIGH QUALITY SCALING - L9        -

parameter name                  sup      min      max
-----------------------------------------------------
VIDEO_SURFACE_WIDTH              y         1     8192
VIDEO_SURFACE_HEIGHT             y         1     8192
CHROMA_TYPE                      y
LAYERS                           y         0        4

attribute name                  sup      min      max
-----------------------------------------------------
BACKGROUND_COLOR                 y
CSC_MATRIX                       y
NOISE_REDUCTION_LEVEL            y      0.00     1.00
SHARPNESS_LEVEL                  y     -1.00     1.00
LUMA_KEY_MIN_LUMA                y
LUMA_KEY_MAX_LUMA                y
```

GStreamer:

```
GStreamer version 1.24.8
```

FFmpeg:

```
ffmpeg version 7.1
```

### H.266/VVC Nvidia
#### Test suite: JVET-VVC_draft6

`./fluster.py run -d FFmpeg-H.266 VVCSoftware_VTM-H266 VVdeC-H266 -ts JVET-VVC_draft6 -ss`

|Test|FFmpeg-H.266|VVCSoftware_VTM-H266|VVdeC-H266|
|-|-|-|-|
|10b400_A_Bytedance_2|✔️|✔️|✔️|
|10b400_B_Bytedance_2|✔️|⌛|✔️|
|10b422_A_Sony_4|✔️|✔️|❌|
|10b422_B_Sony_4|✔️|✔️|❌|
|10b422_C_Sony_4|✔️|✔️|❌|
|10b422_D_Sony_4|✔️|✔️|❌|
|10b422_E_Sony_4|✔️|✔️|❌|
|10b422_F_Sony_4|✔️|✔️|❌|
|10b422_G_Sony_4|☠|✔️|☠|
|10b422_H_Sony_4|☠|✔️|☠|
|10b422_I_Sony_4|❌|✔️|☠|
|10b422_J_Sony_4|❌|✔️|☠|
|10b422_K_Sony_4|❌|✔️|☠|
|10b422_L_Sony_4|❌|✔️|☠|
|10b444_A_Kwai_3|✔️|✔️|✔️|
|10b444_B_Kwai_3|⌛|⌛|✔️|
|8b400_A_Bytedance_2|✔️|✔️|✔️|
|8b400_B_Bytedance_2|✔️|✔️|✔️|
|8b420_A_Bytedance_2|✔️|✔️|✔️|
|8b420_B_Bytedance_2|✔️|✔️|✔️|
|8b422_A_Sony_4|✔️|✔️|❌|
|8b422_B_Sony_4|✔️|✔️|❌|
|8b422_C_Sony_4|✔️|✔️|❌|
|8b422_D_Sony_4|✔️|✔️|❌|
|8b422_E_Sony_4|✔️|✔️|❌|
|8b422_F_Sony_4|✔️|✔️|❌|
|8b422_G_Sony_4|☠|✔️|☠|
|8b422_H_Sony_4|☠|✔️|☠|
|8b422_I_Sony_4|❌|✔️|☠|
|8b422_J_Sony_4|❌|✔️|☠|
|8b422_K_Sony_4|❌|✔️|☠|
|8b422_L_Sony_4|❌|✔️|☠|
|8b444_A_Kwai_2|❌|✔️|☠|
|8b444_B_Kwai_2|☠|⌛|☠|
|ACT_A_Kwai_3|❌|✔️|☠|
|ACT_B_Kwai_3|☠|✔️|☠|
|ACTPIC_A_Huawei_3|✔️|✔️|✔️|
|ACTPIC_B_Huawei_3|✔️|✔️|✔️|
|ACTPIC_C_Huawei_3|✔️|✔️|✔️|
|AFF_A_HUAWEI_2|✔️|✔️|✔️|
|AFF_B_HUAWEI_2|✔️|✔️|✔️|
|ALF_A_Huawei_3|✔️|✔️|✔️|
|ALF_B_Huawei_3|✔️|✔️|✔️|
|ALF_C_KDDI_3|✔️|✔️|✔️|
|ALF_D_Qualcomm_2|✔️|✔️|✔️|
|AMVR_A_HHI_3|✔️|✔️|✔️|
|AMVR_B_HHI_3|✔️|✔️|✔️|
|APSALF_A_Qualcomm_2|✔️|✔️|✔️|
|APSLMCS_A_Dolby_3|✔️|⌛|✔️|
|APSLMCS_B_Dolby_3|✔️|⌛|✔️|
|APSLMCS_C_Dolby_2|✔️|⌛|✔️|
|APSLMCS_D_Dolby_1|✔️|✔️|✔️|
|APSLMCS_E_Dolby_1|✔️|✔️|✔️|
|APSMULT_A_MediaTek_4|✔️|✔️|✔️|
|APSMULT_B_MediaTek_4|✔️|✔️|✔️|
|AUD_A_Broadcom_3|✔️|✔️|✔️|
|BCW_A_MediaTek_4|✔️|✔️|✔️|
|BDOF_A_MediaTek_4|✔️|✔️|✔️|
|BDPCM_A_Orange_2|✔️|✔️|✔️|
|BOUNDARY_A_Huawei_3|❌|✔️|✔️|
|BUMP_A_LGE_2|✔️|✔️|✔️|
|BUMP_B_LGE_2|✔️|✔️|✔️|
|BUMP_C_LGE_2|✔️|✔️|✔️|
|CCALF_A_Sharp_3|✔️|✔️|✔️|
|CCALF_B_Sharp_3|✔️|✔️|✔️|
|CCALF_C_Sharp_3|✔️|✔️|✔️|
|CCALF_D_Sharp_3|✔️|✔️|✔️|
|CCLM_A_KDDI_2|✔️|✔️|✔️|
|CIIP_A_MediaTek_4|✔️|✔️|✔️|
|CodingToolsSets_A_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_B_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_C_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_D_Tencent_2|✔️|✔️|✔️|
|CodingToolsSets_E_Tencent_1|✔️|✔️|✔️|
|CROP_A_Panasonic_3|✔️|✔️|✔️|
|CROP_B_Panasonic_4|✔️|✔️|✔️|
|CST_A_MediaTek_4|✔️|✔️|✔️|
|CTU_A_MediaTek_4|✔️|✔️|✔️|
|CTU_B_MediaTek_4|✔️|✔️|✔️|
|CTU_C_MediaTek_4|✔️|✔️|✔️|
|CUBEMAP_A_MediaTek_3|✔️|✔️|✔️|
|CUBEMAP_B_MediaTek_3|✔️|✔️|✔️|
|CUBEMAP_C_MediaTek_3|⌛|⌛|✔️|
|DCI_A_Tencent_3|✔️|✔️|✔️|
|DCI_B_Tencent_3|✔️|✔️|✔️|
|DEBLOCKING_A_Sharp_3|✔️|✔️|✔️|
|DEBLOCKING_B_Sharp_2|✔️|✔️|✔️|
|DEBLOCKING_C_Huawei_3|✔️|✔️|✔️|
|DEBLOCKING_E_Ericsson_3|✔️|✔️|✔️|
|DEBLOCKING_F_Ericsson_2|✔️|✔️|✔️|
|DMVR_A_Huawei_3|✔️|✔️|✔️|
|DMVR_B_KDDI_4|✔️|✔️|✔️|
|DPB_A_Sharplabs_2|✔️|✔️|✔️|
|DPB_B_Sharplabs_2|✔️|✔️|✔️|
|DQ_A_HHI_3|✔️|✔️|✔️|
|DQ_B_HHI_3|⌛|⌛|⌛|
|ENT444HIGHTIER_A_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_B_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_C_Sony_3|✔️|✔️|✔️|
|ENT444HIGHTIER_D_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_A_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_B_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_C_Sony_3|✔️|✔️|✔️|
|ENT444MAINTIER_D_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_A_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_B_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_C_Sony_3|✔️|✔️|✔️|
|ENTHIGHTIER_D_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_A_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_B_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_C_Sony_3|✔️|✔️|✔️|
|ENTMAINTIER_D_Sony_3|✔️|✔️|✔️|
|ENTROPY_A_Chipsnmedia_2|⌛|⌛|⌛|
|ENTROPY_B_Sharp_2|✔️|✔️|✔️|
|ENTROPY_C_Qualcomm_1|✔️|✔️|✔️|
|ERP_A_MediaTek_3|✔️|✔️|✔️|
|FIELD_A_Panasonic_4|❌|✔️|✔️|
|FIELD_B_Panasonic_2|❌|✔️|✔️|
|FILLER_A_Bytedance_1|✔️|✔️|✔️|
|GDR_A_ERICSSON_2|✔️|✔️|✔️|
|GDR_B_NOKIA_2|✔️|✔️|✔️|
|GDR_C_NOKIA_2|✔️|✔️|✔️|
|GDR_D_ERICSSON_1|❌|☠|✔️|
|GPM_A_Alibaba_3|✔️|✔️|✔️|
|GPM_B_Alibaba_1|✔️|✔️|✔️|
|HLG_A_NHK_4|⌛|⌛|✔️|
|HLG_B_NHK_4|☠|⌛|⌛|
|HRD_A_Fujitsu_3|✔️|✔️|✔️|
|HRD_B_Fujitsu_2|✔️|☠|✔️|
|IBC_A_Tencent_2|✔️|✔️|✔️|
|IBC_B_Tencent_2|✔️|✔️|✔️|
|IBC_C_Tencent_2|✔️|✔️|✔️|
|IBC_D_Tencent_2|✔️|✔️|✔️|
|ILRPL_A_Huawei_2|❌|☠|☠|
|IP_A_Huawei_2|✔️|✔️|✔️|
|IP_B_Nokia_1|✔️|✔️|✔️|
|ISP_A_HHI_3|✔️|✔️|✔️|
|ISP_B_HHI_3|⌛|⌛|✔️|
|JCCR_A_Nokia_2|✔️|✔️|✔️|
|JCCR_B_Nokia_2|✔️|✔️|✔️|
|JCCR_C_HHI_3|✔️|✔️|✔️|
|JCCR_D_HHI_3|⌛|⌛|⌛|
|JCCR_E_Nokia_1|✔️|✔️|✔️|
|JCCR_F_Nokia_1|✔️|✔️|✔️|
|LFNST_A_LGE_4|✔️|✔️|✔️|
|LFNST_B_LGE_4|✔️|✔️|✔️|
|LFNST_C_HHI_3|✔️|✔️|✔️|
|LFNST_D_HHI_3|⌛|⌛|⌛|
|LMCS_A_Dolby_3|✔️|✔️|✔️|
|LMCS_B_Dolby_2|✔️|⌛|✔️|
|LMCS_C_Dolby_1|✔️|✔️|✔️|
|LOSSLESS_A_HHI_3|✔️|✔️|✔️|
|LOSSLESS_B_HHI_3|✔️|✔️|✔️|
|LTRP_A_ERICSSON_3|✔️|✔️|✔️|
|MERGE_A_Qualcomm_2|✔️|✔️|✔️|
|MERGE_B_Qualcomm_2|✔️|✔️|✔️|
|MERGE_C_Qualcomm_2|✔️|✔️|✔️|
|MERGE_D_Qualcomm_2|✔️|✔️|✔️|
|MERGE_E_Qualcomm_2|✔️|✔️|✔️|
|MERGE_F_Qualcomm_2|⌛|⌛|✔️|
|MERGE_G_Qualcomm_2|⌛|⌛|✔️|
|MERGE_H_Qualcomm_2|⌛|⌛|✔️|
|MERGE_I_Qualcomm_2|⌛|⌛|✔️|
|MERGE_J_Qualcomm_2|⌛|⌛|✔️|
|MIP_A_HHI_3|✔️|✔️|✔️|
|MIP_B_HHI_3|✔️|✔️|✔️|
|MMVD_A_SAMSUNG_3|⌛|⌛|✔️|
|MNUT_A_Nokia_3|☠|✔️|✔️|
|MNUT_B_Nokia_2|☠|✔️|✔️|
|MPM_A_LGE_3|⌛|⌛|✔️|
|MRLP_A_HHI_2|✔️|✔️|✔️|
|MRLP_B_HHI_2|✔️|✔️|✔️|
|MTS_A_LGE_4|✔️|✔️|✔️|
|MTS_B_LGE_4|✔️|✔️|✔️|
|MTS_LFNST_A_LGE_4|✔️|✔️|✔️|
|MTS_LFNST_B_LGE_4|✔️|✔️|✔️|
|MVCOMP_A_Sharp_2|✔️|✔️|✔️|
|OLS_A_Tencent_4|❌|☠|☠|
|OLS_B_Tencent_4|❌|☠|☠|
|OLS_C_Tencent_4|❌|☠|☠|
|OPI_A_Nokia_1|✔️|✔️|✔️|
|OPI_B_Nokia_2|❌|☠|☠|
|PALETTE_A_Alibaba_2|❌|✔️|☠|
|PALETTE_B_Alibaba_2|☠|✔️|☠|
|PALETTE_C_Alibaba_2|☠|✔️|☠|
|PALETTE_D_Alibaba_2|☠|✔️|☠|
|PALETTE_E_Alibaba_2|❌|✔️|☠|
|PDPC_A_Qualcomm_3|✔️|✔️|✔️|
|PDPC_B_Qualcomm_3|✔️|✔️|✔️|
|PDPC_C_Qualcomm_2|✔️|✔️|✔️|
|PHSH_B_Sharp_1|✔️|✔️|✔️|
|PMERGE_A_MediaTek_1|✔️|✔️|✔️|
|PMERGE_B_MediaTek_1|✔️|✔️|✔️|
|PMERGE_C_MediaTek_1|✔️|✔️|✔️|
|PMERGE_D_MediaTek_1|✔️|✔️|✔️|
|PMERGE_E_MediaTek_1|✔️|✔️|✔️|
|POC_A_Nokia_1|✔️|✔️|✔️|
|POUT_A_Sharplabs_2|✔️|✔️|✔️|
|PPS_A_Bytedance_1|⌛|⌛|✔️|
|PPS_B_Bytedance_1|✔️|✔️|✔️|
|PPS_C_Bytedance_1|✔️|✔️|✔️|
|PQ_A_Dolby_1|✔️|⌛|✔️|
|PROF_A_Interdigital_3|✔️|✔️|✔️|
|PROF_B_Interdigital_3|✔️|✔️|✔️|
|PSEXT_A_Nokia_2|✔️|✔️|✔️|
|PSEXT_B_Nokia_2|✔️|✔️|✔️|
|QTBTT_A_MediaTek_4|✔️|✔️|✔️|
|QUANT_A_Huawei_2|✔️|✔️|✔️|
|QUANT_B_Huawei_2|✔️|✔️|✔️|
|QUANT_C_Huawei_2|✔️|✔️|✔️|
|QUANT_D_Huawei_4|✔️|✔️|✔️|
|QUANT_E_Interdigital_1|✔️|✔️|✔️|
|RAP_A_HHI_1|✔️|✔️|✔️|
|RAP_B_HHI_1|✔️|✔️|✔️|
|RAP_C_HHI_1|✔️|✔️|✔️|
|RAP_D_HHI_1|✔️|✔️|✔️|
|RPL_A_ERICSSON_2|✔️|✔️|✔️|
|RPR_A_Alibaba_4|❌|✔️|✔️|
|RPR_B_Alibaba_3|❌|✔️|✔️|
|RPR_C_Alibaba_3|❌|✔️|✔️|
|RPR_D_Qualcomm_1|❌|✔️|✔️|
|SAO_A_SAMSUNG_3|✔️|✔️|✔️|
|SAO_B_SAMSUNG_3|✔️|✔️|✔️|
|SAO_C_SAMSUNG_3|✔️|✔️|✔️|
|SBT_A_HUAWEI_2|✔️|✔️|✔️|
|SbTMVP_A_Bytedance_3|✔️|✔️|✔️|
|SbTMVP_B_Bytedance_3|✔️|✔️|✔️|
|SCALING_A_InterDigital_1|✔️|✔️|✔️|
|SCALING_B_InterDigital_1|✔️|✔️|✔️|
|SCALING_C_InterDigital_1|✔️|✔️|✔️|
|SDH_A_Dolby_2|✔️|✔️|✔️|
|SLICES_A_HUAWEI_2|✔️|✔️|✔️|
|SMVD_A_HUAWEI_2|✔️|✔️|✔️|
|SPATSCAL444_A_Qualcomm_2|❌|☠|☠|
|SPATSCAL_A_Qualcomm_3|❌|☠|☠|
|SPS_A_Bytedance_1|⌛|⌛|✔️|
|SPS_B_Bytedance_1|✔️|✔️|✔️|
|SPS_C_Bytedance_1|✔️|✔️|✔️|
|STILL444_A_KDDI_1|✔️|✔️|✔️|
|STILL444_B_ERICSSON_1|✔️|✔️|✔️|
|STILL_A_KDDI_1|✔️|✔️|✔️|
|STILL_B_ERICSSON_1|✔️|✔️|✔️|
|SUBPIC_A_HUAWEI_3|✔️|✔️|✔️|
|SUBPIC_B_HUAWEI_3|✔️|✔️|✔️|
|SUBPIC_C_ERICSSON_1|☠|✔️|✔️|
|SUBPIC_D_ERICSSON_1|☠|✔️|✔️|
|SUBPIC_E_MediaTek_1|✔️|✔️|✔️|
|SUFAPS_A_HHI_1|✔️|✔️|✔️|
|TEMPSCAL_A_Panasonic_4|✔️|⌛|✔️|
|TEMPSCAL_B_Panasonic_5|⌛|⌛|✔️|
|TEMPSCAL_C_Panasonic_3|✔️|⌛|✔️|
|TILE_A_Nokia_2|✔️|✔️|✔️|
|TILE_B_Nokia_2|✔️|✔️|✔️|
|TILE_C_Nokia_2|✔️|✔️|✔️|
|TILE_D_Nokia_2|✔️|✔️|✔️|
|TILE_E_Nokia_2|✔️|✔️|✔️|
|TILE_F_Nokia_2|✔️|✔️|✔️|
|TILE_G_Nokia_2|✔️|✔️|✔️|
|TMVP_A_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_B_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_C_Chipsnmedia_3|✔️|✔️|✔️|
|TMVP_D_Chipsnmedia_3|✔️|✔️|✔️|
|TRANS_A_Chipsnmedia_2|✔️|✔️|✔️|
|TRANS_B_Chipsnmedia_2|✔️|✔️|✔️|
|TRANS_C_Chipsnmedia_4|✔️|✔️|✔️|
|TRANS_D_Chipsnmedia_4|✔️|✔️|✔️|
|TREE_A_HHI_3|✔️|⌛|✔️|
|TREE_B_HHI_3|⌛|⌛|✔️|
|TREE_C_HHI_3|⌛|⌛|✔️|
|VIRTUAL_A_MediaTek_3|✔️|✔️|✔️|
|VIRTUAL_B_MediaTek_3|✔️|✔️|✔️|
|VPS_A_INTEL_3|❌|☠|☠|
|VPS_B_ERICSSON_1|❌|☠|☠|
|VPS_C_ERICSSON_1|☠|☠|☠|
|WP_A_InterDigital_3|✔️|✔️|✔️|
|WP_B_InterDigital_3|✔️|✔️|✔️|
|WPP_A_Sharp_3|✔️|✔️|✔️|
|WPP_B_Sharp_2|✔️|✔️|✔️|
|WRAP_A_InterDigital_4|✔️|✔️|✔️|
|WRAP_B_InterDigital_4|✔️|✔️|✔️|
|WRAP_C_InterDigital_4|✔️|✔️|✔️|
|WRAP_D_InterDigital_4|✔️|✔️|✔️|
|-|-|-|-|
|TOTAL|218/282|239/282|234/282|


### H.265/HEVC Nvidia
#### Test suite: JCT-VC-HEVC_V1

`./fluster.py run -d FFmpeg-H.265 FFmpeg-H.265-VDPAU GStreamer-H.265-NVDEC-Gst1.0 JCT-VT-H.265 -ts JCT-VC-HEVC_V1 -s`

|Test|FFmpeg-H.265|FFmpeg-H.265-VDPAU|GStreamer-H.265-NVDEC-Gst1.0|JCT-VT-H.265|
|-|-|-|-|-|
|AMP_A_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_B_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_D_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_E_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_F_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMVP_A_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_B_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_C_Samsung_7|✔️|✔️|✔️|✔️|
|BUMPING_A_ericsson_1|✔️|✔️|✔️|✔️|
|CAINIT_A_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_B_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_C_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_D_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_E_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_F_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_G_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_H_SHARP_3|✔️|✔️|✔️|✔️|
|CIP_A_Panasonic_3|✔️|✔️|✔️|✔️|
|cip_B_NEC_3|✔️|✔️|✔️|✔️|
|CIP_C_Panasonic_2|✔️|✔️|✔️|✔️|
|CONFWIN_A_Sony_1|✔️|✔️|❌|✔️|
|DBLK_A_MAIN10_VIXS_4|✔️|✔️|✔️|✔️|
|DBLK_A_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_B_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_C_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_D_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_E_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_F_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_G_VIXS_2|✔️|✔️|✔️|✔️|
|DELTAQP_A_BRCM_4|✔️|✔️|✔️|✔️|
|DELTAQP_B_SONY_3|✔️|✔️|✔️|✔️|
|DELTAQP_C_SONY_3|✔️|✔️|✔️|✔️|
|DSLICE_A_HHI_5|✔️|✔️|✔️|✔️|
|DSLICE_B_HHI_5|✔️|✔️|✔️|✔️|
|DSLICE_C_HHI_5|✔️|✔️|✔️|✔️|
|ENTP_A_QUALCOMM_1|✔️|✔️|✔️|✔️|
|ENTP_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|ENTP_C_Qualcomm_1|✔️|✔️|✔️|✔️|
|EXT_A_ericsson_4|✔️|✔️|✔️|✔️|
|FILLER_A_Sony_1|✔️|✔️|✔️|✔️|
|HRD_A_Fujitsu_3|✔️|✔️|✔️|✔️|
|INITQP_A_Sony_1|✔️|✔️|✔️|✔️|
|INITQP_B_Main10_Sony_1|✔️|✔️|✔️|✔️|
|ipcm_A_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_B_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_C_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_D_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_E_NEC_2|✔️|✔️|✔️|✔️|
|IPRED_A_docomo_2|✔️|✔️|✔️|✔️|
|IPRED_B_Nokia_3|✔️|☠|☠|✔️|
|IPRED_C_Mitsubishi_3|✔️|✔️|✔️|✔️|
|LS_A_Orange_2|✔️|✔️|✔️|✔️|
|LS_B_Orange_4|✔️|✔️|✔️|✔️|
|LTRPSPS_A_Qualcomm_1|✔️|❌|✔️|✔️|
|MAXBINS_A_TI_5|✔️|✔️|✔️|✔️|
|MAXBINS_B_TI_5|✔️|✔️|✔️|✔️|
|MAXBINS_C_TI_5|✔️|✔️|✔️|✔️|
|MERGE_A_TI_3|✔️|✔️|✔️|✔️|
|MERGE_B_TI_3|✔️|✔️|✔️|✔️|
|MERGE_C_TI_3|✔️|✔️|✔️|✔️|
|MERGE_D_TI_3|✔️|✔️|✔️|✔️|
|MERGE_E_TI_3|✔️|✔️|✔️|✔️|
|MERGE_F_MTK_4|✔️|✔️|✔️|✔️|
|MERGE_G_HHI_4|✔️|✔️|✔️|✔️|
|MVCLIP_A_qualcomm_3|✔️|✔️|✔️|✔️|
|MVDL1ZERO_A_docomo_4|✔️|✔️|✔️|✔️|
|MVEDGE_A_qualcomm_3|✔️|✔️|✔️|✔️|
|NoOutPrior_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|NoOutPrior_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|NUT_A_ericsson_5|✔️|✔️|✔️|✔️|
|OPFLAG_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|OPFLAG_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|OPFLAG_C_Qualcomm_1|✔️|✔️|✔️|✔️|
|PICSIZE_A_Bossen_1|✔️|☠|☠|✔️|
|PICSIZE_B_Bossen_1|✔️|☠|☠|✔️|
|PICSIZE_C_Bossen_1|✔️|✔️|✔️|✔️|
|PICSIZE_D_Bossen_1|✔️|✔️|✔️|✔️|
|PMERGE_A_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_B_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_C_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_D_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_E_TI_3|✔️|✔️|✔️|✔️|
|POC_A_Bossen_3|✔️|✔️|✔️|✔️|
|PPS_A_qualcomm_7|✔️|✔️|✔️|✔️|
|PS_B_VIDYO_3|✔️|✔️|✔️|✔️|
|RAP_A_docomo_6|✔️|✔️|✔️|✔️|
|RAP_B_Bossen_2|✔️|✔️|✔️|✔️|
|RPLM_A_qualcomm_4|✔️|✔️|✔️|✔️|
|RPLM_B_qualcomm_4|✔️|✔️|✔️|✔️|
|RPS_A_docomo_5|✔️|✔️|✔️|✔️|
|RPS_B_qualcomm_5|✔️|✔️|✔️|✔️|
|RPS_C_ericsson_5|✔️|✔️|✔️|✔️|
|RPS_D_ericsson_6|✔️|❌|✔️|✔️|
|RPS_E_qualcomm_5|✔️|❌|✔️|✔️|
|RPS_F_docomo_2|✔️|✔️|✔️|✔️|
|RQT_A_HHI_4|✔️|✔️|✔️|✔️|
|RQT_B_HHI_4|✔️|✔️|✔️|✔️|
|RQT_C_HHI_4|✔️|✔️|✔️|✔️|
|RQT_D_HHI_4|✔️|✔️|✔️|✔️|
|RQT_E_HHI_4|✔️|✔️|✔️|✔️|
|RQT_F_HHI_4|✔️|✔️|✔️|✔️|
|RQT_G_HHI_4|✔️|✔️|✔️|✔️|
|SAO_A_MediaTek_4|✔️|✔️|✔️|✔️|
|SAO_B_MediaTek_5|✔️|✔️|✔️|✔️|
|SAO_C_Samsung_5|✔️|✔️|✔️|✔️|
|SAO_D_Samsung_5|✔️|✔️|✔️|✔️|
|SAO_E_Canon_4|✔️|✔️|✔️|✔️|
|SAO_F_Canon_3|✔️|✔️|✔️|✔️|
|SAO_G_Canon_3|✔️|✔️|✔️|✔️|
|SAO_H_Parabola_1|✔️|✔️|✔️|✔️|
|SAODBLK_A_MainConcept_4|❌|✔️|✔️|✔️|
|SAODBLK_B_MainConcept_4|❌|✔️|✔️|✔️|
|SDH_A_Orange_4|✔️|✔️|✔️|✔️|
|SLICES_A_Rovi_3|✔️|✔️|✔️|✔️|
|SLIST_A_Sony_5|✔️|✔️|✔️|✔️|
|SLIST_B_Sony_9|✔️|✔️|✔️|✔️|
|SLIST_C_Sony_4|✔️|✔️|✔️|✔️|
|SLIST_D_Sony_9|✔️|✔️|✔️|✔️|
|SLPPLP_A_VIDYO_2|✔️|✔️|✔️|✔️|
|STRUCT_A_Samsung_7|✔️|✔️|✔️|✔️|
|STRUCT_B_Samsung_7|✔️|✔️|✔️|✔️|
|TILES_A_Cisco_2|✔️|✔️|✔️|✔️|
|TILES_B_Cisco_1|✔️|✔️|✔️|✔️|
|TMVP_A_MS_3|✔️|✔️|✔️|✔️|
|TSCL_A_VIDYO_5|✔️|✔️|✔️|✔️|
|TSCL_B_VIDYO_4|✔️|✔️|✔️|✔️|
|TSKIP_A_MS_3|✔️|✔️|✔️|✔️|
|TSUNEQBD_A_MAIN10_Technicolor_2|☠|☠|❌|✔️|
|TUSIZE_A_Samsung_1|✔️|✔️|✔️|✔️|
|VPSID_A_VIDYO_2|✔️|✔️|✔️|✔️|
|VPSSPSPPS_A_MainConcept_1|❌|❌|✔️|✔️|
|WP_A_MAIN10_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_A_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_B_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_MAIN10_B_Toshiba_3|✔️|✔️|✔️|✔️|
|WPP_A_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_A_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_B_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_B_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_C_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_C_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_D_ericsson_MAIN10_2|✔️|❌|☠|✔️|
|WPP_D_ericsson_MAIN_2|✔️|❌|☠|✔️|
|WPP_E_ericsson_MAIN10_2|✔️|✔️|☠|✔️|
|WPP_E_ericsson_MAIN_2|✔️|✔️|☠|✔️|
|WPP_F_ericsson_MAIN10_2|✔️|✔️|✔️|✔️|
|WPP_F_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|-|-|-|-|-|
|TOTAL|143/147|137/147|138/147|147/147|


### H.264/AVC Nvidia
#### Test suite: JVT-AVC_V1

`./fluster.py run -d FFmpeg-H.264 FFmpeg-H.264-VDPAU GStreamer-H.264-NVDEC-Gst1.0 JCT-VT-H.264 -ts JVT-AVC_V1 -s`

|Test|FFmpeg-H.264|FFmpeg-H.264-VDPAU|GStreamer-H.264-NVDEC-Gst1.0|JCT-VT-H.264|
|-|-|-|-|-|
|AUD_MW_E|✔️|✔️|✔️|✔️|
|BA1_FT_C|✔️|✔️|✔️|✔️|
|BA1_Sony_D|✔️|✔️|✔️|✔️|
|BA2_Sony_F|✔️|✔️|✔️|✔️|
|BA3_SVA_C|✔️|✔️|☠|✔️|
|BA_MW_D|✔️|✔️|✔️|✔️|
|BAMQ1_JVC_C|✔️|✔️|✔️|✔️|
|BAMQ2_JVC_C|✔️|✔️|✔️|✔️|
|BANM_MW_D|✔️|✔️|✔️|✔️|
|BASQP1_Sony_C|✔️|✔️|✔️|✔️|
|CABA1_Sony_D|✔️|✔️|✔️|✔️|
|CABA1_SVA_B|✔️|✔️|✔️|✔️|
|CABA2_Sony_E|✔️|✔️|✔️|✔️|
|CABA2_SVA_B|✔️|✔️|✔️|✔️|
|CABA3_Sony_C|✔️|✔️|✔️|✔️|
|CABA3_SVA_B|✔️|✔️|✔️|✔️|
|CABA3_TOSHIBA_E|✔️|✔️|✔️|✔️|
|cabac_mot_fld0_full|✔️|✔️|✔️|✔️|
|cabac_mot_frm0_full|✔️|✔️|✔️|✔️|
|cabac_mot_mbaff0_full|✔️|✔️|✔️|✔️|
|cabac_mot_picaff0_full|✔️|✔️|✔️|✔️|
|CABACI3_Sony_B|✔️|✔️|✔️|✔️|
|CABAST3_Sony_E|✔️|✔️|✔️|✔️|
|CABASTBR3_Sony_B|✔️|✔️|✔️|✔️|
|CABREF3_Sand_D|✔️|✔️|✔️|✔️|
|CACQP3_Sony_D|✔️|✔️|✔️|✔️|
|CAFI1_SVA_C|✔️|✔️|✔️|✔️|
|CAMA1_Sony_C|✔️|✔️|✔️|✔️|
|CAMA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|cama1_vtc_c|✔️|✔️|✔️|✔️|
|cama2_vtc_b|✔️|✔️|✔️|✔️|
|CAMA3_Sand_E|✔️|✔️|✔️|✔️|
|cama3_vtc_b|✔️|✔️|✔️|✔️|
|CAMACI3_Sony_C|✔️|✔️|✔️|✔️|
|CAMANL1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAMANL2_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAMANL3_Sand_E|✔️|✔️|✔️|✔️|
|CAMASL3_Sony_B|✔️|✔️|✔️|✔️|
|CAMP_MOT_MBAFF_L30|✔️|✔️|✔️|✔️|
|CAMP_MOT_MBAFF_L31|✔️|✔️|✔️|✔️|
|CANL1_Sony_E|✔️|✔️|✔️|✔️|
|CANL1_SVA_B|✔️|✔️|✔️|✔️|
|CANL1_TOSHIBA_G|✔️|✔️|✔️|✔️|
|CANL2_Sony_E|✔️|✔️|✔️|✔️|
|CANL2_SVA_B|✔️|✔️|✔️|✔️|
|CANL3_Sony_C|✔️|✔️|✔️|✔️|
|CANL3_SVA_B|✔️|✔️|✔️|✔️|
|CANL4_SVA_B|✔️|✔️|✔️|✔️|
|CANLMA2_Sony_C|✔️|✔️|✔️|✔️|
|CANLMA3_Sony_C|✔️|✔️|✔️|✔️|
|CAPA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CAPAMA3_Sand_F|✔️|✔️|✔️|✔️|
|CAPCM1_Sand_E|✔️|✔️|✔️|✔️|
|CAPCMNL1_Sand_E|✔️|✔️|✔️|✔️|
|CAPM3_Sony_D|✔️|✔️|✔️|✔️|
|CAQP1_Sony_B|✔️|✔️|✔️|✔️|
|cavlc_mot_fld0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_frm0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_mbaff0_full_B|✔️|✔️|✔️|✔️|
|cavlc_mot_picaff0_full_B|✔️|✔️|✔️|✔️|
|CAWP1_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CAWP5_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CI1_FT_B|✔️|✔️|✔️|✔️|
|CI_MW_D|✔️|✔️|✔️|✔️|
|CVBS3_Sony_C|✔️|✔️|✔️|✔️|
|CVCANLMA2_Sony_C|✔️|✔️|✔️|✔️|
|CVFC1_Sony_C|✔️|✔️|❌|✔️|
|CVFI1_Sony_D|✔️|✔️|✔️|✔️|
|CVFI1_SVA_C|✔️|✔️|✔️|✔️|
|CVFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVFI2_SVA_C|✔️|✔️|✔️|✔️|
|CVMA1_Sony_D|✔️|✔️|✔️|✔️|
|CVMA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL2_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMAPAQP3_Sony_E|✔️|✔️|✔️|✔️|
|CVMAQP2_Sony_G|✔️|✔️|✔️|✔️|
|CVMAQP3_Sony_D|✔️|✔️|✔️|✔️|
|CVMP_MOT_FLD_L30_B|✔️|✔️|✔️|✔️|
|CVMP_MOT_FRM_L31_B|✔️|✔️|✔️|✔️|
|CVNLFI1_Sony_C|✔️|✔️|✔️|✔️|
|CVNLFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVPA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVPCMNL1_SVA_C|✔️|✔️|✔️|✔️|
|CVPCMNL2_SVA_C|✔️|✔️|✔️|✔️|
|CVSE2_Sony_B|✔️|✔️|✔️|✔️|
|CVSE3_Sony_H|✔️|✔️|✔️|✔️|
|CVSEFDFT3_Sony_E|✔️|✔️|✔️|✔️|
|CVWP1_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP2_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP3_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP5_TOSHIBA_E|✔️|✔️|✔️|✔️|
|FI1_Sony_E|✔️|✔️|✔️|✔️|
|FM1_BT_B|☠|☠|❌|✔️|
|FM1_FT_E|❌|❌|❌|✔️|
|FM2_SVA_C|☠|☠|☠|✔️|
|HCBP1_HHI_A|✔️|✔️|✔️|✔️|
|HCBP2_HHI_A|✔️|✔️|✔️|✔️|
|HCMP1_HHI_A|✔️|✔️|✔️|✔️|
|LS_SVA_D|✔️|✔️|✔️|✔️|
|MIDR_MW_D|✔️|✔️|✔️|✔️|
|MPS_MW_A|✔️|✔️|✔️|✔️|
|MR1_BT_A|✔️|✔️|✔️|✔️|
|MR1_MW_A|✔️|✔️|✔️|✔️|
|MR2_MW_A|✔️|✔️|✔️|✔️|
|MR2_TANDBERG_E|✔️|✔️|✔️|✔️|
|MR3_TANDBERG_B|✔️|❌|✔️|✔️|
|MR4_TANDBERG_C|✔️|❌|✔️|✔️|
|MR5_TANDBERG_C|✔️|❌|✔️|✔️|
|MR6_BT_B|✔️|❌|☠|✔️|
|MR7_BT_B|✔️|✔️|☠|✔️|
|MR8_BT_B|✔️|❌|☠|✔️|
|MR9_BT_B|✔️|✔️|✔️|✔️|
|MV1_BRCM_D|✔️|✔️|✔️|✔️|
|NL1_Sony_D|✔️|✔️|✔️|✔️|
|NL2_Sony_H|✔️|✔️|✔️|✔️|
|NL3_SVA_E|✔️|✔️|✔️|✔️|
|NLMQ1_JVC_C|✔️|✔️|✔️|✔️|
|NLMQ2_JVC_C|✔️|✔️|✔️|✔️|
|NRF_MW_E|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_1_B|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_2_B|✔️|✔️|✔️|✔️|
|Sharp_MP_Field_3_B|✔️|✔️|✔️|✔️|
|Sharp_MP_PAFF_1r2|✔️|✔️|✔️|✔️|
|Sharp_MP_PAFF_2r|✔️|✔️|✔️|✔️|
|SL1_SVA_B|✔️|✔️|✔️|✔️|
|SP1_BT_A|❌|❌|☠|❌|
|sp2_bt_b|❌|❌|☠|❌|
|SVA_BA1_B|✔️|✔️|✔️|✔️|
|SVA_BA2_D|✔️|✔️|✔️|✔️|
|SVA_Base_B|✔️|✔️|✔️|✔️|
|SVA_CL1_E|✔️|✔️|✔️|✔️|
|SVA_FM1_E|✔️|✔️|✔️|✔️|
|SVA_NL1_B|✔️|✔️|✔️|✔️|
|SVA_NL2_E|✔️|✔️|✔️|✔️|
|-|-|-|-|-|
|TOTAL|130/135|125/135|125/135|133/135|
