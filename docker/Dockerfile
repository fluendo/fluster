# Fluster Docker Image with FULL H.266/VVC support via vvdec
FROM python:3.11-slim-bookworm
WORKDIR /fluster
# Install ALL necessary build dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    pkg-config \
    wget \
    ca-certificates \
    yasm \
    nasm \
    ninja-build \
    meson \
    flex \
    bison \
    python3-pip \
    libssl-dev \
    libx264-dev \
    libx265-dev \
    libnuma-dev \
    libglib2.0-dev \
    libffi-dev \
    libmount-dev \
    libpcre2-dev \
    zlib1g-dev \
    liborc-0.4-dev \
    libpng-dev \
    libjpeg-dev \
    libopus-dev \
    libvorbis-dev \
    && rm -rf /var/lib/apt/lists/*
# Step 1: Build vvdec (VVC/H.266 decoder) - THE CORE COMPONENT
RUN echo "=== Building vvdec ===" && \
    git clone --depth 1 https://github.com/fraunhoferhhi/vvdec.git /tmp/vvdec && \
    cd /tmp/vvdec && \
    mkdir build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DVVDEC_INSTALL_VVDECAPP=ON \
        -DBUILD_SHARED_LIBS=ON && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/vvdec && \
    echo "vvdec installed successfully"
# Step 2: Build FFmpeg with VVC/H.266 decoder support
# Note: FFmpeg has native VVC decoder since version 6.1
RUN echo "=== Building FFmpeg with native VVC decoder ===" && \
    git clone --depth 1 --branch release/7.1 https://github.com/FFmpeg/FFmpeg.git /tmp/ffmpeg && \
    cd /tmp/ffmpeg && \
    export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-} && \
    export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-} && \
    ./configure \
        --prefix=/usr/local \
        --enable-gpl \
        --enable-version3 \
        --enable-nonfree \
        --enable-shared \
        --disable-static \
        --enable-decoder=vvc \
        --enable-libx264 \
        --enable-libx265 && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/ffmpeg && \
    echo "FFmpeg with native VVC decoder installed successfully"
# Step 3: Upgrade pip and install latest Meson
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir meson==1.5.2
# Step 4: Build GStreamer 1.26 (required for VVC/H.266 support via libav)
RUN echo "=== Building GStreamer 1.26 with full plugin support ===" && \
    git clone --depth 1 --branch 1.26.0 https://gitlab.freedesktop.org/gstreamer/gstreamer.git /tmp/gstreamer && \
    cd /tmp/gstreamer && \
    meson setup builddir \
        --prefix=/usr/local \
        --buildtype=release \
        -Dgpl=enabled \
        -Dbase=enabled \
        -Dgood=enabled \
        -Dbad=enabled \
        -Dugly=disabled \
        -Dlibav=enabled \
        -Dvaapi=disabled \
        -Dgst-plugins-base:gl=disabled \
        -Dgst-plugins-bad:nvcodec=disabled \
        -Dtests=disabled \
        -Dexamples=disabled \
        -Ddoc=disabled \
        -Dintrospection=disabled \
        -Dnls=disabled && \
    ninja -C builddir -j$(nproc) && \
    ninja -C builddir install && \
    ldconfig && \
    cd / && rm -rf /tmp/gstreamer && \
    echo "GStreamer 1.26 with VVC/H.266 support installed successfully"
# Copy Fluster source code
COPY . /fluster/
# Install Fluster
RUN cd /fluster && pip install -e . --no-cache-dir
# Create Fluster directories
RUN mkdir -p /fluster/resources /fluster/test_suites /fluster/fluster_output
# Set all necessary environment variables
ENV PYTHONPATH=/fluster:$PYTHONPATH
ENV GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0:/usr/local/lib/x86_64-linux-gnu/gstreamer-1.0
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib/x86_64-linux-gnu/pkgconfig:$PKG_CONFIG_PATH
ENV PATH=/usr/local/bin:$PATH
ENV TERM=xterm-256color
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
CMD ["/bin/bash"]
