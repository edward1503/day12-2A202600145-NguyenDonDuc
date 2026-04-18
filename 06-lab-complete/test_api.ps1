# hãy di chuyển tới branch MASTER
# Script to test the AI Agent API (PowerShell)

$API_KEY = "lab6-secret-key-123"
$BASE_URL = "http://localhost:8000"

Write-Host "1. Testing Health Check (Public)" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
Write-Host "`n"

Write-Host "2. Testing Readiness Probe (Public)" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$BASE_URL/ready" -Method Get
Write-Host "`n"

Write-Host "3. Testing AI Agent Ask (Protected)" -ForegroundColor Cyan
$body = @{ question = "How do I deploy a docker container?" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE_URL/ask" -Method Post -Headers @{ "X-API-Key" = $API_KEY } -ContentType "application/json" -Body $body
Write-Host "`n"

Write-Host "4. Testing Metrics (Protected)" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$BASE_URL/metrics" -Method Get -Headers @{ "X-API-Key" = $API_KEY }
Write-Host "`n"

Write-Host "5. Testing Unauthorized Request" -ForegroundColor Red
try {
    Invoke-RestMethod -Uri "$BASE_URL/metrics" -Method Get
} catch {
    Write-Host "Caught expected error: $($_.Exception.Message)"
}
Write-Host "`n"
