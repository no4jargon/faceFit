#!/bin/bash

set -e

# update apt and install the OpenGL runtime + common native deps
apt-get update && \
apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 && \
rm -rf /var/lib/apt/lists/*