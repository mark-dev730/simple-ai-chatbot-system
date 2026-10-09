# AI Chatbot System Production Startup Script

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AI CHATBOT SYSTEM - PRODUCTION" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".\venv")) {
    Write-Host "Error: Virtual environment not found" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Check if .env exists
if (-Not (Test-Path ".\.env")) {
    Write-Host "Error: .env file not found" -ForegroundColor Red
    exit 1
}

# Build frontend if needed
if (-Not (Test-Path ".\frontend\dist")) {
    Write-Host "Building frontend..." -ForegroundColor Green
    Set-Location frontend
    npm run build
    Set-Location ..
} else {
    Write-Host "Frontend build found" -ForegroundColor Green
}

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Green
python .\backend\core\config.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Database connection failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting production server..." -ForegroundColor Green
Write-Host "Application will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python main.py
