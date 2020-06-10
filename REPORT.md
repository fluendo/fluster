# Report

## Table of Contents

- [Report](#report)
  - [Table of Contents](#table-of-contents)
  - [Environment](#environment)
  - [H.265/HEVC](#h265hevc)
  - [H.264/AVC](#h264avc)

## Environment

Lenovo Thinkpad T490 using i965 driver:

```
ibva info: VA-API version 1.7.0
libva info: User environment variable requested driver 'i965'
libva info: Trying to open /usr/lib/x86_64-linux-gnu/dri/i965_drv_video.so
libva info: Found init function __vaDriverInit_1_6
libva info: va_openDriver() returns 0
vainfo: VA-API version: 1.7 (libva 2.6.0)
vainfo: Driver version: Intel i965 driver for Intel(R) Coffee Lake - 2.4.0
vainfo: Supported profile and entrypoints
      VAProfileMPEG2Simple            : VAEntrypointVLD
      VAProfileMPEG2Simple            : VAEntrypointEncSlice
      VAProfileMPEG2Main              : VAEntrypointVLD
      VAProfileMPEG2Main              : VAEntrypointEncSlice
      VAProfileH264ConstrainedBaseline: VAEntrypointVLD
      VAProfileH264ConstrainedBaseline: VAEntrypointEncSlice
      VAProfileH264ConstrainedBaseline: VAEntrypointEncSliceLP
      VAProfileH264Main               : VAEntrypointVLD
      VAProfileH264Main               : VAEntrypointEncSlice
      VAProfileH264Main               : VAEntrypointEncSliceLP
      VAProfileH264High               : VAEntrypointVLD
      VAProfileH264High               : VAEntrypointEncSlice
      VAProfileH264High               : VAEntrypointEncSliceLP
      VAProfileH264MultiviewHigh      : VAEntrypointVLD
      VAProfileH264MultiviewHigh      : VAEntrypointEncSlice
      VAProfileH264StereoHigh         : VAEntrypointVLD
      VAProfileH264StereoHigh         : VAEntrypointEncSlice
      VAProfileVC1Simple              : VAEntrypointVLD
      VAProfileVC1Main                : VAEntrypointVLD
      VAProfileVC1Advanced            : VAEntrypointVLD
      VAProfileNone                   : VAEntrypointVideoProc
      VAProfileJPEGBaseline           : VAEntrypointVLD
      VAProfileJPEGBaseline           : VAEntrypointEncPicture
      VAProfileVP8Version0_3          : VAEntrypointVLD
      VAProfileVP8Version0_3          : VAEntrypointEncSlice
      VAProfileHEVCMain               : VAEntrypointVLD
      VAProfileHEVCMain               : VAEntrypointEncSlice
      VAProfileHEVCMain10             : VAEntrypointVLD
      VAProfileHEVCMain10             : VAEntrypointEncSlice
      VAProfileVP9Profile0            : VAEntrypointVLD
      VAProfileVP9Profile0            : VAEntrypointEncSlice
      VAProfileVP9Profile2            : VAEntrypointVLD
```

## H.265/HEVC

`./fluster.py run -d JCT-VT-H.265 GStreamer-H.265-VAAPI-Gst1.0 FFmpeg-H.265-VAAPI FFmpeg-H.265 -ts JCT-VC-HEVC_V1 -s`


|Test|JCT-VT-H.265|GStreamer-H.265-VAAPI-Gst1.0|FFmpeg-H.265-VAAPI|FFmpeg-H.265|
|-|-|-|-|-|
|AMP_A_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_B_Samsung_7|✔️|✔️|✔️|✔️|
|AMP_D_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_E_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMP_F_Hisilicon_3|✔️|✔️|✔️|✔️|
|AMVP_A_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_B_MTK_4|✔️|✔️|✔️|✔️|
|AMVP_C_Samsung_7|✔️|✔️|✔️|✔️|
|BUMPING_A_ericsson_1|✔️|✔️|❌|❌|
|CAINIT_A_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_B_SHARP_4|✔️|✔️|✔️|✔️|
|CAINIT_C_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_D_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_E_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_F_SHARP_3|✔️|✔️|✔️|✔️|
|CAINIT_G_SHARP_3|✔️|❌|✔️|✔️|
|CAINIT_H_SHARP_3|✔️|❌|✔️|✔️|
|CIP_A_Panasonic_3|✔️|✔️|✔️|✔️|
|cip_B_NEC_3|✔️|✔️|✔️|✔️|
|CIP_C_Panasonic_2|✔️|✔️|✔️|✔️|
|CONFWIN_A_Sony_1|✔️|❌|❌|❌|
|DBLK_A_MAIN10_VIXS_4|✔️|❌|✔️|✔️|
|DBLK_A_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_B_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_C_SONY_3|✔️|✔️|✔️|✔️|
|DBLK_D_VIXS_2|✔️|❌|✔️|✔️|
|DBLK_E_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_F_VIXS_2|✔️|✔️|✔️|✔️|
|DBLK_G_VIXS_2|✔️|✔️|✔️|✔️|
|DELTAQP_A_BRCM_4|✔️|✔️|❌|❌|
|DELTAQP_B_SONY_3|✔️|✔️|✔️|✔️|
|DELTAQP_C_SONY_3|✔️|✔️|✔️|✔️|
|DSLICE_A_HHI_5|✔️|❌|✔️|✔️|
|DSLICE_B_HHI_5|✔️|❌|✔️|✔️|
|DSLICE_C_HHI_5|✔️|❌|✔️|✔️|
|ENTP_A_QUALCOMM_1|✔️|✔️|✔️|✔️|
|ENTP_B_Qualcomm_1|✔️|✔️|✔️|✔️|
|ENTP_C_Qualcomm_1|✔️|✔️|✔️|✔️|
|EXT_A_ericsson_4|✔️|✔️|✔️|✔️|
|FILLER_A_Sony_1|✔️|✔️|✔️|✔️|
|HRD_A_Fujitsu_3|✔️|✔️|✔️|✔️|
|INITQP_A_Sony_1|✔️|✔️|✔️|✔️|
|INITQP_B_Main10_Sony_1|✔️|❌|✔️|✔️|
|ipcm_A_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_B_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_C_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_D_NEC_3|✔️|✔️|✔️|✔️|
|ipcm_E_NEC_2|✔️|✔️|✔️|✔️|
|IPRED_A_docomo_2|✔️|✔️|✔️|✔️|
|IPRED_B_Nokia_3|✔️|✔️|✔️|✔️|
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
|NoOutPrior_A_Qualcomm_1|✔️|✔️|❌|❌|
|NoOutPrior_B_Qualcomm_1|✔️|✔️|❌|❌|
|NUT_A_ericsson_5|✔️|✔️|❌|❌|
|OPFLAG_A_Qualcomm_1|✔️|✔️|✔️|✔️|
|OPFLAG_B_Qualcomm_1|✔️|✔️|❌|❌|
|OPFLAG_C_Qualcomm_1|✔️|✔️|❌|❌|
|PICSIZE_A_Bossen_1|✔️|❌|✔️|✔️|
|PICSIZE_B_Bossen_1|✔️|❌|✔️|✔️|
|PICSIZE_C_Bossen_1|✔️|❌|✔️|✔️|
|PICSIZE_D_Bossen_1|✔️|❌|✔️|✔️|
|PMERGE_A_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_B_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_C_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_D_TI_3|✔️|✔️|✔️|✔️|
|PMERGE_E_TI_3|✔️|✔️|✔️|✔️|
|POC_A_Bossen_3|✔️|✔️|✔️|✔️|
|PPS_A_qualcomm_7|✔️|✔️|✔️|✔️|
|PS_B_VIDYO_3|✔️|✔️|✔️|✔️|
|RAP_A_docomo_6|✔️|✔️|✔️|✔️|
|RAP_B_Bossen_2|✔️|✔️|❌|❌|
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
|SAODBLK_A_MainConcept_4|✔️|✔️|✔️|❌|
|SAODBLK_B_MainConcept_4|✔️|✔️|✔️|❌|
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
|TSUNEQBD_A_MAIN10_Technicolor_2|✔️|❌|❌|❌|
|TUSIZE_A_Samsung_1|✔️|✔️|✔️|✔️|
|VPSID_A_VIDYO_2|✔️|✔️|✔️|✔️|
|VPSSPSPPS_A_MainConcept_1|✔️|❌|❌|❌|
|WP_A_MAIN10_Toshiba_3|✔️|❌|✔️|✔️|
|WP_A_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_B_Toshiba_3|✔️|✔️|✔️|✔️|
|WP_MAIN10_B_Toshiba_3|✔️|❌|✔️|✔️|
|WPP_A_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_A_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_B_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_B_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_C_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_C_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_D_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_D_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_E_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_E_ericsson_MAIN_2|✔️|✔️|✔️|✔️|
|WPP_F_ericsson_MAIN10_2|✔️|❌|✔️|✔️|
|WPP_F_ericsson_MAIN_2|✔️|✔️|✔️|✔️|


## H.264/AVC

`./fluster.py run -d JCT-VT-H.264 GStreamer-H.264-VAAPI-Gst1.0 FFmpeg-H.264-VAAPI FFmpeg-H.264 -ts JVT-AVC_V1 -s`

|Test|JCT-VT-H.264|GStreamer-H.264-VAAPI-Gst1.0|FFmpeg-H.264-VAAPI|FFmpeg-H.264|
|-|-|-|-|-|
|AUD_MW_E|✔️|✔️|✔️|✔️|
|BA1_FT_C|✔️|✔️|✔️|✔️|
|BA1_Sony_D|✔️|✔️|✔️|✔️|
|BA2_Sony_F|✔️|✔️|✔️|✔️|
|BA3_SVA_C|✔️|✔️|✔️|✔️|
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
|CVFC1_Sony_C|✔️|❌|❌|❌|
|CVFI1_Sony_D|✔️|✔️|✔️|✔️|
|CVFI1_SVA_C|✔️|✔️|✔️|✔️|
|CVFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVFI2_SVA_C|✔️|✔️|✔️|✔️|
|CVMA1_Sony_D|✔️|✔️|✔️|✔️|
|CVMA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMANL2_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVMAPAQP3_Sony_E|✔️|✔️|❌|❌|
|CVMAQP2_Sony_G|✔️|✔️|✔️|✔️|
|CVMAQP3_Sony_D|✔️|✔️|✔️|✔️|
|CVMP_MOT_FLD_L30_B|✔️|✔️|✔️|✔️|
|CVMP_MOT_FRM_L31_B|✔️|✔️|✔️|✔️|
|CVNLFI1_Sony_C|✔️|✔️|✔️|✔️|
|CVNLFI2_Sony_H|✔️|✔️|✔️|✔️|
|CVPA1_TOSHIBA_B|✔️|✔️|✔️|✔️|
|CVPCMNL1_SVA_C|✔️|✔️|✔️|✔️|
|CVPCMNL2_SVA_C|✔️|✔️|✔️|✔️|
|CVSE2_Sony_B|✔️|✔️|❌|❌|
|CVSE3_Sony_H|✔️|✔️|❌|❌|
|CVSEFDFT3_Sony_E|✔️|✔️|❌|❌|
|CVWP1_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP2_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP3_TOSHIBA_E|✔️|✔️|✔️|✔️|
|CVWP5_TOSHIBA_E|✔️|✔️|✔️|✔️|
|FI1_Sony_E|✔️|✔️|✔️|✔️|
|FM1_BT_B|✔️|❌|❌|❌|
|FM1_FT_E|✔️|❌|❌|❌|
|FM2_SVA_C|✔️|❌|❌|❌|
|HCBP1_HHI_A|✔️|✔️|✔️|✔️|
|HCBP2_HHI_A|✔️|✔️|✔️|✔️|
|HCMP1_HHI_A|✔️|✔️|✔️|✔️|
|LS_SVA_D|✔️|✔️|✔️|✔️|
|MIDR_MW_D|✔️|✔️|✔️|✔️|
|MPS_MW_A|✔️|✔️|✔️|✔️|
|MR1_BT_A|✔️|✔️|✔️|✔️|
|MR1_MW_A|✔️|✔️|✔️|✔️|
|MR2_MW_A|✔️|✔️|✔️|✔️|
|MR2_TANDBERG_E|✔️|❌|✔️|✔️|
|MR3_TANDBERG_B|✔️|❌|❌|❌|
|MR4_TANDBERG_C|✔️|❌|✔️|✔️|
|MR5_TANDBERG_C|✔️|❌|✔️|✔️|
|MR6_BT_B|✔️|❌|✔️|✔️|
|MR7_BT_B|✔️|❌|❌|❌|
|MR8_BT_B|✔️|❌|✔️|✔️|
|MR9_BT_B|✔️|✔️|❌|❌|
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
|Sharp_MP_PAFF_1r2|✔️|✔️|❌|❌|
|Sharp_MP_PAFF_2r|✔️|✔️|❌|❌|
|SL1_SVA_B|✔️|✔️|✔️|✔️|
|SP1_BT_A|❌|❌|❌|❌|
|sp2_bt_b|❌|❌|❌|❌|
|SVA_BA1_B|✔️|✔️|✔️|✔️|
|SVA_BA2_D|✔️|✔️|✔️|✔️|
|SVA_Base_B|✔️|✔️|✔️|✔️|
|SVA_CL1_E|✔️|✔️|✔️|✔️|
|SVA_FM1_E|✔️|✔️|✔️|✔️|
|SVA_NL1_B|✔️|✔️|✔️|✔️|
|SVA_NL2_E|✔️|✔️|✔️|✔️|
|TOTAL|133/135|122/135|120/135|120/135|
