# SpikeClip web API: accounts, Paddle payments and licence keys.
# A few MB, no video tooling: clipping runs in the desktop app on the user's PC.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 api && mkdir -p /app/data && chown api /app/data
USER api
EXPOSE 8080
# $PORT is set by Render, Railway, Fly and Cloud Run.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips=*"]
