# DocuMind AI - Local Document Analyzer & Summarizer

A fully local, privacy-first document analyzer, summarizer, and interactive Q&A assistant built with **Python (managed by UV)**, **PyPDF**, **LM Studio (OpenAI-compatible local API)**, **pywebview**, and **Streamlit**.

---

## Features

- **100% Local & Private**: No data leaves your machine. Powered by local LLMs via LM Studio.
- **Standalone Desktop Interface**: Runs in a dedicated native window without opening an external web browser.
- **Multi-format Extraction**: Analyzes PDF, Markdown (`.md`/`.markdown`), plain text (`.txt`), JSON (`.json`), Python (`.py`/`.pyi`), and C++/C source files (`.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp`). PDFs also support page images for vision-capable local LLMs.
- **Code Reader / Analyzer**: Detects Python and C++ source structure, counts functions/classes/imports, chunks code by line ranges, and supports keyword search across source files.
- **Summary Language Selection**: Choose Same as Document, English, or Finnish for single-pass and map-reduce summaries.
- **Multi-Preset Summarization**:
  - Executive Summary (Overview, Main Themes, Conclusions)
  - Key Insights & Bullet Points (Top findings with bold callouts)
  - Technical Breakdown (Architectures, formulas, datasets, and numbers)
  - Actionable Takeaways & Next Steps (Strategic recommendations & action items)
  - Custom Prompting (Run arbitrary analysis instructions on document text)
- **Map-Reduce for Large Documents**: Automatically chunks long documents and synthesizes section-by-section summaries.
- **SQLite Persistence & Instant Caching**: Document extractions, past summary reports, and Q&A chat history are persisted in a local SQLite database (`documind.db`). Re-uploading or selecting a saved document loads instantly from cache.
- **Recent Documents Library**: Seamlessly switch between previously analyzed documents from the sidebar library.
- **Modern Glassmorphic UI**: Sleek dark mode styling, real-time response streaming, metric cards, and one-click Markdown/TXT exports.

---

## Requirements & Stack

- **Package Manager**: [uv](https://docs.astral.sh/uv/) (Fast Python package manager)
- **Document & Code Parsers**: `pypdf` and `PyMuPDF` for PDFs; Python standard library for Markdown, text, and JSON; built-in source parsing for Python and C++/C files
- **Standalone Window Engine**: `pywebview`
- **LLM Local Server**: [LM Studio](https://lmstudio.ai/)
- **Frontend Framework**: `streamlit`
- **LLM Client**: `openai` (configured to point to LM Studio's local endpoint `http://localhost:1234/v1`)

---

## Quickstart Guide

### 1. Prerequisites

Ensure you have **LM Studio** and **UV** installed on your system.

- Install `uv` (if not already installed):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  ```bash
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### 2. Configure & Start LM Studio Server

You can start the LM Studio local inference server using either the **LM Studio GUI** or the **LM Studio CLI (`lms`)**:

#### Option A: Using LM Studio GUI
1. Open **LM Studio** and download an instruction-tuned GGUF model (e.g., `Llama-3.2-3B-Instruct`, `Llama-3.1-8B-Instruct`, `Qwen2.5-7B-Instruct`, or `Mistral-7B-Instruct`).
2. Go to the **Developer / Local Server** tab (`<->` icon).
3. Select your model at the top and click **Start Server**.
4. By default, LM Studio will start serving at `http://localhost:1234/v1`.

#### Option B: Using LM Studio CLI (`lms`)
If you have installed the `lms` CLI tool (via LM Studio Settings -> Install `lms` CLI):

1. **Start the local server**:
   ```bash
   lms server start
   ```
2. **List available local models**:
   ```bash
   lms ls
   ```
3. **Load a model into memory**:
   ```bash
   lms load <model-name-or-identifier>
   # Example: lms load llama-3.2-3b-instruct
   ```
4. **Check server status**:
   ```bash
   lms server status
   ```
   The local server will run on `http://localhost:1234/v1`.

### 3. Install Dependencies with UV

Running with `uv` automatically sets up the venv and syncs dependencies:

```bash
uv sync
```

For image analysis, load a vision-capable multimodal model in LM Studio. Text-only
models can still analyze the extracted PDF text, but they cannot interpret rendered
page images.

### 4. Run the Application

#### Standalone Desktop App (Recommended - No Browser Required)
Launch as a native standalone desktop app window:

```bash
uv run python main.py
```
*or using the CLI script entry point:*
```bash
uv run documind
```

#### Browser Mode
Launch in a standard browser window via Streamlit:

```bash
uv run streamlit run app.py
```

The app accepts source-code files as well as PDFs and text documents, so you can upload sample projects, scripts, or C++ sources for local analysis.

---

## Running Tests & Sanity Checks

Run the automated test runner script to verify environment setup, pytest test suite, and module syntax:

### Linux / macOS
```bash
./scripts/run_checks.sh
```

### Windows Command Prompt (CMD)
```cmd
scripts\run_checks.bat
```

### Windows PowerShell
```powershell
.\scripts\run_checks.ps1
```

### Cross-Platform (Any OS)
```bash
uv run python scripts/run_checks.py
```
*or using pytest directly:*
```bash
uv run pytest -v
```

For full details on unit tests, smoke tests, and edge-case coverage (Unicode, floating point inf/nan, stop signals), see [tests/README.md](tests/README.md).

---

## Project Structure

```
odysseus-group-project/
├── app.py                 # Main Streamlit application
├── main.py                # Standalone application entry point
├── pyproject.toml         # UV project configuration and dependencies
├── uv.lock                # UV lockfile
├── todo.md                # Project progress & task checklist
├── .env.example           # Environment configuration template
├── README.md              # Project documentation
├── Docs/                  # Sample PDF documents and output reports
├── testdocs/              # Sample text, JSON, and source-code fixtures for validation
│   ├── sample_python.py
│   ├── sample_cpp.cpp
│   ├── test_document.md
│   ├── test_document.txt
│   └── test_document.json
├── scripts/
│   ├── run_checks.sh      # Linux/macOS bash sanity check script
│   ├── run_checks.bat     # Windows CMD sanity check script
│   ├── run_checks.ps1     # Windows PowerShell sanity check script
│   └── run_checks.py      # Cross-platform Python sanity check runner
├── src/
│   ├── __init__.py        # Package initialization
│   ├── code_analyzer.py   # Code parsing, detection, chunking, and search for Python/C++
│   ├── code_reader.py     # Compatibility wrapper for code-analysis entry points
│   ├── db.py              # SQLite storage layer for caching & session persistence
│   ├── desktop_launcher.py# Standalone native window launcher via pywebview
│   ├── llm_client.py      # LM Studio OpenAI API client & map-reduce engine
│   ├── pdf_processor.py   # Multi-format extraction, PDF image rendering, and chunking
│   └── ui.py              # Custom CSS styling, hero banner, and UI components
└── tests/
    ├── __init__.py        # Test package initialization
    ├── README.md          # Test suite documentation & coverage guide
    ├── test_app_imports.py   # Syntax and import sanity tests
    ├── test_code_analyzer.py # Unit tests for Python/C++ code parsing
    ├── test_llm_client.py    # Unit tests for LLM client functions
    ├── test_pdf_processor.py # Unit tests for PDF and text parsing
    └── test_code_reader.py   # Compatibility checks for the code reader API
    ├── test_db.py            # Unit tests for SQLite storage layer
```

---