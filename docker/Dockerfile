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

# A user is required by Ubuntu 24.04 to install meson as non-root
ARG USERNAME='mock'
ARG PASSWORD='mock'

ARG ARCH=x86_64
ARG CARGO_C_VERSION=v0.10.23

# Re-declare args after FROM to make them available in build stages
ARG UBUNTU_VERSION
ARG NVIDIA_DRIVER_VERSION
# FFmpeg installation method: "system" (default), "static", "source"
ARG FFMPEG_INSTALL_METHOD=system
# FFmpeg version for "source" method
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
    sudo \
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
    mesa-va-drivers \
    && (apt-get install -y i965-va-driver || true) \
    && (apt-get install -y intel-media-va-driver-non-free || \
        apt-get install -y intel-media-va-driver || true) \
    && rm -rf /var/lib/apt/lists/*

# VAAPI driver for NVIDIA (Ubuntu 24.04+)
# apt's nvidia-vaapi-driver defaults to the broken EGL backend (driver >=525,
# elFarto/nvidia-vaapi-driver#207). Build from source instead (direct backend).
RUN if [ "${UBUNTU_VERSION}" = "24.04" ]; then \
        apt-get update && \
        apt-get install -y meson ninja-build git pkg-config \
            libegl1-mesa-dev libgstreamer-plugins-bad1.0-dev && \
        apt-mark manual libunwind8 libdw1t64 && \
        git clone --depth 1 --branch n12.2.72.0 https://github.com/FFmpeg/nv-codec-headers.git /tmp/nv-codec-headers && \
        make -C /tmp/nv-codec-headers install && \
        git clone --depth 1 --branch v0.0.17 https://github.com/elFarto/nvidia-vaapi-driver.git /tmp/nvidia-vaapi-driver && \
        meson setup /tmp/nvidia-vaapi-driver/build /tmp/nvidia-vaapi-driver --prefix=/usr --libdir=lib/x86_64-linux-gnu && \
        ninja -C /tmp/nvidia-vaapi-driver/build install && \
        rm -rf /tmp/nv-codec-headers /tmp/nvidia-vaapi-driver && \
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
        apt-get update \
        && apt-get install -y \
            libnvidia-decode-${NVIDIA_DRIVER_VERSION} \
            libnvidia-encode-${NVIDIA_DRIVER_VERSION} \
            nvidia-utils-${NVIDIA_DRIVER_VERSION} \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Intel QuickSync support via Media SDK and oneVPL (x86_64 only)
RUN apt-get update \
  && (apt-get install -y libmfx1 libmfx-tools || true) \
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
        libssl-dev \
        libpango1.0-dev \
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
      export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib/${ARCH}-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-} && \
      export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/${ARCH}-linux-gnu:${LD_LIBRARY_PATH:-} && \
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
      wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
      tar -xf ffmpeg-release-amd64-static.tar.xz && \
      mv ffmpeg-*-amd64-static /opt/ffmpeg && \
      ln -sf /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg && \
      ln -sf /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe && \
      rm ffmpeg-release-amd64-static.tar.xz; \
    else \
      apt-get update && \
      apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-dev \
        libavfilter-dev \
        libavformat-dev \
        libavutil-dev \
        libswresample-dev \
        libswscale-dev \
      && rm -rf /var/lib/apt/lists/*; \
    fi

# Update python packages depending on Ubuntu version
RUN if [ "${GSTREAMER_INSTALL_METHOD}" = "source" ]; then \
      if [ "${UBUNTU_VERSION}" = "24.04" ]; then \
        pip3 install --upgrade pip setuptools; \
        apt update && apt install -y pipx ninja-build && rm -rf /var/lib/apt/lists/*; \
      else \
        pip3 install --upgrade pip setuptools meson; \
      fi; \
    fi


# Ubuntu 24.04: Remove default user
RUN if [ "${UBUNTU_VERSION}" = "24.04" ] && id ubuntu >/dev/null 2>&1; then \
      userdel -r ubuntu; \
    fi

# Create USERNAME user and add it to sudoers without password
RUN addgroup ${USERNAME} && \
    useradd -rm -s /bin/bash -m -g ${USERNAME} -u 1000 -G sudo ${USERNAME} && \
    echo ${USERNAME}':'${PASSWORD} | chpasswd && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers;

# Change to USERNAME user
USER ${USERNAME}

# Set PATH to include pipx bin directory - required for meson in Ubuntu 24.04
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Ubuntu 24.04: install python packages for non-root user
RUN if [ "${GSTREAMER_INSTALL_METHOD}" = "source" ] && [ "${UBUNTU_VERSION}" = "24.04" ]; then \
      echo "export PATH=/home/${USERNAME}/.local/bin:\${PATH}" >> /home/${USERNAME}/.bashrc; \
      pipx install meson==1.6.1; \
    fi

# GStreamer installation (2 methods: system, source)
# Method "source": Build GStreamer from source (needed for new versions on old distros)
# Method "system": Install GStreamer from system packages (default)
RUN if [ "${GSTREAMER_INSTALL_METHOD}" = "source" ]; then \
      sudo apt-get update && sudo apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        pkg-config \
        python3-pip \
        bison \
        flex \
        nasm \
        libglib2.0-dev \
        # To avoid 1.24.12 compilation error
        libsysprof-capture-4-dev \
        # To avoid 1.24.12 runtime error
        libsqlite3-dev \
        liborc-0.4-dev \
        libpthread-stubs0-dev \
        libva-dev \
        libvdpau-dev \
        libmfx-dev \
        libx11-dev \
        libxext-dev \
        libxv-dev \
        libx11-xcb-dev \
        libdrm-dev \
        libgudev-1.0-dev \
        libasound2-dev \
        libopus-dev \
        libvorbis-dev \
        libtheora-dev \
        libvpx-dev \
        libpng-dev \
        libjpeg-dev \
        libxml2-dev \
        libegl1-mesa-dev \
        libgles2-mesa-dev \
        libgl1-mesa-dev \
        libglu1-mesa-dev \
      && sudo rm -rf /var/lib/apt/lists/* \
      && mkdir -p /tmp/gstreamer && cd /tmp/gstreamer \
      && curl -L "https://gitlab.freedesktop.org/gstreamer/gstreamer/-/archive/${GSTREAMER_VERSION}/gstreamer-${GSTREAMER_VERSION}.tar.gz" | tar xz \
      && cd gstreamer-${GSTREAMER_VERSION} \
      # Dynamically assign -Dvaapi=enabled for ANY version < 1.28 \
      && GST_MINOR=$(echo ${GSTREAMER_VERSION} | cut -d. -f2) \
      && if [ "$GST_MINOR" -lt 28 ]; then \
           VAAPI_OPT="-Dvaapi=enabled"; \
         else \
           VAAPI_OPT=""; \
         fi \
      && if [ "${FFMPEG_INSTALL_METHOD}" = "static" ]; \
         then \
           FFMPEG_FALLBACK="--force-fallback-for=FFmpeg,libavcodec,libavformat,libavutil,libavfilter,libswscale,libswresample"; \
         else \
           FFMPEG_FALLBACK=""; \
         fi \
      && PKG_CONFIG_PATH="/usr/local/lib/${ARCH}-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/${ARCH}-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}" \
         LD_LIBRARY_PATH="/usr/local/lib/${ARCH}-linux-gnu:/usr/local/lib:/usr/lib/${ARCH}-linux-gnu:${LD_LIBRARY_PATH:-}" \
        meson setup build \
        --prefix=/usr/local \
        --buildtype=release \
        -Dgpl=enabled \
        -Dugly=enabled \
        ${VAAPI_OPT} \
        ${FFMPEG_FALLBACK} \
        -Dlibav=enabled \
        -Dbase=enabled \
        -Dgood=enabled \
        -Dbad=enabled \
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
      && meson compile -C build -j$(nproc) \
      && sudo ninja install -C build \
      && sudo ldconfig \
      && cd / && rm -rf /tmp/gstreamer \
      && sudo apt-get purge -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev 2>/dev/null || true; \
    else \
      sudo DEBIAN_FRONTEND=noninteractive apt-get update && \
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
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
        && (sudo apt-get install -y gstreamer1.0-va || true) \
        && (sudo apt-get install -y gstreamer1.0-msdk || true) \
        && sudo rm -rf /var/lib/apt/lists/*; \
    fi

USER root

# =========================================================================
# Conditionally Install Native vvdec Core, Rust & Build GStreamer Plugins
# =========================================================================
RUN if [ "${GSTREAMER_INSTALL_METHOD}" = "source" ]; then \
      GST_MINOR=$(echo ${GSTREAMER_VERSION} | cut -d. -f2) && \
      if [ "$GST_MINOR" -ge 26 ]; then \
        # Dynamically scope the Rust home paths to this conditional execution context \
        export CARGO_HOME="/usr/local/.cargo" && \
        export RUSTUP_HOME="/usr/local/.rustup" && \
        export PATH="${CARGO_HOME}/bin:${PATH}" && \
        \
        # 1. Ensure OpenSSL development headers are present for the Rust compilation \
        apt-get update && apt-get install -y --no-install-recommends \
          libssl-dev \
          clang \
          libclang-dev \
        && rm -rf /var/lib/apt/lists/* && \
        \
        # 2. Clone, build, and install the native Fraunhofer HHI VVC Decoder core \
        git clone --depth 1 --branch v3.1.0 https://github.com/fraunhoferhhi/vvdec.git /tmp/vvdec && \
        cd /tmp/vvdec && \
        mkdir build && cd build && \
        cmake -DCMAKE_BUILD_TYPE=Release \
              -DBUILD_SHARED_LIBS=ON \
              -DCMAKE_INSTALL_PREFIX=/usr/local \
              -DCMAKE_INSTALL_LIBDIR=lib/${ARCH}-linux-gnu .. && \
        make -j$(nproc) && \
        make install && \
        ldconfig && \
        cd / && rm -rf /tmp/vvdec && \
        \
        # 3. Configure Cargo network optimizations \
        mkdir -p ${CARGO_HOME} && \
        echo '[net]\ngit-fetch-with-cli = true' > ${CARGO_HOME}/config && \
        \
        # 4. Install Rust toolchain environment \
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path && \
        \
        # 5. Extract pre-compiled cargo-c binaries directly to skip compilation errors \
        curl -L "https://github.com/lu-zero/cargo-c/releases/download/${CARGO_C_VERSION}/cargo-c-${ARCH}-unknown-linux-musl.tar.gz" | tar -xz -C ${CARGO_HOME}/bin && \
        chmod -R 777 ${CARGO_HOME} && \
        \
        # 6. Map GStreamer core versions to their matching Rust plugins stable branch \
        case "$GST_MINOR" in \
          "26") RS_BRANCH="0.14" ;; \
          "28") RS_BRANCH="0.15" ;; \
          *)    RS_BRANCH="main" ;; \
        esac && \
        \
        # 7. Clone and build the targeted stable gst-plugins-rs branch \
        export PKG_CONFIG_PATH="/usr/local/lib/${ARCH}-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/${ARCH}-linux-gnu/pkgconfig:/usr/share/pkgconfig:${PKG_CONFIG_PATH:-}" && \
        git clone --depth 1 --branch ${RS_BRANCH} https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git /tmp/gst-plugins-rs && \
        cd /tmp/gst-plugins-rs && \
        cargo cinstall -p gst-plugin-vvdec --prefix=/usr/local --libdir=/usr/local/lib/${ARCH}-linux-gnu && \
        \
        # 8. Refresh loader runtime cache and run post-build cleanup \
        ldconfig && \
        rm -rf /tmp/gst-plugins-rs ${RUSTUP_HOME} ${CARGO_HOME}; \
      else \
        echo "GStreamer version 1.${GST_MINOR} does not natively support the vvdec plugin. Skipping compilation smoothly."; \
      fi; \
    fi

# Set library paths - /usr/local MUST come first to prioritize compiled versions
ENV LD_LIBRARY_PATH=/usr/local/lib/${ARCH}-linux-gnu:/usr/local/lib:/usr/lib/${ARCH}-linux-gnu \
    GST_PLUGIN_PATH=/usr/local/lib/${ARCH}-linux-gnu/gstreamer-1.0:/usr/local/lib/gstreamer-1.0:/usr/lib/${ARCH}-linux-gnu/gstreamer-1.0 \
    PKG_CONFIG_PATH=/usr/local/lib/${ARCH}-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/${ARCH}-linux-gnu/pkgconfig \
    PATH=/usr/local/bin:/usr/bin:/bin

COPY . /fluster/

# Install Fluster
RUN pip3 install . --no-cache-dir --break-system-packages 2>/dev/null || \
    pip3 install . --no-cache-dir

RUN mkdir -p /fluster/resources /fluster/test_suites

# Additional environment variables
ENV PYTHONPATH=/fluster \
    LIBVA_DRIVERS_PATH=/usr/lib/${ARCH}-linux-gnu/dri \
    VDPAU_DRIVER_PATH=/usr/lib/${ARCH}-linux-gnu/vdpau \
    MFX_HOME=/opt/intel/mediasdk \
    NVD_BACKEND=direct \
    GST_VA_ALL_DRIVERS=1 \
    GST_VAAPI_ALL_DRIVERS=1

RUN echo "export DISPLAY=:0" >> /home/"${USERNAME}"/.profile

# sshd doesn't inherit Docker's ENV in login sessions; SetEnv fixes that.
RUN echo "SetEnv NVD_BACKEND=direct GST_VA_ALL_DRIVERS=1 GST_VAAPI_ALL_DRIVERS=1 DISPLAY=:0 \
    LIBVA_DRIVERS_PATH=/usr/lib/${ARCH}-linux-gnu/dri VDPAU_DRIVER_PATH=/usr/lib/${ARCH}-linux-gnu/vdpau" \
    >> /etc/ssh/sshd_config

COPY docker/hw-info.sh /usr/local/bin/hw-info
RUN chmod +x /usr/local/bin/hw-info

CMD ["/bin/bash"]
