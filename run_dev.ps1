# NexusIQ All-in-One Development Runner
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " NexusIQ - AI-Powered Energy Management Platform " -ForegroundColor Cyan
Write-Host " Predict. Optimize. Sustain. | Ideathon 2026 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# Start Backend in background process or separate job
$backendScript = Join-Path $PSScriptRoot "start_backend.py"
Write-Host "`n[1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
$backendJob = Start-Process -FilePath "python" -ArgumentList $backendScript -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Frontend Vite Server on http://localhost:3000..." -ForegroundColor Yellow
Set-Location (Join-Path $PSScriptRoot "frontend")
npm run dev -- --host

