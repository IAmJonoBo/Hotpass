#!/usr/bin/env bash
# Helper to run uv commands with caches on the external SSD volume.

set -euo pipefail

export UV_DATA_DIR="/Volumes/APFS Space/.uv-data"
export UV_CACHE_DIR="/Volumes/APFS Space/.uv-cache"

exec "$@"
