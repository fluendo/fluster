# Fluster - testing framework for decoders conformance
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from enum import Enum


class Codec(Enum):
    """Codec type"""

    NONE = "None"
    DUMMY = "Dummy"
    H264 = "H.264"
    H265 = "H.265"
    VP8 = "VP8"
    VP9 = "VP9"


class PixelFormat(Enum):
    """Pixel format"""

    YUV420P = "yuv420p"
    YUV420P10LE = "yuv420p10le"

    def to_gst(self) -> str:
        """Return GStreamer pixel format"""
        mapping = {self.YUV420P: "I420", self.YUV420P10LE: "I420_10LE"}

        return mapping[str(self)]
