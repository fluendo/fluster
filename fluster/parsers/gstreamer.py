# Fluster - testing framework for decoders conformance
# Copyright (C) 2026, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
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

from functools import lru_cache
from typing import Optional

from fluster.codec import Codec, Profile
from fluster.gstreamer import gst_element_exists, run_pipeline
from fluster.parsers.base import Parser, register_parser

PARSER_PIPELINE_TPL = "filesrc location={} ! {} ! fakesink"
PARSER_PROFILE_PIPELINE_TPL = "filesrc location={} ! {} ! {},profile={} ! fakesink"
CAPS_NAME = {
    Codec.H264: "video/x-h264",
    Codec.H265: "video/x-h265",
    Codec.H266: "video/x-h266",
}


def profile_to_gst(profile: Profile, codec: Codec) -> str:
    """Convert a Fluster profile to the matching GStreamer caps profile."""
    value = str(profile.value).lower().replace(" ", "-")
    if codec == Codec.H266:
        value = value.replace("4:4:4", "444")
    if codec == Codec.H264 and value == "high-4:4:4-predictive":
        value = "high-4:4:4"
    return value


class GStreamerParser(Parser):
    """Base class for GStreamer parsers"""

    provider = "GStreamer"

    def gen_pipeline(self, input_filepath: str, profile: Optional[Profile] = None) -> str:
        """Generate the GStreamer pipeline used to parse the test vector"""
        caps_name = CAPS_NAME.get(self.codec)
        if profile is not None and caps_name:
            return PARSER_PROFILE_PIPELINE_TPL.format(
                input_filepath,
                self.element,
                caps_name,
                profile_to_gst(profile, self.codec),
            )
        return PARSER_PIPELINE_TPL.format(input_filepath, self.element)

    def parse(
        self,
        input_filepath: str,
        timeout: int,
        verbose: bool,
        profile: Optional[Profile] = None,
    ) -> str:
        """Parse the test vector and check that the pipeline completes"""
        run_pipeline(self.gen_pipeline(input_filepath, profile), timeout=timeout, verbose=verbose)
        return ""

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Check if the GStreamer parser element is available"""
        exists = gst_element_exists(self.element)
        if verbose and not exists:
            print(f"GStreamer element {self.element} can't be found to be executed")
        return exists


@register_parser
class H264Parse(GStreamerParser):
    """GStreamer H.264 parser implementation for GStreamer"""

    codec = Codec.H264
    element = "h264parse"


@register_parser
class H265Parse(GStreamerParser):
    """GStreamer H.265 parser implementation for GStreamer"""

    codec = Codec.H265
    element = "h265parse"


@register_parser
class H266Parse(GStreamerParser):
    """GStreamer H.266 parser implementation for GStreamer"""

    codec = Codec.H266
    element = "h266parse"
