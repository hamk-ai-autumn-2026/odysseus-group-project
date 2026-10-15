# DocuMind AI

DocuMind AI is a local document analysis and summarization application. It uses Streamlit for the interface and an OpenAI-compatible LM Studio server for local language-model inference. It can summarize documents, answer questions about them, inspect extracted content, and export reports.

Document parsing, LM Studio requests, and neural text-to-speech run 100% locally by default. The text-to-speech feature uses local neural models via `piper-tts`, running completely offline on your device with high-quality English and Finnish neural voices (downloaded on first use and cached locally).


## Features

- Analyze PDF, Markdown, text, JSON, CSV, Python, C, and C/C++ header/source files.
- Analyze PNG, JPEG, and WebP images with a vision-capable model.
- Extract PDF text, metadata, page images, word counts, character counts, and estimated reading time.
- Choose presets for executive summaries, key insights, technical breakdowns, actionable takeaways, mathematical analysis, or custom prompts.
- Select the output language: same as the document, English, or Finnish.
- Use map-reduce processing for large documents and stream generated responses.
- Stop an active analysis request and avoid saving incomplete reports.
- Chat with a document using relevant document sections as context.
- Search document text, inspect individual pages, and inspect generated chunks.
- Save document extractions, summaries, and chat history in a local SQLite database.
- Browse the SQLite database from the Streamlit Database Explorer page or `scripts/view_db.py`.
- Generate local neural audio voiceovers (WAV) for summaries using English or Finnish Piper TTS without sending data to external services.
- Run in a browser or in a standalone native window powered by pywebview.

## Supported Files

| Category | Extensions | Processing |
| --- | --- | --- |
| Documents | `.pdf`, `.md`, `.markdown`, `.txt`, `.json`, `.csv` | Local text extraction and analysis |
| Images | `.png`, `.jpg`, `.jpeg`, `.webp` | Image input for a vision-capable LM Studio model; no local OCR |
| Source code | `.py`, `.pyi`, `.cpp`, `.cxx`, `.cc`, `.c`, `.h`, `.hpp` | Text analysis plus source metrics and chunking |

Text files must be valid UTF-8. JSON is parsed and formatted before analysis. CSV files use Python's strict CSV parser; the first non-empty record is used as the header row.

#### Image analysis

If you plan to upload PNG, JPEG, or WebP files, load a vision-capable multimodal
model in LM Studio. Text-only models can analyze extracted document text but cannot
interpret image input. If the selected model rejects image input, the app reports
that a vision-capable model is required instead of retrying as text-only analysis.


## Requirements & Stack

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- [LM Studio](https://lmstudio.ai/) with an OpenAI-compatible local server
- `streamlit` for the interface
- `openai` for LM Studio API requests
- `pypdf`, `PyMuPDF`, and `Pillow` for document and image processing
- `pywebview` for the standalone window
- `piper-tts` for 100% offline, local neural text-to-speech voiceovers

The default LM Studio endpoint is `http://localhost:1234/v1`. You can change it in the sidebar. A vision-capable model is required for image analysis.


## Quickstart Guide

### 1. Prerequisites

Ensure you have **LM Studio** and **uv** installed on your system.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Configure & Start LM Studio Server

You can start the LM Studio local inference server using either the **LM Studio CLI (`lms`)** or the **LM Studio GUI**:

#### Option A: Using LM Studio CLI (`lms`) (Recommended)
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

#### Option B: Using LM Studio GUI
1. Open **LM Studio** and download an instruction-tuned GGUF model (e.g., `Llama-3.2-3B-Instruct`, `Llama-3.1-8B-Instruct`, `Qwen2.5-7B-Instruct`, or `Mistral-7B-Instruct`).
2. Go to the **Developer / Local Server** tab (`<->` icon).
3. Select your model at the top and click **Start Server**.
4. By default, LM Studio will start serving at `http://localhost:1234/v1`.


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

The app accepts source-code files as well as PDFs and text documents, so you can upload sample projects, scripts, or C++ sources for local analysis.

### 5. Database Storage & Explorer

Generated documents, summaries, audio voiceovers, and chat messages are persisted in a local SQLite database (`documind.db`) in the current working directory.

To customize the database location, set the `DOCUMIND_DB_PATH` environment variable:

- **Linux / macOS (Bash / Zsh):**
  ```bash
  export DOCUMIND_DB_PATH="/path/to/custom/documind.db"
  ```
- **Windows PowerShell:**
  ```powershell
  $env:DOCUMIND_DB_PATH = "C:\path\to\custom\documind.db"
  ```
- **Windows Command Prompt (CMD):**
  ```cmd
  set DOCUMIND_DB_PATH=C:\path\to\custom\documind.db
  ```

To inspect or query the database:
- Open the interactive **Database Explorer** page in Streamlit via the sidebar.
- Or use the read-only CLI inspector script:
  ```bash
  # View all tables and row counts
  uv run python scripts/view_db.py --tables

  # View recent document records
  uv run python scripts/view_db.py --data documents --limit 20

  # Execute a custom read-only SQL query
  uv run python scripts/view_db.py --query "SELECT COUNT(*) AS total FROM documents"
  ```


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

The checks verify the uv environment, run the full pytest suite, and import the Streamlit application to catch syntax and import errors. To run pytest directly:

```bash
uv run pytest -v
```


## Project Structure

```
odysseus-group-project/
├── app.py                 # Main Streamlit application
├── main.py                # Standalone application entry point
├── pyproject.toml         # UV project configuration and dependencies
├── uv.lock                # UV lockfile
├── todo.md                # Project progress & task checklist
├── .env.example           # Example LM Studio settings
├── README.md              # Project documentation
├── pages/
│   └── db.py              # Streamlit SQLite database viewer page
├── testdocs/              # Sample text, JSON, and source-code fixtures
│   ├── sample_python.py
│   ├── sample_cpp.cpp
│   ├── test_document.md
│   ├── test_document.txt
│   └── test_document.json
├── scripts/
│   ├── run_checks.bat     # Windows CMD checks
│   ├── run_checks.ps1     # Windows PowerShell checks
│   ├── run_checks.py      # Cross-platform checks
│   ├── run_checks.sh      # Linux/macOS checks
│   └── view_db.py         # Read-only SQLite database viewer
├── src/
│   ├── code_analyzer.py   # Source-code detection and metrics
│   ├── code_reader.py     # Code-reader compatibility helpers
│   ├── db.py              # SQLite persistence and database queries
│   ├── desktop_launcher.py # pywebview standalone launcher
│   ├── llm_client.py      # LM Studio client and analysis pipelines
│   ├── pdf_processor.py   # Document, PDF, CSV, and image extraction
│   ├── tts.py             # Local neural Piper TTS voiceover generation
│   └── ui.py              # CSS and reusable Streamlit UI components
└── tests/
      ├── test_app_imports.py   # Syntax and import checks
      ├── test_code_analyzer.py # Source-code analysis tests
      ├── test_db.py            # SQLite persistence tests
      ├── test_llm_client.py    # LM Studio client and analysis tests
      ├── test_pdf_processor.py # Document extraction tests
      └── test_tts.py           # Text-to-speech utility tests
```
