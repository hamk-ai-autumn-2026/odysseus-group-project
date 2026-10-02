# DocuMind AI - Local PDF Document Analyzer & Summarizer

A fully local, privacy-first PDF document analyzer, summarizer, and interactive Q&A assistant built with **Python (managed by UV)**, **PyPDF**, **LM Studio (OpenAI-compatible local API)**, **pywebview**, and **Streamlit**.

---

## Features

- **100% Local & Private**: No data leaves your machine. Powered by local LLMs via LM Studio.
- **Standalone Desktop Interface**: Runs in a dedicated native window without opening an external web browser.
- **Fast PDF Text Extraction**: Uses `pypdf` for fast text parsing, metadata extraction, page indexing, and search.
- **Multi-Preset Summarization**:
  - Executive Summary (Overview, Main Themes, Conclusions)
  - Key Insights & Bullet Points (Top findings with bold callouts)
  - Technical Breakdown (Architectures, formulas, datasets, and numbers)
  - Actionable Takeaways & Next Steps (Strategic recommendations & action items)
  - Custom Prompting (Run arbitrary analysis instructions on document text)
- **Map-Reduce for Large PDFs**: Automatically chunks long documents and synthesizes section-by-section summaries.
- **Interactive Chat / Q&A**: Ask grounded questions with document context and page-level citations.
- **In-App PDF Search & Inspection**: Search keywords across pages with snippet previews, view raw page content, and inspect text chunk segmentation.
- **Modern Glassmorphic UI**: Sleek dark mode styling, real-time response streaming, metric cards, and one-click Markdown/TXT exports.

---

## Requirements & Stack

- **Package Manager**: [uv](https://docs.astral.sh/uv/) (Fast Python package manager)
- **PDF Parser**: `pypdf`
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

---

## Running Tests & Sanity Checks

Run the automated test runner script to verify environment setup, pytest test suite, and module syntax:

```bash
./scripts/run_checks.sh
```

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
├── scripts/
│   └── run_checks.sh      # Sanity check & test execution script
├── src/
│   ├── __init__.py        # Package initialization
│   ├── desktop_launcher.py# Standalone native window launcher via pywebview
│   ├── llm_client.py      # LM Studio OpenAI API client & map-reduce engine
│   ├── pdf_processor.py   # PyPDF extraction, page analysis, and chunking
│   └── ui.py              # Custom CSS styling, hero banner, and UI components
└── tests/
    ├── __init__.py        # Test package initialization
    ├── test_app_imports.py   # Syntax and import sanity tests
    ├── test_llm_client.py    # Unit tests for LLM client functions
    └── test_pdf_processor.py # Unit tests for PDF parsing and chunking
```

---