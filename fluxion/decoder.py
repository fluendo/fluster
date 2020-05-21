
import functools


class Decoder:
    name = None
    codec = None
    description = None

    def decode(self, file):
        return ''

    def __str__(self):
        return f'    {self.name}: {self.description}'


DECODERS = {}


def register_decoder(clazz):
    if clazz.codec not in DECODERS:
        DECODERS[clazz.codec] = []
    DECODERS[clazz.codec].append(clazz())
