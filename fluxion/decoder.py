
import functools


class Decoder:
    name = None
    codec = None
    description = None

    @staticmethod
    def decode(self, file):
        return ''


DECODERS = {}


def register_decoder(clazz):
    if clazz.codec not in DECODERS:
        DECODERS[clazz.codec] = []
    DECODERS[clazz.codec].append(clazz)
