# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
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

from typing import Any, Dict, List, Optional

from fluster.codec import Codec, OutputFormat
from fluster.decoder import Decoder, NotSupportedError, register_decoder
from fluster.utils import file_checksum, run_command

# Bits per sample of the decoded WAV. fluster compares 16 or 32 bit WAV files and its tolerance of 128 only makes
# sense with 16 bit samples (the decoders under test have to output the same width as the reference one)
OUTPUT_BIT_DEPTH = 16

# Decoder target loudness is given to mpeghdec in steps of -0.25 LU (valid range 40..127)
LOUDNESS_STEPS_PER_LU = 4


@register_decoder
class MPEGHMhasDecoder(Decoder):
    """Fraunhofer mpeghdec MPEG-H 3D Audio decoder for raw MHAS streams.

    `mhasdec` is a small front-end built over the libmpeghdec library (see scripts/mpeghdec_mhas)
    because the mpeghDecoder demo of mpeghdec only reads ISOBMFF files.
    """

    name = "Fraunhofer-mpeghdec"
    description = "Fraunhofer mpeghdec MPEG-H 3D Audio decoder (raw MHAS front-end)"
    codec = Codec.MPEGH_3DA
    binary = "mhasdec"
    is_reference = True

    @staticmethod
    def _options(optional_params: Optional[Dict[str, Any]]) -> List[str]:
        """Translate the optional parameters of a test vector to mhasdec options"""
        options: List[str] = []
        params = dict(optional_params or {})

        if "preset_id" in params:
            # libmpeghdec has no API to select a preset, it is requested with a MHAS user interaction packet
            raise NotSupportedError("Selecting an MPEG-H preset is not supported by mpeghdec")
        if "target_layout" in params:
            options += ["-tl", str(params.pop("target_layout"))]
        if "drc_effect_type" in params:
            options += ["-dse", str(params.pop("drc_effect_type"))]
        if "target_loudness" in params:
            # The test vectors give a negative loudness in LKFS, e.g. -24
            options += ["-rl", str(int(-params.pop("target_loudness") * LOUDNESS_STEPS_PER_LU))]
        if params:
            raise NotSupportedError(f"Unknown parameters for {MPEGHMhasDecoder.name}: {sorted(params)}")
        return options

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
        run_command(
            [
                self.binary,
                "-bd",
                str(OUTPUT_BIT_DEPTH),
                *self._options(optional_params),
                "-if",
                input_filepath,
                "-of",
                output_filepath,
            ],
            timeout=timeout,
            verbose=verbose,
        )
        return file_checksum(output_filepath)
