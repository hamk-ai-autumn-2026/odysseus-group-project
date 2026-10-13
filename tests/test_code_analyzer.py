from pathlib import Path

import pytest

from src.code_analyzer import extract_code_data, chunk_code_lines, search_in_code
from src.pdf_processor import extract_document_data


ROOT = Path(__file__).resolve().parents[1]
TESTDOCS = ROOT / "testdocs"


def test_extract_code_data_python_and_cpp():
    python_code = (TESTDOCS / "sample_python.py").read_text(encoding="utf-8")
    cpp_code = (TESTDOCS / "sample_cpp.cpp").read_text(encoding="utf-8")

    python_data = extract_code_data(python_code, "sample_python.py")
    cpp_data = extract_code_data(cpp_code, "sample_cpp.cpp")

    assert python_data["language"] == "python"
    assert python_data["metrics"]["function_count"] >= 1
    assert cpp_data["language"] == "cpp"
    assert cpp_data["metrics"]["function_count"] >= 1


def test_extract_document_data_supports_code_files():
    python_bytes = (TESTDOCS / "sample_python.py").read_bytes()
    cpp_bytes = (TESTDOCS / "sample_cpp.cpp").read_bytes()

    python_data = extract_document_data(python_bytes, "sample_python.py")
    cpp_data = extract_document_data(cpp_bytes, "sample_cpp.cpp")

    assert python_data["total_pages"] == 1
    assert python_data["language"] == "python"
    assert cpp_data["total_pages"] == 1
    assert cpp_data["language"] == "cpp"


def test_chunk_and_search_code():
    lines = [
        {"line_num": 1, "text": "def hello_world():"},
        {"line_num": 2, "text": "    print('hello')"},
        {"line_num": 3, "text": "    return 42"},
    ]

    chunks = chunk_code_lines(lines, max_chars=15, overlap=0)
    assert len(chunks) > 1

    results = search_in_code(lines, "hello")
    assert len(results) >= 1
    assert any(result["line_num"] in {1, 2} for result in results)
