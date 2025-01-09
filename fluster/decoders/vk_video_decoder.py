# Fluster - testing framework for decoders conformance
# Copyright (C) 2024, Igalia.
#  Author: Stephane Cerveau
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

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command


class VKVSDecoder(Decoder):
    """NVidia vk_video_samples decoder implementation"""

    binary = "vk-video-dec-test"

    def __init__(self) -> None:
        super().__init__()
        self.name = f"VKVS-{self.codec.value}"
        self.description = f"Vulkan Video Samples {self.codec.value} decoder"

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
        multiple_layers: bool = False,
    ) -> str:
        """Decodes input_filepath in output_filepath"""
        codec_mapping = {
            Codec.H264: "avc",
            Codec.H265: "hevc",
            Codec.AV1: "av1",
        }
        run_command(
            [
                self.binary,
                "-i",
                input_filepath,
                "-o",
                output_filepath,
                "--codec",
                codec_mapping[self.codec],
                "--noPresent",
            ],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)


@register_decoder
class VKVSH264Decoder(VKVSDecoder):
    """Vulkan Video Samples decoder for H.264"""

    codec = Codec.H264


@register_decoder
class VKVSH265Decoder(VKVSDecoder):
    """Vulkan Video Samples decoder for H.265"""

    codec = Codec.H265


@register_decoder
class VKVSAV1Decoder(VKVSDecoder):
    """Vulkan Video Samples decoder for AV1"""

    codec = Codec.AV1
