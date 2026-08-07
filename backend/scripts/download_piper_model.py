"""
Script to download the Piper TTS en_US-lessac-medium voice model.
Run once inside the backend container:
  python scripts/download_piper_model.py
"""

import os
import urllib.request

MODEL_DIR = os.getenv("PIPER_MODEL_DIR", "/app/tts_models")
VOICE = "en_US-lessac-medium"
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"

FILES = [
    f"{VOICE}.onnx",
    f"{VOICE}.onnx.json",
]

os.makedirs(MODEL_DIR, exist_ok=True)

for fname in FILES:
    dest = os.path.join(MODEL_DIR, fname)
    if os.path.exists(dest):
        print(f"✓ Already exists: {dest}")
        continue
    url = f"{BASE_URL}/{fname}"
    print(f"Downloading {url} → {dest}")
    urllib.request.urlretrieve(url, dest)
    print(f"✓ Downloaded {fname}")

print("Done! Piper model ready.")
