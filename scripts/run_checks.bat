@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🧪 Running DocuMind Automated Sanity Checks (Windows CMD)
echo ==========================================

echo [1/3] Checking UV environment...
uv --version
if %ERRORLEVEL% neq 0 (
    echo ❌ UV environment check failed!
    exit /b %ERRORLEVEL%
)

echo [2/3] Running pytest suite...
uv run pytest -v
if %ERRORLEVEL% neq 0 (
    echo ❌ Pytest suite failed!
    exit /b %ERRORLEVEL%
)

echo [3/3] Verifying Streamlit module dry-run...
uv run python -c "import app; print('✅ app.py syntax and imports verified!')"
if %ERRORLEVEL% neq 0 (
    echo ❌ App import verification failed!
    exit /b %ERRORLEVEL%
)

echo ==========================================
echo 🎉 ALL SANITY CHECKS PASSED SUCCESSFULLY!
echo ==========================================
