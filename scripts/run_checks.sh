#!/usr/bin/env bash
set -e

echo "=========================================="
echo "🧪 Running DocuMind Automated Sanity Checks"
echo "=========================================="

echo "[1/3] Checking UV environment..."
uv --version

echo "[2/3] Running pytest suite..."
uv run pytest -v

echo "[3/3] Verifying Streamlit module dry-run..."
uv run python -c "import app; print('✅ app.py syntax and imports verified!')"

echo "=========================================="
echo "🎉 ALL SANITY CHECKS PASSED SUCCESSFULLY!"
echo "=========================================="
