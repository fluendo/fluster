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

"""MPEG-H 3D Audio MHAS helpers shared by the decoders that can not read a raw MHAS stream.

flumpeghdec (GStreamer) and libmpeghdec (FFmpeg) only get MHAS access units from the 'mhm1' track of an ISOBMFF file,
so the raw MHAS test vectors are wrapped in a temporary MP4 file before decoding them."""

import struct
from typing import List, NamedTuple, Optional

# MHAS packet types (ISO/IEC 23008-3, clause 14)
MHAS_PACTYP_CONFIG = 1
MHAS_PACTYP_FRAME = 2
MHAS_PACTYP_SYNC = 6

# CICP index to render the streams that do not have a CICP reference layout, the same as the reference decoder
DEFAULT_LAYOUT = 6

# Sampling frequencies of the samplingFrequencyIndex of mpegh3daConfig(), 0x1f means an explicit 24 bit value
SAMPLING_RATES = {
    **dict(enumerate([96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350])),
    **dict(
        enumerate([57600, 51200, 40000, 38400, 34150, 28800, 25600, 20000, 19200, 17075, 14400, 12800, 9600], start=16)
    ),
}
# Output samples per access unit for each coreSbrFrameLengthIndex
FRAME_LENGTHS = {0: 768, 1: 1024, 2: 2048, 3: 4096, 4: 4096}


class _Bits:
    """Big endian bit reader"""

    def __init__(self, data: bytes, byte_pos: int = 0) -> None:
        self.data = data
        self.bit = byte_pos * 8

    def read(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | ((self.data[self.bit >> 3] >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return value

    def escaped(self, bits1: int, bits2: int, bits3: int) -> int:
        """escapedValue() of ISO/IEC 23003-3"""
        value = self.read(bits1)
        if value == (1 << bits1) - 1:
            extra = self.read(bits2)
            value += extra
            if extra == (1 << bits2) - 1:
                value += self.read(bits3)
        return value


class _Stream(NamedTuple):
    """Access units of a MHAS stream and the properties read from its mpegh3daConfig()"""

    units: List[bytes]
    rate: int  # Sampling rate
    length: int  # Samples of an access unit
    layout: Optional[int]  # CICP index of the reference speaker layout, None if it is not a CICP layout
    config: bytes  # Payload of the MPEGH3DACFG packet


def _read_mhas(data: bytes) -> _Stream:
    """Split a raw MHAS stream in access units (each one ends with a MPEGH3DAFRAME packet), without the SYNC
    packets, which are not carried in the samples of ISOBMFF files."""
    units: List[bytes] = []
    unit = b""
    rate, length, layout, config = 48000, 1024, None, b""
    config_read = False
    pos = 0
    while pos < len(data):
        bits = _Bits(data, pos)
        packet_type = bits.escaped(3, 8, 8)
        bits.escaped(2, 8, 32)  # label
        size = bits.escaped(11, 24, 24)
        payload = bits.bit >> 3
        end = payload + size
        if end > len(data):
            raise ValueError("Truncated MHAS packet")
        if packet_type == MHAS_PACTYP_CONFIG and not config_read:
            config_read = True
            config = data[payload:end]
            cfg = _Bits(data, payload)
            cfg.read(8)  # mpegh3daProfileLevelIndication
            index = cfg.read(5)
            rate = cfg.read(24) if index == 0x1F else SAMPLING_RATES.get(index, rate)
            length = FRAME_LENGTHS.get(cfg.read(3), length)
            cfg.read(2)  # reserved, receiverDelayCompensation
            if cfg.read(2) == 0:  # speakerLayoutType: CICP
                layout = cfg.read(6)
        if packet_type != MHAS_PACTYP_SYNC:
            unit += data[pos:end]
        pos = end
        if packet_type == MHAS_PACTYP_FRAME:
            units.append(unit)
            unit = b""
    return _Stream(units, rate, length, layout, config)


def _box(kind: bytes, payload: bytes = b"") -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind) + payload


def _full_box(kind: bytes, flags: int, payload: bytes = b"") -> bytes:
    return _box(kind, struct.pack(">I", flags) + payload)


def _write_mp4(path: str, stream: _Stream, with_config: bool) -> None:
    """Write the access units as the samples of a minimal ISOBMFF file ('mhm1' sample entry).

    With with_config the sample entry also has the 'mhaC' box (MHADecoderConfigurationRecord), which is where FFmpeg
    reads the layout of the stream."""
    units, rate, length = stream.units, stream.rate, stream.length
    duration = len(units) * length
    matrix = struct.pack(">9I", 0x10000, 0, 0, 0, 0x10000, 0, 0, 0, 0x40000000)
    mvhd = _full_box(
        b"mvhd",
        0,
        struct.pack(">IIII", 0, 0, rate, duration)
        + struct.pack(">IH", 0x10000, 0x100)
        + bytes(10)
        + matrix
        + bytes(24)
        + struct.pack(">I", 2),
    )
    tkhd = _full_box(
        b"tkhd",
        7,
        struct.pack(">IIIII", 0, 0, 1, 0, duration)
        + bytes(8)
        + struct.pack(">hhhH", 0, 0, 0x100, 0)
        + matrix
        + struct.pack(">II", 0, 0),
    )
    mdhd = _full_box(b"mdhd", 0, struct.pack(">IIII", 0, 0, rate, duration) + struct.pack(">HH", 0x55C4, 0))
    hdlr = _full_box(b"hdlr", 0, struct.pack(">I4s", 0, b"soun") + bytes(12) + b"SoundHandler\0")
    dinf = _box(b"dinf", _full_box(b"dref", 0, struct.pack(">I", 1) + _full_box(b"url ", 1)))
    entry = (
        bytes(6) + struct.pack(">H", 1) + bytes(8) + struct.pack(">HHHH", 2, 16, 0, 0) + struct.pack(">I", rate << 16)
    )
    if with_config:
        profile = stream.config[0] if stream.config else 0
        record = struct.pack(">BBBH", 1, profile, stream.layout or 0, len(stream.config)) + stream.config
        entry += _box(b"mhaC", record)
    entry = _box(b"mhm1", entry)
    count = len(units)
    stbl_head = (
        _full_box(b"stsd", 0, struct.pack(">I", 1) + entry)
        + _full_box(b"stts", 0, struct.pack(">III", 1, count, length))
        + _full_box(b"stsc", 0, struct.pack(">IIII", 1, 1, count, 1))
        + _full_box(b"stsz", 0, struct.pack(">II", 0, count) + b"".join(struct.pack(">I", len(u)) for u in units))
    )
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 512) + b"isomiso2mp41")

    def moov(offset: int) -> bytes:
        stbl = _box(b"stbl", stbl_head + _full_box(b"stco", 0, struct.pack(">II", 1, offset)))
        minf = _box(b"minf", _full_box(b"smhd", 0, bytes(4)) + dinf + stbl)
        return _box(b"moov", mvhd + _box(b"trak", tkhd + _box(b"mdia", mdhd + hdlr + minf)))

    # The only chunk starts after ftyp, moov and the mdat header
    offset = len(ftyp) + len(moov(0)) + 8
    with open(path, "wb") as mp4:
        mp4.write(ftyp + moov(offset) + _box(b"mdat", b"".join(units)))


def mhas_to_mp4(mhas_filepath: str, mp4_filepath: str, with_config: bool = False, layout: Optional[int] = None) -> int:
    """Write the access units of a raw MHAS stream as the samples of a MP4 file.

    The layout is the CICP index written in the 'mhaC' box (only with with_config), the one used to render the stream by
    default. Returns that default: the CICP index of the reference speaker layout of the stream or DEFAULT_LAYOUT if
    the stream does not have one."""
    with open(mhas_filepath, "rb") as mhas:
        stream = _read_mhas(mhas.read())
    default = stream.layout or DEFAULT_LAYOUT
    _write_mp4(mp4_filepath, stream._replace(layout=layout or default), with_config)
    return default
