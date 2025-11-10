# Fluster - testing framework for decoders conformance
# Copyright (C) 2025, Fluendo, S.A.
#  Author: Ruben Sanchez Sanchez <rsanchez@fluendo.com>, Fluendo, S.A.
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

# Fluster Docker Image with Hardware Acceleration Support
# Supports VAAPI, VDPAU, NVDEC, and Intel QuickSync

ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

# Re-declare args after FROM to make them available in build stages
ARG UBUNTU_VERSION
ARG NVIDIA_DRIVER_VERSION
# FFmpeg installation method: "system" (default), "static", "source"
ARG FFMPEG_INSTALL_METHOD=system
# FFmpeg version for "static" and "source" methods
ARG FFMPEG_VERSION=8.0
# GStreamer installation method: "system" (default), "source"
ARG GSTREAMER_INSTALL_METHOD=system
# GStreamer version for "source" method
ARG GSTREAMER_VERSION=1.24.2

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /fluster

# Base dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ca-certificates \
    software-properties-common \
    python3 \
    python3-pip \
    python3-venv \
    pciutils \
    && rm -rf /var/lib/apt/lists/*

# VAAPI support, Intel and AMD drivers
RUN apt-get update && apt-get install -y \
    libva-dev \
    libva-drm2 \
    libva-x11-2 \
    vainfo \
    i965-va-driver \
    mesa-va-drivers \
    && (apt-get install -y intel-media-va-driver-non-free || \
        apt-get install -y intel-media-va-driver || true) \
    && rm -rf /var/lib/apt/lists/*

# VAAPI driver for NVIDIA (Ubuntu 24.04+)
RUN if [ "${UBUNTU_VERSION}" = "24.04" ]; then \
        apt-get update && \
        apt-get install -y nvidia-vaapi-driver && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# VDPAU support and GPU drivers
RUN apt-get update && apt-get install -y \
    libvdpau-dev \
    libvdpau1 \
    vdpauinfo \
    libvdpau-va-gl1 \
    mesa-vdpau-drivers \
    && rm -rf /var/lib/apt/lists/*

# NVIDIA VDPAU libraries (must match host driver version)
RUN if [ -n "${NVIDIA_DRIVER_VERSION}" ]; then \
        apt-get update && \
        apt-get install -y \
            libnvidia-decode-${NVIDIA_DRIVER_VERSION} \
            libnvidia-encode-${NVIDIA_DRIVER_VERSION} && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Intel QuickSync support via Media SDK and oneVPL
RUN apt-get update && apt-get install -y \
    libmfx1 \
    libmfx-tools \
    && (apt-get install -y libmfx-gen1.2 || true) \
    && (apt-get install -y libvpl-dev libvpl2 || true) \
    && rm -rf /var/lib/apt/lists/*

# FFmpeg installation (3 methods: system, static, source)
# Method "source": Build FFmpeg from source with all backends (VAAPI, VDPAU, QuickSync)
# Method "static": Download pre-built static FFmpeg binary
# Method "system": Install FFmpeg from system packages (default)
RUN if [ "${FFMPEG_INSTALL_METHOD}" = "source" ]; then \
      apt-get update -qq && apt-get install -y \
        autoconf \
        automake \
        build-essential \
        cmake \
        git-core \
        libass-dev \
        libfreetype6-dev \
        libgnutls28-dev \
        libmp3lame-dev \
        libsdl2-dev \
        libtool \
        libva-dev \
        libvdpau-dev \
        libvorbis-dev \
        libxcb1-dev \
        libxcb-shm0-dev \
        libxcb-xfixes0-dev \
        meson \
        ninja-build \
        pkg-config \
        texinfo \
        wget \
        yasm \
        zlib1g-dev \
        nasm \
        libx264-dev \
        libx265-dev \
        libnuma-dev \
        libvpx-dev \
        libfdk-aac-dev \
        libopus-dev \
        libmfx-dev \
        libunistring-dev \
      && rm -rf /var/lib/apt/lists/* && \
      mkdir /tmp/aom && \
      cd /tmp/aom && \
      git -C aom pull 2> /dev/null || git clone --depth 1 https://aomedia.googlesource.com/aom && \
      mkdir -p aom_build && \
      cd aom_build && \
      cmake -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX="/usr/local" -DENABLE_TESTS=OFF -DENABLE_NASM=on ../aom && \
      make && \
      make install && \
      cd / && rm -rf /tmp/aom && \
      mkdir /tmp/dav1d && \
      cd /tmp/dav1d && \
      git -C dav1d pull 2> /dev/null || git clone --depth 1 https://code.videolan.org/videolan/dav1d.git && \
      mkdir -p dav1d/build && \
      cd dav1d/build && \
      meson setup -Denable_tools=false -Denable_tests=false --default-library=static .. --prefix "/usr/local" --libdir="/usr/local/lib" && \
      ninja && \
      ninja install && \
      cd / && rm -rf /tmp/dav1d && \
      git clone --depth 1 --branch n${FFMPEG_VERSION} https://github.com/FFmpeg/FFmpeg.git /tmp/ffmpeg && \
      cd /tmp/ffmpeg && \
      export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-} && \
      export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-} && \
      ./configure \
        --prefix=/usr/local \
        --pkg-config-flags="--static" \
        --extra-cflags="-I$HOME/ffmpeg_build/include" \
        --extra-ldflags="-L$HOME/ffmpeg_build/lib" \
        --extra-libs="-lpthread -lm" \
        --ld="g++" \
        --enable-gpl \
        --enable-vaapi \
        --enable-vdpau \
        --enable-version3 \
        --enable-nonfree \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libmfx \
        --enable-gnutls \
        --enable-libaom \
        --enable-libass \
        --enable-libfdk-aac \
        --enable-libfreetype \
        --enable-libmp3lame \
        --enable-libopus \
        --enable-libdav1d \
        --enable-libvorbis \
        --enable-libvpx \
      && make -j$(nproc) \
      && make install \
      && ldconfig \
      && cd / && rm -rf /tmp/ffmpeg /tmp/ffmpeg_sources; \
    elif [ "${FFMPEG_INSTALL_METHOD}" = "static" ]; then \
      wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-${FFMPEG_VERSION}-linux64-gpl.tar.xz && \
      tar -xf ffmpeg-${FFMPEG_VERSION}-linux64-gpl.tar.xz && \
      mv ffmpeg-${FFMPEG_VERSION}-linux64-gpl /opt/ffmpeg && \
      ln -sf /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg && \
      ln -sf /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe && \
      rm ffmpeg-${FFMPEG_VERSION}-linux64-gpl.tar.xz; \
    else \
      apt-get update && \
      apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libswscale-dev \
      && rm -rf /var/lib/apt/lists/*; \
    fi

# GStreamer installation (2 methods: system, source)
# Method "source": Build GStreamer from source (needed for new versions on old distros)
#   Note: gst-libav is disabled when building from source to avoid FFmpeg API incompatibilities
#         (GStreamer 1.24.x is not compatible with FFmpeg 7+/8+ APIs)
#         Use GStreamer native decoders or FFmpeg directly for decoding.
# Method "system": Install GStreamer from system packages (default)
RUN if [ "${GSTREAMER_INSTALL_METHOD}" = "source" ]; then \
      apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        pkg-config \
        python3-pip \
        bison \
        flex \
        nasm \
        libglib2.0-dev \
        liborc-0.4-dev \
        libpthread-stubs0-dev \
        libva-dev \
        libvdpau-dev \
        libx11-dev \
        libxext-dev \
        libxv-dev \
        libdrm-dev \
        libgudev-1.0-dev \
        libasound2-dev \
        libopus-dev \
        libvorbis-dev \
        libtheora-dev \
        libvpx-dev \
        libpng-dev \
        libjpeg-dev \
      && rm -rf /var/lib/apt/lists/* \
      && pip3 install --upgrade pip setuptools meson \
      && mkdir -p /tmp/gstreamer && cd /tmp/gstreamer \
      && curl -L "https://gitlab.freedesktop.org/gstreamer/gstreamer/-/archive/${GSTREAMER_VERSION}/gstreamer-${GSTREAMER_VERSION}.tar.gz" | tar xz \
      && cd gstreamer-${GSTREAMER_VERSION} \
      && meson setup build \
        --prefix=/usr/local \
        --buildtype=release \
        -Dgpl=enabled \
        -Dugly=enabled \
        -Dvaapi=enabled \
        -Dlibav=disabled \
        -Dbase=enabled \
        -Dgood=enabled \
        -Dbad=enabled \
        -Dgst-plugins-base:gl=disabled \
        -Dgst-plugins-bad:gl=disabled \
        -Ddevtools=disabled \
        -Dges=disabled \
        -Drtsp_server=disabled \
        -Dsharp=disabled \
        -Dpython=disabled \
        -Dtests=disabled \
        -Dexamples=disabled \
        -Dintrospection=disabled \
        -Ddoc=disabled \
        -Dqt5=disabled \
        -Dqt6=disabled \
      && meson compile -C build -j$(nproc) \
      && meson install -C build \
      && ldconfig \
      && cd / && rm -rf /tmp/gstreamer \
      && apt-get purge -y 'libgstreamer*' 'gstreamer1.0-*' 2>/dev/null || true \
      && apt-get autoremove -y 2>/dev/null || true; \
    else \
      apt-get update && apt-get install -y \
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev \
        libgstreamer-plugins-bad1.0-dev \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        gstreamer1.0-tools \
        gstreamer1.0-vaapi \
        && (apt-get install -y gstreamer1.0-va || true) \
        && (apt-get install -y gstreamer1.0-msdk || true) \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Set library paths - /usr/local MUST come first to prioritize compiled versions
ENV LD_LIBRARY_PATH=/usr/local/lib/x86_64-linux-gnu:/usr/local/lib:/usr/lib/x86_64-linux-gnu \
    GST_PLUGIN_PATH=/usr/local/lib/x86_64-linux-gnu/gstreamer-1.0:/usr/local/lib/gstreamer-1.0:/usr/lib/x86_64-linux-gnu/gstreamer-1.0 \
    PKG_CONFIG_PATH=/usr/local/lib/x86_64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig \
    PATH=/usr/local/bin:/usr/bin:/bin

COPY . /fluster/

# Install Fluster
RUN pip3 install . --no-cache-dir --break-system-packages 2>/dev/null || \
    pip3 install . --no-cache-dir

RUN mkdir -p /fluster/resources /fluster/test_suites

# Additional environment variables
ENV PYTHONPATH=/fluster \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    MFX_HOME=/opt/intel/mediasdk

COPY docker/hw-info.sh /usr/local/bin/hw-info
RUN chmod +x /usr/local/bin/hw-info

CMD ["/bin/bash"]
