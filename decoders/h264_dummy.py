import hashlib

from fluxion.codec import Codec
from fluxion.decoder import Decoder, register_decoder


@register_decoder
class H264_Dummy(Decoder):
    name = "H.264 Dummy"
    codec = Codec.H264
    description = "This is a dummy implementation for H.264"

    def decode(self, file):
        return hashlib.md5(file.utf8())
