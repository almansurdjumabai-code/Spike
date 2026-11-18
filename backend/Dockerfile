# SpikeClip backend: the Python engine (download, transcription, scoring,
# video cutting and rendering) and its HTTP/WebSocket API.
#
# Build from this folder:  docker build -t spikeclip-backend backend/
#
# The same image serves two purposes:
#   - cloud deployment (Render, Railway, Fly.io, Cloud Run, a VPS): set
#     SPIKECLIP_API_TOKEN, SPIKECLIP_CORS_ORIGINS and SPIKECLIP_ALLOWED_HOSTS,
#     see backend/.env.example and DEPLOY.md;
#   - a contributor environment via the root docker-compose.yml.
#
# CPU only. GPU rendering needs a CUDA base image and the NVIDIA runtime;
# DEPLOY.md explains the variant.

FROM python:3.11-slim

# ffmpeg      — every decode, encode and probe in the pipeline
# libgl1 etc. — OpenCV imports fail without them on slim images
# git         — yt-dlp and some tooling shell out to it
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU PyTorch FIRST, so the requirements below resolve against it rather
# than pulling ~4 GB of CUDA wheels.
COPY requirements.txt requirements-build.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir ruff pytest

COPY . .

# The image holds only backend/, so the app version (kept in
# frontend/package.json) is passed in at build time.
ARG SPIKECLIP_VERSION=dev
ENV SPIKECLIP_VERSION=${SPIKECLIP_VERSION} \
    SPIKECLIP_DATA_DIR=/data \
    SPIKECLIP_HOST=0.0.0.0 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

# Downloads, clips and the database live on a volume, never in the image.
RUN useradd --create-home --uid 10001 spikeclip \
    && mkdir -p /data && chown spikeclip:spikeclip /data /app
USER spikeclip
VOLUME ["/data"]

EXPOSE 8765

# $PORT is honoured when the platform sets it (main.py serve reads it).
# Without SPIKECLIP_API_TOKEN the server refuses to bind 0.0.0.0, unless
# SPIKECLIP_INSECURE_NO_AUTH=1 (local Docker only).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8765\")}/health', timeout=4)" || exit 1

CMD ["python", "main.py", "serve"]
