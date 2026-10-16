import io
import logging
import os
import re
import threading
import urllib.request
import wave
from pathlib import Path
from typing import Optional

from piper.voice import PiperVoice

logger = logging.getLogger(__name__)

# Base directory for local models
DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "piper"

VOICE_CONFIGS = {
    "en": {
        "model_file": "en_US-lessac-medium.onnx",
        "config_file": "en_US-lessac-medium.onnx.json",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
    "fi": {
        "model_file": "fi_FI-harri-medium.onnx",
        "config_file": "fi_FI-harri-medium.onnx.json",
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fi/fi_FI/harri/medium/fi_FI-harri-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fi/fi_FI/harri/medium/fi_FI-harri-medium.onnx.json",
    },
}

_VOICE_CACHE: dict[str, PiperVoice] = {}
_VOICE_LOCK = threading.Lock()


def clean_text_for_tts(text: Optional[str]) -> str:
    """
    Cleans markdown formatting, code blocks, URLs, and syntax characters
    from text to make it suitable and natural for Text-to-Speech synthesis.
    """
    if not text:
        return ""

    # 1. Remove code blocks
    cleaned = re.sub(r"```[\s\S]*?```", "", text)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # 2. Remove Markdown links [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)

    # 3. Remove standalone URLs
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)

    # 4. Remove Markdown headings (e.g., #, ##, ###)
    cleaned = re.sub(r"^\s*#{1,6}\s+", "", cleaned, flags=re.MULTILINE)

    # 5. Remove bold/italic formatting (**text**, *text*, __text__, _text_)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)

    # 6. Remove blockquotes and horizontal rules
    cleaned = re.sub(r"^\s*>\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)

    # 7. Convert list markers (- item, * item, 1. item) to clean sentences
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)

    # 8. Normalize whitespace and extra newlines
    cleaned = re.sub(r"\n{2,}", ". ", cleaned)
    cleaned = re.sub(r"\n", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    return cleaned.strip()


def ensure_voice_model(lang_code: str = "en", models_dir: Optional[Path] = None) -> tuple[Path, Path]:
    """
    Ensures that the Piper ONNX voice model and config files exist locally.
    Downloads them on-demand from HuggingFace if not already cached.
    """
    if lang_code not in VOICE_CONFIGS:
        lang_code = "en"

    dest_dir = models_dir or DEFAULT_MODELS_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    config = VOICE_CONFIGS[lang_code]
    model_path = dest_dir / config["model_file"]
    config_path = dest_dir / config["config_file"]

    # Download config if missing
    if not config_path.exists():
        logger.info("Downloading Piper voice config for %s to %s", lang_code, config_path)
        urllib.request.urlretrieve(config["config_url"], config_path)

    # Download ONNX model weights if missing
    if not model_path.exists():
        logger.info("Downloading Piper voice model for %s to %s", lang_code, model_path)
        urllib.request.urlretrieve(config["model_url"], model_path)

    return model_path, config_path


def get_piper_voice(lang_code: str = "en", models_dir: Optional[Path] = None) -> PiperVoice:
    """
    Retrieves or initializes a cached PiperVoice instance for the given language.
    """
    if lang_code not in VOICE_CONFIGS:
        lang_code = "en"

    with _VOICE_LOCK:
        if lang_code in _VOICE_CACHE:
            return _VOICE_CACHE[lang_code]

        model_path, config_path = ensure_voice_model(lang_code, models_dir=models_dir)
        voice = PiperVoice.load(str(model_path), config_path=str(config_path))
        _VOICE_CACHE[lang_code] = voice
        return voice


def generate_tts_audio_bytes(text: Optional[str], language: str = "Same as Document") -> bytes:
    """
    Generates high-quality, 100% offline neural WAV audio bytes using Piper TTS.
    Supports English ('en') and Finnish ('fi').
    """
    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        return b""

    lang_code = "fi" if language == "Finnish" else "en"

    # Truncate if extremely long to avoid high latency (up to 3000 chars)
    if len(cleaned_text) > 3000:
        cleaned_text = cleaned_text[:3000] + "..."

    voice = get_piper_voice(lang_code)

    buf = io.BytesIO()
    with _VOICE_LOCK:
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(cleaned_text, wav_file)

    return buf.getvalue()
