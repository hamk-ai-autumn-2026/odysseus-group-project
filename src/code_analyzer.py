import os
import re
from typing import Any, Dict, List, Union

SUPPORTED_CODE_EXTENSIONS = {
    ".py": "python",
    ".pyi": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".hh": "cpp",
}


def detect_language(file_name: str = "", file_content: str = "") -> str:
    """Infer the source language from the filename or content."""
    ext = os.path.splitext(file_name or "")[1].lower()
    if ext in SUPPORTED_CODE_EXTENSIONS:
        return SUPPORTED_CODE_EXTENSIONS[ext]

    text = file_content.lower()
    if "def " in text and "return " in text:
        return "python"
    if "int main" in text or "std::" in text or "#include <iostream>" in text:
        return "cpp"
    if "class " in text and "public:" in text:
        return "cpp"
    return "text"


def _coerce_text(file_content: Union[str, bytes, None]) -> str:
    if file_content is None:
        return ""
    if isinstance(file_content, bytes):
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return file_content.decode("utf-8", errors="replace")
    return str(file_content)


def _normalize_lines(lines: Union[List[Dict[str, Any]], List[str], str]) -> List[Dict[str, Any]]:
    if isinstance(lines, str):
        raw = lines.splitlines()
        return [
            {
                "line_num": idx + 1,
                "text": line,
                "char_count": len(line),
                "word_count": len(re.findall(r"\S+", line)),
            }
            for idx, line in enumerate(raw)
        ]

    normalized: List[Dict[str, Any]] = []
    for idx, entry in enumerate(lines):
        if isinstance(entry, dict):
            text = str(entry.get("text", ""))
            normalized.append(
                {
                    "line_num": int(entry.get("line_num", idx + 1)),
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(re.findall(r"\S+", text)),
                }
            )
        else:
            text = str(entry)
            normalized.append(
                {
                    "line_num": idx + 1,
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(re.findall(r"\S+", text)),
                }
            )
    return normalized


def _count_comment_lines(lines: List[Dict[str, Any]]) -> int:
    patterns = ("#", "//", "/*", "*", ";")
    count = 0
    for item in lines:
        stripped = item["text"].strip()
        if not stripped:
            continue
        if stripped.startswith(patterns):
            count += 1
    return count


def _count_imports(lines: List[Dict[str, Any]], language: str) -> int:
    if language == "python":
        pattern = re.compile(r"^\s*(?:from\s+\w+\s+import\s+.*|import\s+\w+(?:\s*,\s*\w+)*)")
    elif language in {"cpp", "c"}:
        pattern = re.compile(r"^\s*#include\s*[<\"].*[>\"]")
    else:
        pattern = re.compile(r"^\s*(?:import|from|#include)\b")

    return sum(1 for item in lines if pattern.match(item["text"]))


def extract_code_data(file_content: Union[str, bytes, None], file_name: str = "snippet.py") -> Dict[str, Any]:
    """Parse a source file and return summary metadata and structure info."""
    text = _coerce_text(file_content)
    language = detect_language(file_name, text)
    lines = _normalize_lines(text)
    non_empty_lines = [line for line in lines if line["text"].strip()]

    function_pattern = re.compile(
        r"^\s*(?:async\s+)?(?:def\s+[A-Za-z_][\w]*|function\s+[A-Za-z_][\w]*|[A-Za-z_][\w*\s&:<>]*\s+[A-Za-z_][\w]*\s*\(.*\))\s*(?::|\{)",
        re.MULTILINE,
    )
    class_pattern = re.compile(r"^\s*(?:class|struct)\s+[A-Za-z_][\w]*", re.MULTILINE)

    metrics = {
        "language": language,
        "file_name": file_name,
        "total_lines": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "comment_lines": _count_comment_lines(lines),
        "import_count": _count_imports(lines, language),
        "function_count": len(function_pattern.findall(text)),
        "class_count": len(class_pattern.findall(text)),
        "total_chars": len(text),
        "total_words": len(re.findall(r"\S+", text)),
    }

    return {
        "file_name": file_name,
        "language": language,
        "full_text": text.strip(),
        "lines": lines,
        "metrics": metrics,
        "total_lines": len(lines),
        "total_words": metrics["total_words"],
        "total_chars": metrics["total_chars"],
    }


def chunk_code_lines(lines: Union[List[Dict[str, Any]], List[str]], max_chars: int = 3500, overlap: int = 200) -> List[Dict[str, Any]]:
    """Split code into manageable chunks while preserving line order."""
    entries = _normalize_lines(lines)
    if not entries:
        return []

    chunks: List[Dict[str, Any]] = []
    current_lines: List[Dict[str, Any]] = []
    current_text = ""
    chunk_id = 1

    def push_chunk() -> None:
        nonlocal chunk_id
        if not current_text.strip():
            return
        start_line = current_lines[0]["line_num"]
        end_line = current_lines[-1]["line_num"]
        chunks.append(
            {
                "chunk_id": chunk_id,
                "line_range": f"Lines {start_line}-{end_line}",
                "start_line": start_line,
                "end_line": end_line,
                "text": current_text.strip(),
            }
        )
        chunk_id += 1

    for entry in entries:
        if not entry["text"].strip():
            continue

        candidate = (current_text + ("\n" if current_text else "") + entry["text"]).strip()
        if current_text and len(candidate) > max_chars:
            push_chunk()
            current_lines = []
            current_text = ""

        current_lines.append(entry)
        current_text = "\n".join(item["text"] for item in current_lines).strip()

    if current_text.strip():
        push_chunk()

    return chunks


def search_in_code(lines: Union[List[Dict[str, Any]], List[str]], query: str) -> List[Dict[str, Any]]:
    """Search code content for matches and return matching lines with snippets."""
    if not query or not str(query).strip():
        return []

    entries = _normalize_lines(lines)
    if not entries:
        return []

    q_lower = str(query).lower()
    matches: List[Dict[str, Any]] = []
    for entry in entries:
        text = entry["text"]
        lowered = text.lower()
        if q_lower not in lowered:
            continue

        pos = lowered.find(q_lower)
        start = max(0, pos - 40)
        end = min(len(text), pos + len(query) + 40)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        matches.append(
            {
                "line_num": entry["line_num"],
                "snippet": snippet,
                "matches_on_line": lowered.count(q_lower),
            }
        )

    return matches


def analyze_code(file_content: Union[str, bytes, None], file_name: str = "snippet.py") -> Dict[str, Any]:
    """Convenience wrapper for code analysis."""
    data = extract_code_data(file_content, file_name)
    metrics = data["metrics"]
    summary = (
        f"{data['language'].title()} file with {metrics['total_lines']} lines, "
        f"{metrics['function_count']} functions, {metrics['class_count']} classes, and "
        f"{metrics['import_count']} imports."
    )
    return {**data, "summary": summary}
