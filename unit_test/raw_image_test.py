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
import unittest
from typing import List

from fluster.image.raw_buffer import RawBuffer
from fluster.image.raw_image import RawImage


class SyntheticImage:
    """Generate a synthetic RGBA image
    As we do not want to include image files in the repository,
    this class is in charge of generating an image with three verticals
    color bands of at least one pixel."""

    RED = [0xFF, 0, 0, 0xFF]
    GREEN = [0, 0xFF, 0, 0xFF]
    BLUE = [0, 0, 0xFF, 0xFF]

    def __init__(
        self,
        first_band: List[int],
        second_band: List[int],
        third_band: List[int],
        color_band_width: int,
        num_rows: int,
    ) -> None:
        if color_band_width < 3:
            raise RuntimeError("color_band_width must be greater or equal than 3")

        color_band_width = color_band_width // 3
        _row = []
        _row.extend(first_band * color_band_width)
        _row.extend(second_band * color_band_width)
        _row.extend(third_band * color_band_width)

        self._image: bytearray = bytearray(_row * num_rows)

    @property
    def image(self) -> bytearray:
        """Returns the image buffer"""
        return self._image


class TestRawImage(unittest.TestCase):
    """Raw Image unit test"""

    def test_frame_comparison_custom_rgba(self) -> None:
        """Comparison of 2 identical raw images in RGBA pixel format using custom comparison method"""
        square_1 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        square_2 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        source = RawImage(square_1.image, "square_1", 24, 24, RawBuffer.Type.RGBA)
        target = RawImage(square_2.image, "square_2", 24, 24, RawBuffer.Type.RGBA)
        self.assertEqual(source.is_equal(target, RawBuffer.Type.RGBA), 0)

    def test_frame_comparison_custom_yuv(self) -> None:
        """Comparison of 2 identical raw images in YUV420 pixel format using custom comparison method"""
        square_1 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        square_2 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        source = RawImage(square_1.image, "square_1", 24, 24, RawBuffer.Type.RGBA)
        target = RawImage(square_2.image, "square_2", 24, 24, RawBuffer.Type.RGBA)
        self.assertEqual(source.is_equal(target, RawBuffer.Type.YUV420), 0)

    def test_expected_fail_frame_comparison_custom_rgba(self) -> None:
        """Comparison with expected fail of 2 different raw images in RGBA pixel format
        using custom comparison method"""
        square_1 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        square_2 = SyntheticImage(
            SyntheticImage.GREEN, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        source = RawImage(square_1.image, "square_1", 24, 24, RawBuffer.Type.RGBA)
        target = RawImage(square_2.image, "square_2", 24, 24, RawBuffer.Type.RGBA)
        self.assertNotEqual(source.is_equal(target, RawBuffer.Type.RGBA), 0)

    def test_expected_fail_frame_comparison_custom_yuv(self) -> None:
        """Comparison with expected fail of 2 different raw images in YUV420 pixel format
        using custom comparison method"""
        square_1 = SyntheticImage(
            SyntheticImage.RED, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        square_2 = SyntheticImage(
            SyntheticImage.GREEN, SyntheticImage.GREEN, SyntheticImage.BLUE, 24, 24
        )
        source = RawImage(square_1.image, "square_1", 24, 24, RawBuffer.Type.RGBA)
        target = RawImage(square_2.image, "square_2", 24, 24, RawBuffer.Type.RGBA)
        self.assertNotEqual(source.is_equal(target, RawBuffer.Type.RGBA), 0)
