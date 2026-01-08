# PowerShell script to start the FastAPI server and open browser
# This script starts uvicorn and automatically opens the browser once the server is ready

$projectRoot = "C:\Daniel\Project VSCODE\SelfStudy - Cursor Vibe Coding\intro_copilot\skills-getting-started-with-github-copilot"
$url = "http://127.0.0.1:8000"
$port = 8000

Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Project root: $projectRoot"

# Change to project root
Set-Location $projectRoot

# Start uvicorn in the background
$process = Start-Process -PassThru -NoNewWindow -FilePath python `
  -ArgumentList "-m uvicorn src.app:app --reload --host 127.0.0.1 --port $port"

# Wait for server to be ready (listen on port)
$timeout = 30
$elapsed = 0
$ready = $false

while ($elapsed -lt $timeout) {
  try {
    $conn = [System.Net.Sockets.TcpClient]::new()
    $conn.Connect("127.0.0.1", $port)
    $conn.Close()
    $ready = $true
    break
  }
  catch {
    Start-Sleep -Milliseconds 500
    $elapsed += 0.5
  }
}

if ($ready) {
  Write-Host "✅ Server is ready!" -ForegroundColor Green
  Write-Host "Opening browser at $url" -ForegroundColor Cyan
  Start-Process $url
  Write-Host "Visit: $url" -ForegroundColor Yellow
} else {
  Write-Host "❌ Server failed to start within timeout" -ForegroundColor Red
}

# Wait for the process to complete
$process.WaitForExit()
