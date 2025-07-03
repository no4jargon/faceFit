#!/bin/bash
set -e

# update and install a generic libGL plus GLib
apt-get update && \
apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 && \
rm -rf /var/lib/apt/lists/*