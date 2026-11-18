#!/bin/sh
# Make the data disk writable by the app's user, then run as that user.
#
# Cloud disks are mounted over /data when the container starts, owned by
# root, so the chown done while building the image no longer applies.
set -e
DATA="${SPIKECLIP_DATA_DIR:-/data}"

# Model downloads (Whisper, YOLO, Hugging Face) go to the disk too, so a
# redeploy does not fetch gigabytes again.
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$DATA/cache}"
export HF_HOME="${HF_HOME:-$XDG_CACHE_HOME/huggingface}"
export TORCH_HOME="${TORCH_HOME:-$XDG_CACHE_HOME/torch}"

if [ "$(id -u)" = "0" ]; then
    mkdir -p "$DATA" "$XDG_CACHE_HOME"
    chown spikeclip:spikeclip "$DATA" "$XDG_CACHE_HOME"
    export HOME=/home/spikeclip
    exec setpriv --reuid=spikeclip --regid=spikeclip --init-groups "$@"
fi
exec "$@"
