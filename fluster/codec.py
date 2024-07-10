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


class OutputFormat(Enum):
    """Output format"""

    NONE = "None"
    YUV420P = "yuv420p"
    YUV422P = "yuv422p"
    YUV420P10LE = "yuv420p10le"
    YUV420P12LE = "yuv420p12le"
    YUV422P10LE = "yuv422p10le"
    YUV422P12LE = "yuv422p12le"
    YUV444P = "yuv444p"
    YUV444P10LE = "yuv444p10le"
    YUV444P12LE = "yuv444p12le"
    YUV444P16LE = "yuv444p16le"
    GRAY = "gray"
    GRAY12LE = "gray12le"
    GRAY16LE = "gray16le"
    GBRP14LE = "gbrp14le"
    UNKNOWN = "Unknown"
