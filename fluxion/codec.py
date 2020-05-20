class Codec:
    H264 = 'H.264'
    H265 = 'H.265'


class Decoder:
    name = None
    codec = None
    description = None

    def decode(self, file):
        pass
