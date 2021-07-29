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
from typing import Tuple, Optional, Dict, Any
from enum import Enum

PixelToIgnore = Dict[int, Any]


class RawBuffer:
    """Class to handle the raw image buffer"""

    _RGBA_TOLERANCE = 0
    _YUV_TOLERANCE = 0

    class Type(Enum):
        """Allows raw buffer types"""

        YUV420 = "yuv420"
        RGBA = "rgba"

    def __init__(
        self,
        buffer: bytes,
        width: int,
        height: int,
        buffer_type: Type = Type.YUV420,
        pixels_to_ignore: Optional[PixelToIgnore] = None,
        create_diff_buffer: bool = False,
        color_diff: Optional[Tuple[int, int, int]] = None,
        buffer_diff: Optional[bytearray] = None,
    ):
        if buffer_type == RawBuffer.Type.YUV420:
            if (width % 4) or (height % 4):
                raise Exception("Width and height must be multiples of 4")
            len_buffer = (width * height * 3) // 2
        elif buffer_type == RawBuffer.Type.RGBA:
            len_buffer = width * height * 4
        else:
            raise RuntimeError(f"The type buffer {buffer_type} is not supported")

        if len(buffer) != len_buffer:
            raise RuntimeError(
                f"The size of the frame and the len of the buffer do not match {len(buffer)} {len_buffer}"
            )

        self._width = width
        self._height = height
        self._buffer_type = buffer_type
        self._buffer = buffer
        if pixels_to_ignore is None:
            self._pixels_to_ignore: PixelToIgnore = {}
        else:
            self._pixels_to_ignore = pixels_to_ignore
        self._create_diff_buffer = create_diff_buffer

        if color_diff is None:
            self._color_diff: Tuple[int, int, int] = (0xFF, 0, 0)
        else:
            self._color_diff = color_diff

        if buffer_diff is None:
            self._buffer_diff: bytearray = bytearray()
        else:
            self._buffer_diff = buffer_diff

    def from_format(self, buffer_type: Type) -> "RawBuffer":
        """Returns an instance of RawBuffer in the requested format"""
        if (
            self.buffer_type == RawBuffer.Type.RGBA
            and buffer_type == RawBuffer.Type.YUV420
        ):
            new_buffer = self.rgba_to_yuv420()
        elif (
            self.buffer_type == RawBuffer.Type.YUV420
            and buffer_type == RawBuffer.Type.RGBA
        ):
            new_buffer = self.yuv420_to_rgba()
        elif self.buffer_type == buffer_type:
            new_buffer = self.buffer
        else:
            raise RuntimeError(f"The {buffer_type} is not supported")

        return RawBuffer(
            new_buffer,
            self._width,
            self._height,
            buffer_type,
            self._pixels_to_ignore,
            self._create_diff_buffer,
            self._color_diff,
            self._buffer_diff,
        )

    @property
    def buffer_diff(self) -> Optional[bytearray]:
        """Return the buffer with comparison differences"""
        return self._buffer_diff

    @property
    def create_diff_buffer(self) -> bool:
        """Returns a value that indicates it should be generated a new buffer with the differences between buffers"""
        return self._create_diff_buffer

    @create_diff_buffer.setter
    def create_diff_buffer(self, value: bool) -> None:
        """Set create_diff_buffer value"""
        self._create_diff_buffer = value
        if value:
            self._color_diff = (0xFF, 0, 0)

    @property
    def color_diff(self) -> Optional[Tuple[int, int, int]]:
        """Returns a value that indicates the color of the different points in a three-position tuple in RGB format"""
        return self._color_diff

    @color_diff.setter
    def color_diff(self, value: Tuple[int, int, int]) -> None:
        """Set color_diff value"""
        if len(value) != 3:
            raise RuntimeError("A format other than RGB is not allowed")
        self._color_diff = value
        self._create_diff_buffer = True

    @property
    def buffer(self) -> bytes:
        """Returns the raw data"""
        return self._buffer

    @property
    def pixels_to_ignore(self) -> PixelToIgnore:
        """Returns the list of pixels to ignore in comparison"""
        return self._pixels_to_ignore

    @property
    def buffer_type(self) -> Type:
        """Returns the buffer type of the class"""
        return self._buffer_type

    @property
    def width(self) -> int:
        """Returns the width of the image stored in the buffer"""
        return self._width

    @property
    def height(self) -> int:
        """Returns the height of the image stored in the buffer"""
        return self._height

    @property
    def frame_size(self) -> int:
        """Returns the size of the frame stored in the buffer"""
        return self._height * self._width

    def _rgba(self, index: int) -> Tuple[int, int, int, int]:
        """Returns the RGBA tuple from the indicated position"""
        return (
            self._buffer[index] & 0xFF,
            self._buffer[index + 1] & 0xFF,
            self._buffer[index + 2] & 0xFF,
            self._buffer[index + 3] & 0xFF,
        )

    @staticmethod
    def _rgba_to_yuv(rgba_value: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
        """It converts an RGBA tuple to another YUV420 tuple"""

        def y_from_rgba(_r: int, _g: int, _b: int, _a: int) -> int:
            return RawBuffer.clamp(((66 * _r + 129 * _g + 25 * _b + 128) >> 8) + 16)

        def u_from_rgba(_r: int, _g: int, _b: int, _a: int) -> int:
            return RawBuffer.clamp(((-38 * _r - 74 * _g + 112 * _b + 128) >> 8) + 128)

        def v_from_rgba(_r: int, _g: int, _b: int, _a: int) -> int:
            return RawBuffer.clamp(((112 * _r - 94 * _g - 18 * _b + 128) >> 8) + 128)

        return (
            y_from_rgba(*rgba_value),
            u_from_rgba(*rgba_value),
            v_from_rgba(*rgba_value),
        )

    def _yuv420_comparison(
        self, target: "RawBuffer", deviations: Dict[int, int]
    ) -> int:
        """Comparison of two buffers of type YUV420"""
        source_buffer: bytes = self.buffer
        target_buffer: bytes = target.buffer
        size_chroma: int = self.frame_size // 4
        start_u: int = self.frame_size
        start_v: int = self.frame_size + size_chroma
        total_errors = 0

        def check_deviation(source_pixel: int, target_pixel: int) -> int:
            deviation = int(abs(source_pixel - target_pixel))
            if deviation > self._YUV_TOLERANCE:
                if i not in self._pixels_to_ignore:
                    deviations[deviation] = (
                        1 if deviation not in deviations else deviations[deviation] + 1
                    )
                    return 1
            return 0

        # First compare the y buffer
        for i in range(self.frame_size):
            total_errors += check_deviation(source_buffer[i], target_buffer[i])
            if i < size_chroma:
                total_errors += check_deviation(
                    source_buffer[i + start_u], target_buffer[i + start_u]
                )
                total_errors += check_deviation(
                    source_buffer[i + start_v], target_buffer[i + start_v]
                )

        return total_errors

    def _rgba_comparison(self, target: "RawBuffer", deviations: Dict[int, int]) -> int:
        """Comparison of two buffers of type RGBA"""
        if self._create_diff_buffer:
            self._buffer_diff = bytearray(self._buffer)
        total_errors = 0

        for i in range((self.frame_size * 4)):
            deviation = abs(self._buffer[i] - target.buffer[i])
            if deviation:
                total_errors += 1
                if self._create_diff_buffer and i % 4 == 0:
                    self._buffer_diff[i] = self._color_diff[0]
                    self._buffer_diff[i + 1] = self._color_diff[1]
                    self._buffer_diff[i + 2] = self._color_diff[2]
                deviations[deviation] = (
                    1 if deviation not in deviations else deviations[deviation] + 1
                )

        return total_errors

    @staticmethod
    def clamp(value: int) -> int:
        """Clip between 0 and 255"""
        return max(0, min(255, value))

    def save(self, filename: str) -> None:
        """Save the content of the buffer to file"""
        with open(filename, "wb") as file:
            file.write(self._buffer)

    def save_diff(self, filename: str) -> None:
        """Save the content of the buffer to file"""
        with open(filename, "wb") as file:
            file.write(self._buffer_diff)

    def save_as_python(self, filename: str) -> None:
        """Save the content of the buffer to file"""
        with open(filename, "w") as file:
            counter = 0
            sentence = "image_content = ["
            for item in self._buffer:
                sentence += f"{item},"
                if counter % 20 == 0:
                    sentence += "\n"
                counter += 1
            sentence += "]"
            file.write(sentence)

    def rgba_to_yuv420(self) -> bytes:
        """Converts rgba to yuv420p"""
        yuv_buffer = bytearray((self.frame_size * 3) // 2)
        u_index = self.frame_size
        v_index = u_index + (self.frame_size // 4)

        def is_pixel_to_ignore(_r: int, _g: int, _b: int, _a: int) -> bool:
            return _r in (0, 255) or _g in (0, 255) or _b in (0, 255)

        for row in range(self._height):
            for column in range(self._width):
                y_index = row * self._width + column
                rgba = self._rgba(y_index * 4)
                yuv = RawBuffer._rgba_to_yuv(rgba)
                yuv_buffer[y_index] = yuv[0]

                if is_pixel_to_ignore(*rgba):
                    self._pixels_to_ignore[y_index] = [rgba, yuv]

                if row % 2 == 0 and y_index % 2 == 0:
                    yuv_buffer[u_index] = yuv[1]
                    u_index += 1
                    yuv_buffer[v_index] = yuv[2]
                    v_index += 1

        return bytes(yuv_buffer)

    def yuv420_to_rgba(self) -> bytes:
        """Converts yuv420p to rgba"""
        rgba_buffer = bytearray(self._width * self._height * 4)
        rgba_index = 0
        y_index = 0

        def r_from_yuv(_y: int, _u: int, _v: int) -> int:
            return RawBuffer.clamp((_y + 409 * _v + 128) // 256)

        def g_from_yuv(_y: int, _u: int, _v: int) -> int:
            return RawBuffer.clamp((_y - 100 * _u - 208 * _v + 128) // 256)

        def b_from_yuv(_y: int, _u: int, _v: int) -> int:
            return RawBuffer.clamp((_y + 516 * _u + 128) // 256)

        for row in range(0, self._height):
            u_index = self.frame_size + (row // 2) * (self._width // 2)
            v_index = u_index + self.frame_size // 4

            for column in range(0, self._width):
                yuv = (
                    ((self._buffer[y_index] - 16) * 298),
                    (self._buffer[u_index] - 128),
                    (self._buffer[v_index] - 128),
                )

                rgba_buffer[rgba_index] = r_from_yuv(*yuv)
                rgba_buffer[rgba_index + 1] = g_from_yuv(*yuv)
                rgba_buffer[rgba_index + 2] = b_from_yuv(*yuv)
                rgba_buffer[rgba_index + 3] = 0xFF

                u_index += column % 2
                v_index += column % 2
                y_index += 1
                rgba_index += 4

        return bytes(rgba_buffer)

    def is_equal(
        self,
        target: "RawBuffer",
        buffer_type: Type,
    ) -> int:
        """Comparison of two RawBuffers"""
        deviations: Dict[int, int] = {}
        if buffer_type == RawBuffer.Type.YUV420:
            different_pixels = self._yuv420_comparison(target, deviations)
        elif buffer_type == RawBuffer.Type.RGBA:
            different_pixels = self._rgba_comparison(target, deviations)
        else:
            raise RuntimeError(f"The {buffer_type} is not supported")

        return different_pixels
