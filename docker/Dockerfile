# Fluster Docker Image with Hardware Acceleration Support
# Supports VAAPI, VDPAU, NVDEC, and Intel QuickSync

ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

# FFmpeg installation options
ARG FFMPEG_STATIC_VERSION=""
ARG BUILD_FFMPEG_FROM_SOURCE=""
ARG FFMPEG_VERSION="8.0"

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /fluster

# Base dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ca-certificates \
    software-properties-common \
    python3 \
    python3-pip \
    python3-venv \
    pciutils \
    && rm -rf /var/lib/apt/lists/*

# VAAPI support
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
        (apt-get install -y nvidia-vaapi-driver || true) && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# VDPAU support
RUN apt-get update && apt-get install -y \
    libvdpau-dev \
    libvdpau1 \
    vdpauinfo \
    libvdpau-va-gl1 \
    mesa-vdpau-drivers \
    && (apt-get install -y libnvidia-decode-535 libnvidia-encode-535 || true) \
    && rm -rf /var/lib/apt/lists/*

# Intel QuickSync support
RUN apt-get update && apt-get install -y \
    libmfx1 \
    libmfx-tools \
    && (apt-get install -y libmfx-gen1.2 || true) \
    && (apt-get install -y libvpl-dev libvpl2 || true) \
    && rm -rf /var/lib/apt/lists/*

# FFmpeg installation (3 options)
RUN if [ -n "${BUILD_FFMPEG_FROM_SOURCE}" ]; then \
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
        libaom-dev \
        libdav1d-dev \
        libunistring-dev \
      && rm -rf /var/lib/apt/lists/* && \
      git clone --depth 1 --branch n${FFMPEG_VERSION} https://github.com/FFmpeg/FFmpeg.git /tmp/ffmpeg && \
      cd /tmp/ffmpeg && \
      export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-} && \
      export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-} && \
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
      && cd / && rm -rf /tmp/ffmpeg; \
    elif [ -n "${FFMPEG_STATIC_VERSION}" ]; then \
      wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-${FFMPEG_STATIC_VERSION}-linux64-gpl.tar.xz && \
      tar -xf ffmpeg-${FFMPEG_STATIC_VERSION}-linux64-gpl.tar.xz && \
      mv ffmpeg-${FFMPEG_STATIC_VERSION}-linux64-gpl /opt/ffmpeg && \
      ln -sf /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg && \
      ln -sf /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe && \
      rm ffmpeg-${FFMPEG_STATIC_VERSION}-linux64-gpl.tar.xz; \
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

# GStreamer
RUN apt-get update && apt-get install -y \
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
    && rm -rf /var/lib/apt/lists/*

COPY . /fluster/

# Install Fluster
RUN python3 -m pip --version && \
    (pip3 install -e . --no-cache-dir --break-system-packages 2>/dev/null || \
     (pip3 install --upgrade pip setuptools wheel && pip3 install -e . --no-cache-dir))

RUN mkdir -p /fluster/resources /fluster/test_suites

# Environment variables
ENV PYTHONPATH=/fluster \
    GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0 \
    LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu \
    PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig \
    PATH=/usr/local/bin:/usr/bin:/bin \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    MFX_HOME=/opt/intel/mediasdk

COPY docker/hw-info.sh /usr/local/bin/hw-info
RUN chmod +x /usr/local/bin/hw-info

CMD ["/bin/bash"]
