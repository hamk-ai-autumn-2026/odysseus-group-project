$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🧪 Running DocuMind Automated Sanity Checks (PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "[1/3] Checking UV environment..." -ForegroundColor Yellow
uv --version
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/3] Running pytest suite..." -ForegroundColor Yellow
uv run pytest -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/3] Verifying Streamlit module dry-run..." -ForegroundColor Yellow
uv run python -c "import app; print('✅ app.py syntax and imports verified!')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==========================================" -ForegroundColor Green
Write-Host "🎉 ALL SANITY CHECKS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
