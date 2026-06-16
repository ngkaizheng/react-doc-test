<#
.SYNOPSIS
    Start the Project Memory retrieval server (keeps embedding model warm).
.DESCRIPTION
    Launches retriever-server.py in the background using Start-Process.
    The server binds to localhost:8000 by default.
.PARAMETER Port
    Port to listen on (default: 8000).
.PARAMETER NoWindow
    Hide the server console window (use with -NoWindow switch).
.EXAMPLE
    .\start-server.ps1
    .\start-server.ps1 -Port 9000
    .\start-server.ps1 -Port 8000 -NoWindow
#>

param(
    [int]$Port = 8000,
    [switch]$NoWindow = $false
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptDir "retriever-server.py"

if (-not (Test-Path $ServerScript)) {
    Write-Error "retriever-server.py not found at: $ServerScript"
    exit 1
}

$windowStyle = if ($NoWindow) { "Hidden" } else { "Normal" }

Write-Host "🚀 Starting Project Memory retrieval server on port $Port..." -ForegroundColor Cyan

Start-Process -FilePath "python" -ArgumentList "$ServerScript --port $Port" `
    -WindowStyle $windowStyle `
    -NoNewWindow:$false

Write-Host "✅ Server starting in background (port $Port)" -ForegroundColor Green
Write-Host "   Use --server flag with retriever.py to connect:"
Write-Host "   python retriever.py --server --port $Port --query ""...""" -ForegroundColor Gray
Write-Host ""
Write-Host "   To stop the server, find its PID and kill it:"
Write-Host "   netstat -ano | findstr :$Port" -ForegroundColor Gray
