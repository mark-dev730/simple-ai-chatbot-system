# McBOT - Manufacturing Chatbot Startup Script

Write-Host "================================" -ForegroundColor Cyan
Write-Host "McBOT - Manufacturing Chatbot" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists in app directory
if (-Not (Test-Path ".\app\venv")) {
    Write-Host "Error: Virtual environment not found in app\venv" -ForegroundColor Red
    Write-Host "Please run: cd app && python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\app\venv\Scripts\Activate.ps1

# Check if .env exists (lives in app/)
if (-Not (Test-Path ".\app\.env")) {
    Write-Host "Warning: app\.env file not found" -ForegroundColor Yellow
    if (Test-Path ".\app\.env.example") {
        Write-Host "Copying from app\.env.example... edit app\.env with your credentials" -ForegroundColor Yellow
        Copy-Item .\app\.env.example .\app\.env
    }
}

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Green
python .\app\backend\core\config.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Database connection failed" -ForegroundColor Red
    Write-Host "Please check your .env configuration" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server - run from project root for proper imports
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
