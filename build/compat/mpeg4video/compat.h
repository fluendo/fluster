/*
 * Fluster - testing framework for decoders conformance
 * Copyright (C) 2026, Fluendo, S.A.
 *
 * Force-included (-include) when building the MPEG-4 Visual reference software (vm_dec):
 * its pre-standard C++ uses iostream names without the std:: prefix.
 */

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <strstream>

class CVideoObjectDecoder;
class CVideoObjectDecoderTPS;
class CEnhcBufferEncoder;

using std::cerr;
using std::cin;
using std::cout;
using std::dec;
using std::endl;
using std::ends;
using std::fixed;
using std::flush;
using std::fstream;
using std::hex;
using std::ifstream;
using std::ios;
using std::iostream;
using std::istream;
using std::istrstream;
using std::left;
using std::ofstream;
using std::oct;
using std::ostream;
using std::ostrstream;
using std::right;
using std::scientific;
using std::setfill;
using std::setprecision;
using std::setw;
using std::streambuf;
using std::streamoff;
using std::streampos;
using std::strstream;
using std::strstreambuf;
using std::ws;
