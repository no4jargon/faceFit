#!/usr/bin/env bash
set -e

# If you have any other system libs you truly need, install them here.
# But for MediaPipe + headless OpenCV, you don't need libGL at all.

# Example (only if you later add a native lib):
# apt-get update && \
# apt-get install -y --no-install-recommends \
#     libglib2.0-0 && \
#     rm -rf /var/lib/apt/lists/*

# Now install your Python deps
pip install --no-cache-dir -r requirements.txt