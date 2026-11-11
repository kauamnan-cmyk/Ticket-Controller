#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive

apt update
apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-requests \
  python3-pyqt5 \
  python3-pyqt5.qtmultimedia \
  libqt5multimedia5-plugins \
  alsa-utils \
  ffmpeg

