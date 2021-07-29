# Fluster - testing framework for decoders conformance
# Copyright (C) 2021, Fluendo, S.A.
#  Author: Manuel Jimeno Martínez <mjimeno@fluendo.com>, Fluendo, S.A.
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
from pathlib import Path
from typing import Optional, List

from fluster.image.raw_buffer import RawBuffer
from fluster.image.raw_image import RawImage, get_meta_from_name


class RawVideo:
    """Class to handle the raw video"""

    def __init__(
        self,
        buffer: bytes,
        video_name: str,
        width: int,
        height: int,
        buffer_type: RawBuffer.Type,
    ):
        self._buffer: bytes = buffer
        self._video_name: str = video_name
        self._width: int = width
        self._height: int = height
        self._buffer_type: RawBuffer.Type = buffer_type
        self._frames = []

        if buffer_type == RawBuffer.Type.YUV420:
            if width % 4 != 0 or height % 4 != 0:
                raise Exception("Width and height must be multiples of 4")
            len_buffer = (width * height * 3) // 2
        elif buffer_type == RawBuffer.Type.RGBA:
            len_buffer = width * height * 4
        else:
            raise RuntimeError(f"The type buffer {buffer_type} is not supported")

        # Slice the buffer using len_buffer
        last_frame_start: int = 0
        for next_frame_start in range(len_buffer, len(buffer) + 1, len_buffer):
            self._frames.append(
                RawImage(
                    buffer[last_frame_start:next_frame_start],
                    video_name,
                    width,
                    height,
                    buffer_type,
                )
            )
            last_frame_start = next_frame_start

    @property
    def frames(self) -> List[RawImage]:
        """Return the frames of the video"""
        return self._frames

    @property
    def width(self) -> int:
        """Return the width of the video"""
        return self._width

    @property
    def height(self) -> int:
        """Return the height of the video"""
        return self._height

    @staticmethod
    def from_file(
        filename: str,
        buffer_type: Optional[RawBuffer.Type] = None,
    ) -> "RawVideo":
        """Create a RawVideo from a file using the content and the metadata stored in the file name"""
        file_path = Path(filename)

        if not file_path.exists():
            raise RuntimeError(f"The file {filename} does not exist")

        buffer = bytes(file_path.read_bytes())

        return RawVideo(buffer, *get_meta_from_name(filename, buffer_type))

    @staticmethod
    def from_buffer(
        filename: str,
        buffer: bytes,
        buffer_type: RawBuffer.Type,
    ) -> "RawVideo":
        """Create a RawVideo from a buffer using the content and the metadata stored in the file name"""
        return RawVideo(buffer, *get_meta_from_name(filename, buffer_type))
