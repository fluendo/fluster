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

# pylint: disable=too-many-instance-attributes, protected-access

from pathlib import Path
from typing import Dict, Optional, Tuple
from fluster.image.raw_buffer import RawBuffer


def get_full_meta_from_name(
    filename: str, buffer_type: Optional[RawBuffer.Type] = None
) -> Tuple[str, str, int, int, RawBuffer.Type, int]:
    """Retrieves the metadata stored in the file name"""
    filename_split = filename.split(".")
    info = str(filename_split[0]).split("_")
    video_name = info[0]
    decode_type = info[1]
    if buffer_type is None:
        buffer_type = RawBuffer.Type(filename_split[1].lower())
    width = int(info[2])
    height = int(info[3])
    num_frame = int(info[4])
    return video_name, decode_type, width, height, buffer_type, num_frame


def get_meta_from_name(
    filename: str, buffer_type: Optional[RawBuffer.Type]
) -> Tuple[str, int, int, RawBuffer.Type]:
    """Retrieves part of the metadata stored in the file name"""
    video_name, _, width, height, buffer_type, _ = get_full_meta_from_name(
        filename, buffer_type
    )
    return video_name, width, height, buffer_type


class RawImage:
    """Class to handle the raw image"""

    def __init__(
        self,
        buffer: bytes,
        video_name: str,
        width: int,
        height: int,
        buffer_type: RawBuffer.Type,
        create_diff_buffer: bool = False,
    ) -> None:

        self._buffer_type: RawBuffer.Type = buffer_type
        self._width: int = width
        self._height: int = height
        self._video_name: str = video_name
        self._create_diff_buffer: bool = create_diff_buffer
        self._data: Dict[RawBuffer.Type, RawBuffer] = {
            buffer_type: RawBuffer(
                buffer,
                width,
                height,
                buffer_type,
                create_diff_buffer=create_diff_buffer,
            )
        }

    @staticmethod
    def from_file(
        filename: str, buffer_type: Optional[RawBuffer.Type] = None
    ) -> "RawImage":
        """Create a RawImage from a file using the content and the metadata stored in the file name"""
        file_path = Path(filename)
        if not file_path.exists():
            raise RuntimeError(f"The file {filename} does not exists")
        buffer = bytes(file_path.read_bytes())
        return RawImage(buffer, *get_meta_from_name(filename, buffer_type))

    @staticmethod
    def from_buffer(
        filename: str,
        buffer: bytes,
        buffer_type: RawBuffer.Type,
    ) -> "RawImage":
        """Create a RawImage from a buffer using the content and the metadata stored in the file name"""
        return RawImage(buffer, *get_meta_from_name(filename, buffer_type))

    def __str__(self) -> str:
        message = f"{self._video_name} with \n"
        for key in self._data:
            raw_image = self._data[key]
            message += f"buffer type {raw_image.buffer_type} ({raw_image.width},{raw_image.height})\n"
        return message

    def _convert(self, buffer_type: RawBuffer.Type) -> None:
        if buffer_type not in self._data:
            self._data[buffer_type] = self.default_raw_buffer.from_format(buffer_type)

    @property
    def default_raw_buffer(self) -> RawBuffer:
        """Return the first buffer created"""
        return self._data[self._buffer_type]

    @property
    def video_name(self) -> str:
        """Return the video name"""
        return self._video_name

    def is_equal(
        self,
        target_image: "RawImage",
        buffer_type: RawBuffer.Type,
    ) -> int:
        """Compares two RawBuffer in the specified pixel format"""
        self._convert(buffer_type)
        target_image._convert(buffer_type)

        result: int = self._data[buffer_type].is_equal(
            target_image._data[buffer_type], buffer_type
        )

        if result > 0 and self._create_diff_buffer:
            self.save_diff(f"{self._video_name}_color_diff.rgba")

        return result

    def save_diff(self, filename: str) -> None:
        """Save buffer_diff stored in the raw image"""
        self.default_raw_buffer.save_diff(filename)

    def save(self, filename: str, buffer_type: RawBuffer.Type) -> None:
        """Save RawBuffer stored in the specified pixel format"""
        self._convert(buffer_type)
        self._data[buffer_type].save(filename)

    def save_as_python(self, filename: str, buffer_type: RawBuffer.Type) -> None:
        """Save RawBuffer stored in the specified pixel format as a python bytes array"""
        self._convert(buffer_type)
        self._data[self._buffer_type].save_as_python(filename)
