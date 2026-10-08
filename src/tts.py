import io
import re
from gtts import gTTS

def clean_text_for_tts(text: str) -> str:
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

def generate_tts_audio_bytes(text: str, language: str = "Same as Document") -> bytes:
    """
    Generates high-quality MP3 audio bytes using gTTS.
    Supports English ('en') and Finnish ('fi').
    """
    cleaned_text = clean_text_for_tts(text)
    if not cleaned_text:
        return b""
    
    lang_code = "en"
    if language == "Finnish":
        lang_code = "fi"
    elif language == "English":
        lang_code = "en"
    
    # Truncate if extremely long to avoid timeouts (up to 3000 chars)
    if len(cleaned_text) > 3000:
        cleaned_text = cleaned_text[:3000] + "..."

    fp = io.BytesIO()
    tts = gTTS(text=cleaned_text, lang=lang_code, slow=False)
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()
