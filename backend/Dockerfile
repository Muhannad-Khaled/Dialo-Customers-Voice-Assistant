FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Minimal system deps. STT is now the Groq API (no local Whisper/ffmpeg); Piper
# writes WAV via Python's `wave`; LiveKit's audio codecs ship in the Python wheels.
# `curl` is only needed for the compose healthcheck. (Add `ffmpeg libsndfile1` back
# here if you switch STT back to a local model.)
# Retries + IPv4 + timeout make the layer resilient to transient mirror hiccups.
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/99retries && \
    apt-get update -o Acquire::http::Timeout=60 && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Cache-mount keeps downloaded wheels (incl. the ~500MB torch) across builds, so an
# interrupted build resumes instead of re-downloading everything on a slow connection.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout 120 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
