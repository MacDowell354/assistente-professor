# voice_utils.py
import os
import uuid
import requests
from typing import Optional
from openai import OpenAI

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default "Rachel"

client = OpenAI()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def transcribe_with_whisper(file_path: str) -> str:
    """Transcreve áudio usando OpenAI Whisper API."""
    with open(file_path, "rb") as f:
        res = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=f,
            language="pt"
        )
    return res.text if hasattr(res, "text") else str(res)

def tts_with_elevenlabs(text: str) -> Optional[str]:
    """Gera mp3 com ElevenLabs. Retorna nome do arquivo ou None se desabilitado/falhou."""
    if not ELEVEN_API_KEY:
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        return None

    filename = f"{uuid.uuid4().hex}.mp3"
    out_path = os.path.join(AUDIO_DIR, filename)
    with open(out_path, "wb") as f:
        f.write(r.content)
    return filename
