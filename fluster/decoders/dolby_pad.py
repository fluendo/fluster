# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#  Author: Martin Cesarini Bozzo <mcesarini@fluendo.com>, Fluendo, S.A.
#  Author: Pablo Garcia Sancho <pgarcia@fluendo.com>, Fluendo, S.A.
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
import platform
from functools import lru_cache
from typing import Any, Dict, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, register_decoder
from fluster.utils import file_checksum, run_command

# Mapping from test suite channels_layout to decoder speaker_config.
# Shared by reference and GStreamer-based EAC3 decoders.
EAC3_CHANNELS_LAYOUT_TO_SPEAKER_CONFIG: Dict[int, int] = {
    0: 1,  # JOC   → 5.1
    2: 0,  # Stereo → STEREO
    7: 1,  # 5.1   → 5.1
}


class DolbyPADDecoder(Decoder):
    """Generic class for Dolby Pro Audio Decoder reference decoder"""

    name = ""
    description = ""
    binary = f"decoder_reference_app_{platform.system().lower()}_x86_64"
    codec = Codec.NONE
    is_reference = True
    _speaker_config_map: Dict[int, int] = {}

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Check if the reference decoder binary is available for this platform."""
        if platform.system() not in ("Linux", "Windows"):
            if verbose:
                print(f"ac4 decoder is not available for OS {platform.system()}")
            return False
        return super().check(verbose)

    def decode(
        self,
        input_filepath: str,
        output_filepath: str,
        output_format: OutputFormat,
        timeout: int,
        verbose: bool,
        keep_files: bool,
        optional_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Decodes input_filepath in output_filepath"""
        cmd = [self.binary, "-i", input_filepath, "-o", output_filepath]

        # Map channels_layout to -ddp_decoder_speaker_config so the reference
        # decoder output matches the native channel layout of the stream.
        if self._speaker_config_map and optional_params:
            channels_layout = optional_params.get("channels_layout", 0)
            speaker_config = self._speaker_config_map.get(channels_layout, 1)
            cmd += ["-ddp_decoder_speaker_config", str(speaker_config)]

        run_command(
            cmd,
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)


@register_decoder
class AC4Decoder(DolbyPADDecoder):
    """AC-4 Dolby Pro Audio Decoder Software Development Kit reference decoder implementation"""

    name = "DolbyPADSReferenceDecoder"
    description = "AC-4 Dolby Pro Audio Decoder Software Development Kit reference decoder implementation"
    codec = Codec.AC4


@register_decoder
class EAC3PRODECDecoder(DolbyPADDecoder):
    """Dolby EC-3 Online Delivery Kit 1.6 elementary stream reference decoder implementation"""

    name = "Dolby_EAC3PRODEC_ReferenceDecoder"
    description = "Dolby EC-3 Online Delivery Kit 1.6 elementary stream reference decoder implementation"
    codec = Codec.EAC3
    _speaker_config_map = EAC3_CHANNELS_LAYOUT_TO_SPEAKER_CONFIG
