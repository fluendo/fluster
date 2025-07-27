# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

from enum import Enum


class Codec(Enum):
    """Codec type"""

    NONE = "None"
    DUMMY = "Dummy"
    H264 = "H.264"
    H265 = "H.265"
    H266 = "H.266"
    VP8 = "VP8"
    VP9 = "VP9"
    AAC = "AAC"
    AV1 = "AV1"
    MPEG2_VIDEO = "MPEG2_VIDEO"
    MPEG4_VIDEO = "MPEG4_VIDEO"

    def __str__(self) -> str:
        return self.value


class OutputFormat(Enum):
    """Output format"""

    NONE = "None"
    YUV420P = "yuv420p"
    YUV420P10LE = "yuv420p10le"
    YUV420P12LE = "yuv420p12le"
    YUV422P = "yuv422p"
    YUV422P10LE = "yuv422p10le"
    YUV422P12LE = "yuv422p12le"
    YUV444P = "yuv444p"
    YUV444P10LE = "yuv444p10le"
    YUV444P12LE = "yuv444p12le"
    YUV444P14LE = "yuv444p14le"
    YUV444P16LE = "yuv444p16le"
    GBRP = "gbrp"
    GBRP10LE = "gbrp10le"
    GBRP12LE = "gbrp12le"
    GBRP14LE = "gbrp14le"
    GRAY = "gray"
    GRAY10LE = "gray10le"
    GRAY12LE = "gray12le"
    GRAY16LE = "gray16le"
    UNKNOWN = "Unknown"
    FLTP = "fltp"


class Profile(Enum):
    """Profile"""

    NONE = "None"

    # H.264
    CONSTRAINED_BASELINE = "Constrained Baseline"
    BASELINE = "Baseline"
    EXTENDED = "Extended"
    MAIN = "Main"
    HIGH = "High"
    HIGH_10 = "High 10"
    HIGH_10_INTRA = "High 10 Intra"
    HIGH_4_2_2 = "High 4:2:2"
    HIGH_4_2_2_INTRA = "High 4:2:2 Intra"
    HIGH_4_4_4_INTRA = "High 4:4:4 Intra"
    HIGH_4_4_4_PREDICTIVE = "High 4:4:4 Predictive"
    CAVLC_4_4_4 = "CAVLC 4:4:4"
    CAVLC_4_4_4_INTRA = "CAVLC 4:4:4 Intra"

    MAIN_10 = "Main 10"
    MAIN_STILL_PICTURE = "Main Still Picture"
    MAIN_4_2_2_10 = "Main 4:2:2 10"
    MAIN_4_4_4_12 = "Main 4:4:4 12"

    # MPEG4 video
    SIMPLE_PROFILE = "Simple Profile"
