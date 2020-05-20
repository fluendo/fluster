import hashlib

from fluxion.codec import Codec, Decoder


class H265_Dummy(Decoder):
    name = "H.265 Dummy"
    codec = Codec.H265
    description = "This is a dummy implementation for H.265"

    def decode(self, file):
        return hashlib.md5(file.utf8())
