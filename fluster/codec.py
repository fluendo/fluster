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
from typing import Optional


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
    AC4 = "AC4"
    EAC3 = "EAC3"
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
    """Profile

    Each member carries a ``codec`` attribute identifying its codec.
    """

    codec: Codec

    NONE = ("None", Codec.NONE)

    # H.264
    CONSTRAINED_BASELINE = ("Constrained Baseline", Codec.H264)
    BASELINE = ("Baseline", Codec.H264)
    EXTENDED = ("Extended", Codec.H264)
    MAIN = ("Main", Codec.H264)
    HIGH = ("High", Codec.H264)
    HIGH_10 = ("High 10", Codec.H264)
    HIGH_10_INTRA = ("High 10 Intra", Codec.H264)
    HIGH_4_2_2 = ("High 4:2:2", Codec.H264)
    HIGH_4_2_2_INTRA = ("High 4:2:2 Intra", Codec.H264)
    HIGH_4_4_4_INTRA = ("High 4:4:4 Intra", Codec.H264)
    HIGH_4_4_4_PREDICTIVE = ("High 4:4:4 Predictive", Codec.H264)
    CAVLC_4_4_4 = ("CAVLC 4:4:4", Codec.H264)
    CAVLC_4_4_4_INTRA = ("CAVLC 4:4:4 Intra", Codec.H264)

    MAIN_10 = ("Main 10", Codec.H264)
    MAIN_STILL_PICTURE = ("Main Still Picture", Codec.H264)
    MAIN_4_2_2_10 = ("Main 4:2:2 10", Codec.H264)
    MAIN_4_4_4_12 = ("Main 4:4:4 12", Codec.H264)

    # H.266
    MAIN_10_4_4_4 = ("Main 10 4:4:4", Codec.H266)
    MAIN_10_STILL_PICTURE = ("Main 10 Still Picture", Codec.H266)
    MAIN_10_4_4_4_STILL_PICTURE = ("Main 10 4:4:4 Still Picture", Codec.H266)
    MULTILAYER_MAIN_10 = ("Multilayer Main 10", Codec.H266)
    MULTILAYER_MAIN_10_4_4_4 = ("Multilayer Main 10 4:4:4", Codec.H266)

    # MPEG2 video
    PROFILE_4_2_2 = ("4:2:2", Codec.MPEG2_VIDEO)
    SIMPLE = ("Simple", Codec.MPEG2_VIDEO)

    # MPEG4 video
    SIMPLE_PROFILE = ("Simple Profile", Codec.MPEG4_VIDEO)
    ADVANCED_SIMPLE_PROFILE = ("Advanced Simple Profile", Codec.MPEG4_VIDEO)
    SIMPLE_STUDIO_PROFILE = ("Simple Studio Profile", Codec.MPEG4_VIDEO)
    ERROR_RESILIENT_SIMPLE_SCALABLE_PROFILE = (
        "Error Resilient Simple Scalable Profile",
        Codec.MPEG4_VIDEO,
    )

    # VP9
    VP9_PROFILE_0 = ("VP9 Profile 0", Codec.VP9)
    VP9_PROFILE_1 = ("VP9 Profile 1", Codec.VP9)
    VP9_PROFILE_2 = ("VP9 Profile 2", Codec.VP9)
    VP9_PROFILE_3 = ("VP9 Profile 3", Codec.VP9)

    def __new__(cls, display_name: str, codec: Optional[Codec] = None) -> "Profile":
        if codec is None:
            for member in cls:
                if member.value == display_name:
                    return member
            raise ValueError(f"{display_name!r} is not a valid {cls.__qualname__}")
        obj = object.__new__(cls)
        obj._value_ = display_name
        obj.codec = codec
        return obj
