import pytest
from src.tts import clean_text_for_tts, generate_tts_audio_bytes, ensure_voice_model


def test_clean_text_for_tts_empty():
    assert clean_text_for_tts("") == ""
    assert clean_text_for_tts(None) == ""


def test_clean_text_for_tts_markdown():
    raw_md = """
    # Executive Summary

    This is a **crucial** document about *AI models*.
    
    - Point 1: Check out [our website](https://example.com)
    - Point 2: Code sample `print('hello')`
    
    > Important note here.
    """
    cleaned = clean_text_for_tts(raw_md)
    assert "#" not in cleaned
    assert "**" not in cleaned
    assert "https://example.com" not in cleaned
    assert "[our website]" not in cleaned
    assert "our website" in cleaned
    assert "crucial" in cleaned
    assert "AI models" in cleaned
    assert "print('hello')" in cleaned


def test_generate_tts_audio_bytes_empty():
    assert generate_tts_audio_bytes("") == b""
    assert generate_tts_audio_bytes(None) == b""


def test_generate_tts_audio_bytes_english():
    wav_bytes = generate_tts_audio_bytes("This is a quick test of local Piper synthesis.", language="English")
    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 1000
    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"


def test_generate_tts_audio_bytes_finnish():
    wav_bytes = generate_tts_audio_bytes("Tämä on testi suomenkielisestä synteesistä.", language="Finnish")
    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 1000
    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"


def test_ensure_voice_model_fallback():
    model_path, config_path = ensure_voice_model("unknown_lang")
    assert model_path.exists()
    assert config_path.exists()
    assert "en_US" in model_path.name
