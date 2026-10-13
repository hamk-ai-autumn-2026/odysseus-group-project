# DocuMind AI - Test Suite Documentation

This directory contains the automated unit tests, integration test suite, and smoke tests for the **DocuMind AI** document analysis and summarization application.

---

## 📐 Architecture & Standards

All unit test code strictly adheres to modern Python software engineering best practices:
- **PEP 8**: Strict code layout, variable naming conventions, and typing annotations.
- **PEP 287**: Standard reStructuredText/Google-style docstrings across modules, test classes, and test methods.
- **Isolation**: All external LLM client network calls and PyMuPDF rendering routines are fully mocked using `unittest.mock.MagicMock` and `@patch` decorators to guarantee rapid, reproducible offline execution.

---

## 🧪 Test Modules & Coverage

| Test File | Description | Key Areas Tested |
| :--- | :--- | :--- |
| **`tests/test_llm_client.py`** | Unit & smoke tests for LLM client integration (`src/llm_client.py`) | Connection status checking, streaming response generators, single-pass summarization, Map-Reduce pipeline, RAG chat chunk scoring, non-ASCII/Unicode text, numerical boundary values, multi-modal image payloads, user stop callbacks. |
| **`tests/test_pdf_processor.py`** | Unit tests for document extraction (`src/pdf_processor.py`) | PDF text/image parsing, Markdown/TXT/JSON parsing, chunking algorithm edge cases, in-document page keyword search. |
| **`tests/test_app_imports.py`** | Syntax & import sanity tests | Dry-run verification of main application modules (`app.py`, `src/desktop_launcher.py`). |

---

## 🌍 Advanced Edge-Case Coverage

The test suite explicitly handles edge cases and boundary conditions that standard test suites often miss:

### 1. International & Multi-Script Unicode Inputs
- **Chinese (Simplified & Traditional)**: `中文: 这是一个关于人工智能DocuMind project 測試.`
- **Arabic (RTL)**: `Arabic: هذا تقرير اختبار شامل لنظام الذكاء الاصطناعي 12345.`
- **Cyrillic**: `Проверка работы системы анализа документов.`
- **Emojis & Mathematical Formulas**: `🚀🔥 Graph 𝛂 + 𝛃 = 𝛄, $E = mc^2$`
- **Zero-Width Spaces**: `\u200b\u200b\u200b`

### 2. Numerical & Boundary Floating-Point Values
- Parameter edge cases for temperature (`temperature=0.0`, `-0.5`, `1.0`, `1e308`, `float('inf')`, `float('-inf')`, `float('nan')`).
- Proper floating-point IEEE 754 NaN assertion handling via `math.isnan`.

### 3. Extreme Text Inputs & Interruptions
- **Large Inputs**: Truncation safety when input documents exceed 100,000+ characters.
- **User Cancellation**: Early stream termination when `check_stop()` callback returns `True` mid-stream or during Map-phase processing.
- **Context Length Overflow**: Error string detection (`context length`, `n_keep`, `tokens`) with user-actionable instructions.

### 4. Multi-Modal Vision & RAG Relevance
- Filtered payload mapping of Base64 image URLs to chunk page ranges.
- Keyword relevance ranking for multi-chunk context retrieval in chat mode.

---

## 🚀 Running the Tests

You can run the tests on any operating system using the provided scripts or standard `pytest` commands.

### 1. Cross-Platform (All OS: Windows, Linux, macOS)
```bash
uv run python scripts/run_checks.py
```
*or using pytest directly:*
```bash
uv run pytest -v
```

### 2. Linux / macOS Bash
```bash
./scripts/run_checks.sh
```

### 3. Windows Command Prompt (CMD)
```cmd
scripts\run_checks.bat
```

### 4. Windows PowerShell
```powershell
.\scripts\run_checks.ps1
```

---

## 📊 Summary of Sanity Checks Script Execution

The runner scripts execute a 3-step verification process:
1. **Environment Check**: Verifies `uv` package manager installation and version.
2. **Pytest Suite**: Executes all 39 unit and smoke tests with verbose output.
3. **Module Syntax Check**: Performs a dry-run import check of `app.py` and core modules.
