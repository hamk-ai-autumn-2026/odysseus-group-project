# AGENTS.md - Repository Guidelines for AI Agents

## 🛠️ Allowed & Recommended Commands

AI agents operating in this repository are authorized to execute the following standard commands without requesting manual user confirmation:

- **Environment & Dependency Sync**: `uv sync`
- **Automated Sanity & Test Verification**: `./scripts/run_checks.sh`
- **Pytest Suite**: `uv run pytest`
- **Launch Standalone Application**: `uv run documind` or `uv run python main.py`
- **Launch Web Application**: `uv run streamlit run app.py`

---

## 📋 Verification & Workflow Rules

1. **Always Verify Edits**: Run `./scripts/run_checks.sh` after modifying any python modules, configuration files, or unit tests.
2. **Sync Dependencies**: Run `uv sync` whenever adding dependencies or modifying `pyproject.toml`.
3. **Preserve Clean Structure**: Source code resides in `src/`, unit tests in `tests/`, executable scripts in `scripts/`.
