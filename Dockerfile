# Build image for padavan-builder-workflow (beta).
#
# Purpose: self-hosted replacement for registry.gitlab.com/hadzhioglu/padavan-ng.
# This is an exact copy of the upstream toolchain image (same base ubuntu:22.04 and
# the same apt package set, see https://gitlab.com/hadzhioglu/padavan-ng Dockerfile)
# PLUS gcc-multilib. Rationale: building LuaJIT from the git branch v2.1 compiles
# 32-bit host tools (HOST_CC="gcc -m32"), which needs the i386 libc headers that the
# published GitLab image lacks. Without them the firmware build fails with:
#   host/buildvm.h:9:10: fatal error: sys/types.h: No such file or directory
#
# Keep the package list in sync with the upstream image. Adding a package is safe for
# the firmware build; do not drop one that upstream relies on.

FROM ubuntu:22.04

ENV PROJECT="padavan-ng"
ENV PROJECT_REPO="https://gitlab.com/hadzhioglu/${PROJECT}.git" \
    BASE_DIR="/opt" \
    DEBIAN_FRONTEND="noninteractive"

RUN apt update && \
    apt upgrade -y && \
    apt install --no-install-recommends -y \
        autoconf \
        autoconf-archive \
        automake \
        autopoint \
        bison \
        build-essential \
        ca-certificates \
        cmake \
        cpio \
        curl \
        dos2unix \
        doxygen \
        fakeroot \
        flex \
        gawk \
        gcc-multilib \
        gettext \
        git \
        gperf \
        help2man \
        kmod \
        libarchive-tools \
        libblkid-dev \
        libc-ares-dev \
        libcurl4-openssl-dev \
        libdevmapper-dev \
        libev-dev \
        libevent-dev \
        libexif-dev \
        libflac-dev \
        libgmp3-dev \
        libid3tag0-dev \
        libidn2-dev \
        libjpeg-dev \
        libkeyutils-dev \
        libltdl-dev \
        libmpc-dev \
        libmpfr-dev \
        libncurses5-dev \
        libogg-dev \
        libsqlite3-dev \
        libssl-dev \
        libsystemd-dev \
        libtool \
        libtool-bin \
        libudev-dev \
        libunbound-dev \
        libvorbis-dev \
        libxml2-dev \
        locales \
        nano \
        pkg-config \
        ppp-dev \
        python3 \
        python3-docutils \
        texinfo \
        unzip \
        uuid \
        uuid-dev \
        vim \
        wget \
        xxd \
        zlib1g-dev \
        zstd && \
    locale-gen --no-purge en_US.UTF-8 ru_RU.UTF-8 && \
    apt clean && \
    apt-get clean && \
    find /var/lib/apt/lists -mindepth 1 -delete && \
    find /tmp -mindepth 1 -delete && \
    find /var/tmp -mindepth 1 -delete

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

WORKDIR "$BASE_DIR"
