import hashlib

from fluxion.codec import Codec
from fluxion.decoder import Decoder, register_decoder

@register_decoder
class H265_Dummy(Decoder):
    name = "H.265 Dummy"
    codec = Codec.H265
    description = "This is a dummy implementation for H.265"

    @staticmethod
    def decode(self, file):
        return hashlib.md5(file.utf8())
