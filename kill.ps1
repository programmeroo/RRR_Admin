# Kill RRR_Admin Flask processes
# Run this with: .\kill.ps1

Write-Host "Stopping RRR_Admin Flask server..." -ForegroundColor Yellow

# Method 1: Kill by port 5001
try {
    $connections = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
    if ($connections) {
        $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $processIds) {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Killing process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Red
                Stop-Process -Id $pid -Force
            }
        }
        Write-Host "Successfully killed Flask server on port 5001" -ForegroundColor Green
    } else {
        Write-Host "No process found on port 5001" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error checking port 5001: $_" -ForegroundColor Red
}

# Method 2: Kill Python processes in this directory (backup method)
Write-Host "`nChecking for Python processes in RRR_Admin..." -ForegroundColor Yellow
$currentDir = (Get-Location).Path
$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*RRR_Admin*"
}

if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        Write-Host "Killing Python process: $($proc.Id) - $($proc.Path)" -ForegroundColor Red
        Stop-Process -Id $proc.Id -Force
    }
    Write-Host "Python processes killed" -ForegroundColor Green
} else {
    Write-Host "No RRR_Admin Python processes found" -ForegroundColor Yellow
}

Write-Host "`nDone!" -ForegroundColor Green
