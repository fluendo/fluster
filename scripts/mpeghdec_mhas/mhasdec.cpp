// Fluster - testing framework for decoders conformance
// Copyright (C) 2026, Fluendo, S.A.
//
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation, either version 3
// of the License, or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public
// License along with this library. If not, see <https://www.gnu.org/licenses/>.

// mhasdec: decode a raw MPEG-H 3D Audio MHAS elementary stream (.mhas, ISO/IEC 23008-3 clause 14)
// into a WAV file using the Fraunhofer mpeghdec library.
//
// The mpeghDecoder demo of mpeghdec only reads ISOBMFF/MP4 files. This tool splits a raw MHAS
// stream into access units (every unit ends with a MPEGH3DAFRAME packet) and feeds them to the
// library, accepting the same decoder options as the demo.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

#include "mpeghdecoder.h"
#include "sys/machine_type.h"
#include "sys/wav_file.h"

namespace {

const uint64_t kPacTypFrame = 2;  // PACTYP_MPEGH3DAFRAME
const uint32_t kMaxRenderedChannels = 24;
const uint32_t kMaxRenderedFrameSize = 3072;
const uint64_t kFrameDurationNs = 21333333;  // 1024 samples at 48 kHz, only used as timestamp step

// Reads the bit packed MHAS packet headers
class BitReader {
 public:
  BitReader(const uint8_t* data, size_t size, size_t bytePos) : data_(data), size_(size), bit_(bytePos * 8) {}

  bool read(unsigned count, uint64_t& value) {
    value = 0;
    for (unsigned i = 0; i < count; i++) {
      if ((bit_ >> 3) >= size_) {
        return false;
      }
      value = (value << 1) | ((data_[bit_ >> 3] >> (7 - (bit_ & 7))) & 1);
      bit_++;
    }
    return true;
  }

  bool escapedValue(unsigned n1, unsigned n2, unsigned n3, uint64_t& value) {
    if (!read(n1, value)) {
      return false;
    }
    if (value == (1ULL << n1) - 1) {
      uint64_t add = 0;
      if (!read(n2, add)) {
        return false;
      }
      value += add;
      if (add == (1ULL << n2) - 1) {
        if (!read(n3, add)) {
          return false;
        }
        value += add;
      }
    }
    return true;
  }

  size_t bytePos() const { return bit_ >> 3; }

 private:
  const uint8_t* data_;
  size_t size_;
  size_t bit_;
};

struct Options {
  std::string input;
  std::string output;
  int cicp = -1;  // -1: use the reference layout signalled in the stream
  int bitDepth = 24;  // bits per sample of the WAV file
  struct Param {
    MPEGH_DECODER_PARAMETER id;
    int value;
  };
  std::vector<Param> params;
};

bool parseArgs(int argc, char* argv[], Options& options) {
  for (int i = 1; i < argc; i++) {
    const std::string arg = argv[i];
    if (arg == "-h" || i + 1 >= argc) {
      return false;
    }
    const std::string value = argv[++i];
    if (arg == "-if") {
      options.input = value;
    } else if (arg == "-of") {
      options.output = value;
    } else if (arg == "-tl") {
      options.cicp = std::atoi(value.c_str());
    } else if (arg == "-bd") {
      options.bitDepth = std::atoi(value.c_str());
      if (options.bitDepth != 16 && options.bitDepth != 24 && options.bitDepth != 32) {
        std::cerr << "Unsupported bit depth " << value << std::endl;
        return false;
      }
    } else if (arg == "-rl") {
      options.params.push_back({MPEGH_DEC_PARAM_TARGET_REFERENCE_LEVEL, std::atoi(value.c_str())});
    } else if (arg == "-dse") {
      options.params.push_back({MPEGH_DEC_PARAM_EFFECT_TYPE, std::atoi(value.c_str())});
    } else if (arg == "-db") {
      options.params.push_back({MPEGH_DEC_PARAM_BOOST_FACTOR, std::atoi(value.c_str())});
    } else if (arg == "-dc") {
      options.params.push_back({MPEGH_DEC_PARAM_ATTENUATION_FACTOR, std::atoi(value.c_str())});
    } else if (arg == "-dam") {
      options.params.push_back({MPEGH_DEC_PARAM_ALBUM_MODE, std::atoi(value.c_str())});
    } else {
      std::cerr << "Unknown option " << arg << std::endl;
      return false;
    }
  }
  return !options.input.empty() && !options.output.empty();
}

void usage(const char* progname) {
  std::cout << "Usage: " << progname << " [options] -if infile.mhas -of outfile.wav\n"
            << "       -tl  CICP index of the desired target layout (default: the reference layout of the stream)\n"
            << "       -bd  bits per sample of the output WAV: 16, 24 or 32 (default: 24)\n"
            << "       -rl  DRC target loudness in steps of -0.25 LU, values [40..127]\n"
            << "       -dse MPEG-D DRC effect type request\n"
            << "       -db  DRC boost scale factor\n"
            << "       -dc  DRC attenuation scale factor\n"
            << "       -dam MPEG-D DRC album mode\n"
            << "       -h   Show this help" << std::endl;
}

struct Output {
  HANDLE_WAV wav = nullptr;
  uint32_t sampleRate = 0;
  int numChannels = -1;
  uint32_t frames = 0;
  std::vector<int32_t> buffer = std::vector<int32_t>(kMaxRenderedChannels * kMaxRenderedFrameSize);
};

// Writes all the decoded frames available in the decoder to the WAV file
bool drain(HANDLE_MPEGH_DECODER_CONTEXT decoder, const std::string& filename, int bitDepth, Output& out) {
  MPEGH_DECODER_ERROR status = MPEGH_DEC_OK;
  while (status == MPEGH_DEC_OK) {
    MPEGH_DECODER_OUTPUT_INFO info;
    status = mpeghdecoder_getSamples(decoder, out.buffer.data(), static_cast<uint32_t>(out.buffer.size()), &info);
    if (status == MPEGH_DEC_FEED_DATA) {
      break;
    }
    if (status != MPEGH_DEC_OK) {
      std::cerr << "Error: unable to obtain output (" << status << ")" << std::endl;
      return false;
    }
    if (info.numChannels <= 0 || info.sampleRate <= 0) {
      std::cerr << "Error: unsupported output format" << std::endl;
      return false;
    }
    if (out.numChannels != -1 &&
        (out.numChannels != info.numChannels || out.sampleRate != static_cast<uint32_t>(info.sampleRate))) {
      std::cerr << "Error: unsupported change of sampling rate or number of channels" << std::endl;
      return false;
    }
    out.numChannels = info.numChannels;
    out.sampleRate = info.sampleRate;
    if (!out.wav && WAV_OutputOpen(&out.wav, filename.c_str(), out.sampleRate, out.numChannels, bitDepth)) {
      std::cerr << "Error: unable to create output file " << filename << std::endl;
      return false;
    }
    if (WAV_OutputWrite(out.wav, out.buffer.data(), out.numChannels * info.numSamplesPerChannel, SAMPLE_BITS,
                        SAMPLE_BITS)) {
      std::cerr << "Error: unable to write to output file " << filename << std::endl;
      return false;
    }
    out.frames++;
  }
  return true;
}

// Returns the CICP index of the reference layout signalled in the first mpegh3daConfig() of the stream,
// or -1 when it is not a plain CICP layout (speakerLayoutType != 0) or there is no configuration.
int streamReferenceLayout(const std::vector<uint8_t>& data) {
  const uint64_t kPacTypConfig = 1;
  size_t pos = 0;
  while (pos < data.size()) {
    BitReader reader(data.data(), data.size(), pos);
    uint64_t type = 0, label = 0, length = 0;
    if (!reader.escapedValue(3, 8, 8, type) || !reader.escapedValue(2, 8, 32, label) ||
        !reader.escapedValue(11, 24, 24, length) || reader.bytePos() + length > data.size()) {
      return -1;
    }
    const size_t payload = reader.bytePos();
    if (type == kPacTypConfig) {
      BitReader cfg(data.data(), payload + length, payload);
      uint64_t profile = 0, rateIndex = 0, rate = 0, frameLength = 0, reserved = 0, delay = 0, layoutType = 0,
               layout = 0;
      // mpegh3daConfig(): profile/level (8), sampling frequency index (5) [+ explicit rate (24)],
      // coreSbrFrameLengthIndex (3), reserved (1), receiverDelayCompensation (1), SpeakerConfig3d()
      if (!cfg.read(8, profile) || !cfg.read(5, rateIndex) || (rateIndex == 0x1f && !cfg.read(24, rate)) ||
          !cfg.read(3, frameLength) || !cfg.read(1, reserved) || !cfg.read(1, delay) || !cfg.read(2, layoutType) ||
          layoutType != 0 || !cfg.read(6, layout)) {
        return -1;
      }
      return static_cast<int>(layout);
    }
    pos = payload + static_cast<size_t>(length);
  }
  return -1;
}

}  // namespace

int main(int argc, char* argv[]) {
  Options options;
  if (!parseArgs(argc, argv, options)) {
    usage(argv[0]);
    return 2;
  }

  std::ifstream file(options.input, std::ios::binary);
  if (!file) {
    std::cerr << "Error: unable to open " << options.input << std::endl;
    return 1;
  }
  const std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

  if (options.cicp < 0) {
    options.cicp = streamReferenceLayout(data);
    if (options.cicp < 0) {
      options.cicp = 6;
      std::cerr << "Warning: unable to read the reference layout of the stream, using CICP " << options.cicp
                << std::endl;
    }
  }
  HANDLE_MPEGH_DECODER_CONTEXT decoder = mpeghdecoder_init(options.cicp);
  if (decoder == nullptr) {
    std::cerr << "Error: unable to create the MPEG-H decoder (target layout " << options.cicp << ")" << std::endl;
    return 1;
  }
  for (size_t i = 0; i < options.params.size(); i++) {
    if (mpeghdecoder_setParam(decoder, options.params[i].id, options.params[i].value) != MPEGH_DEC_OK) {
      std::cerr << "Warning: failed to set decoder parameter " << options.params[i].id << " to "
                << options.params[i].value << std::endl;
    }
  }

  Output out;
  bool ok = true;
  size_t pos = 0;
  size_t auStart = 0;
  uint64_t accessUnits = 0;
  while (ok && pos < data.size()) {
    BitReader reader(data.data(), data.size(), pos);
    uint64_t type = 0, label = 0, length = 0;
    if (!reader.escapedValue(3, 8, 8, type) || !reader.escapedValue(2, 8, 32, label) ||
        !reader.escapedValue(11, 24, 24, length) || reader.bytePos() + length > data.size()) {
      std::cerr << "Error: truncated or invalid MHAS packet at byte " << pos << std::endl;
      ok = false;
      break;
    }
    pos = reader.bytePos() + static_cast<size_t>(length);

    if (type != kPacTypFrame) {
      continue;  // sync, config, CRC... packets belong to the access unit that ends with the next frame
    }
    // An access unit ends with each frame packet
    const MPEGH_DECODER_ERROR err = mpeghdecoder_process(
        decoder, data.data() + auStart, static_cast<uint32_t>(pos - auStart), accessUnits * kFrameDurationNs);
    if (err != MPEGH_DEC_OK) {
      std::cerr << "Error: unable to process access unit " << accessUnits << " (" << err << ")" << std::endl;
      ok = false;
      break;
    }
    auStart = pos;
    accessUnits++;
    ok = drain(decoder, options.output, options.bitDepth, out);
  }

  if (ok) {
    ok = mpeghdecoder_flushAndGet(decoder) == MPEGH_DEC_OK &&
         drain(decoder, options.output, options.bitDepth, out);
  }
  if (out.wav) {
    WAV_OutputClose(&out.wav);
  }
  mpeghdecoder_destroy(decoder);

  if (ok && out.frames == 0) {
    std::cerr << "Error: no audio was decoded" << std::endl;
    return 1;
  }
  std::cout << "Access units: " << accessUnits << ", decoded frames: " << out.frames << ", " << out.numChannels
            << " channels, " << out.sampleRate << " Hz" << std::endl;
  return ok ? 0 : 1;
}
