# YoyangScript Launcher
# Author: Feng Kaiying (2026)

$host.UI.RawUI.WindowTitle = "YoyangScript"
$ErrorActionPreference = "Continue"

Clear-Host
Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "       YoyangScript Toolbox Launcher" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host ""

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Test-PythonExe($exePath) {
    if (-not $exePath) { return $false }
    if (-not (Test-Path $exePath)) { return $false }
    $item = Get-Item $exePath -ErrorAction SilentlyContinue
    if (-not $item -or $item.Length -eq 0) { return $false }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exePath
        $psi.Arguments = "--version"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $process = [System.Diagnostics.Process]::Start($psi)
        $output = $process.StandardOutput.ReadToEnd()
        $null = $process.WaitForExit(5000)
        if ($process.ExitCode -eq 0 -and $output -match "Python") {
            return $true
        }
    } catch {}
    return $false
}

function Find-RealPython {
    $localAppData = [System.Environment]::GetEnvironmentVariable("LOCALAPPDATA")
    $paths = @(
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "$localAppData\Programs\Python\Python312\python.exe",
        "$localAppData\Programs\Python\Python311\python.exe"
    )
    foreach ($p in $paths) {
        if (Test-PythonExe $p) {
            return (Get-Item $p).FullName
        }
    }

    Refresh-Path
    try {
        $cmd = (Get-Command python -ErrorAction Stop).Source
        if (Test-PythonExe $cmd) {
            return (Get-Item $cmd).FullName
        }
    } catch {}

    $whereResult = where.exe python 2>$null
    if ($whereResult) {
        foreach ($line in $whereResult) {
            $line = $line.Trim()
            if ($line -and (Test-Path $line) -and (Test-PythonExe $line)) {
                return (Get-Item $line).FullName
            }
        }
    }

    return $null
}

function Install-PythonWinget {
    Write-Host "  [Mode 1] winget installing Python..." -ForegroundColor Cyan
    cmd /c "winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements"
    Refresh-Path
    Start-Sleep -Seconds 3
    return Find-RealPython
}

function Install-PythonDirect {
    Write-Host "  [Mode 2] Downloading Python 3.12.8 from python.org..." -ForegroundColor Cyan
    $installerName = "python-3.12.8-amd64.exe"
    $downloadUrl = "https://www.python.org/ftp/python/3.12.8/" + $installerName
    $installerPath = Join-Path $env:TEMP $installerName

    if (Test-Path $installerPath) { [System.IO.File]::Delete($installerPath) }

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    } catch {
        Write-Host "  Download failed: $_" -ForegroundColor Red
        return $null
    }
    Write-Host "  Download OK. Installing (1-2 min)..." -ForegroundColor Gray

    $sargs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
    $process = Start-Process -FilePath $installerPath -ArgumentList $sargs -Wait -PassThru

    if (Test-Path $installerPath) { [System.IO.File]::Delete($installerPath) }

    if ($process.ExitCode -ne 0) {
        Write-Host "  Install failed (code: $($process.ExitCode))" -ForegroundColor Red
        return $null
    }

    Refresh-Path
    Start-Sleep -Seconds 3
    return Find-RealPython
}

function Auto-InstallPython {
    Write-Host "  Starting auto-install..." -ForegroundColor Yellow
    Write-Host ""

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        $py = Install-PythonWinget
        if ($py) { return $py }
        Write-Host ""
    }

    $py = Install-PythonDirect
    if ($py) { return $py }

    Write-Host ""
    Write-Host "  ==========================================" -ForegroundColor Red
    Write-Host "  Auto-install failed." -ForegroundColor Red
    Write-Host "  Install Python from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  Check [Add Python to PATH] when installing!" -ForegroundColor White
    Write-Host "  ==========================================" -ForegroundColor Red
    return $null
}

# ========== Main ==========

Write-Host "  [1/3] Checking Python..." -ForegroundColor Yellow
$pythonExe = Find-RealPython

if (-not $pythonExe) {
    Write-Host "  Python is not installed." -ForegroundColor Magenta
    Write-Host ""
    $choice = Read-Host "  Auto-install Python 3.12? (Y=Yes / N=No)"
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        $pythonExe = Auto-InstallPython
        if (-not $pythonExe) {
            Write-Host ""
            Read-Host "  Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "  Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "  Press Enter to exit"
        exit 1
    }
}

Write-Host "  Python path: $pythonExe" -ForegroundColor Gray

# Validate Python
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = "--version"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$process = [System.Diagnostics.Process]::Start($psi)
$verOutput = $process.StandardOutput.ReadToEnd()
$null = $process.WaitForExit(5000)

if ($process.ExitCode -ne 0 -or $verOutput -notmatch "Python") {
    Write-Host "  Python is broken! (exit: $($process.ExitCode))" -ForegroundColor Red
    Write-Host "  Path: $pythonExe" -ForegroundColor Red
    Write-Host "  Output: $verOutput" -ForegroundColor Red
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}
Write-Host "  [OK] Python ready:" $verOutput.Trim() -ForegroundColor Green

Write-Host ""
Write-Host "  [2/3] Checking Flask..." -ForegroundColor Yellow
$flaskOk = $false

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = '-c "import flask"'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$p = [System.Diagnostics.Process]::Start($psi)
$null = $p.WaitForExit(5000)
if ($p.ExitCode -eq 0) { $flaskOk = $true }

if (-not $flaskOk) {
    Write-Host "  Flask is not installed." -ForegroundColor Magenta
    Write-Host ""
    $choice = Read-Host "  Install Flask now? (Y=Yes / N=No)"
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        Write-Host "  Installing Flask..." -ForegroundColor Cyan
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $pythonExe
        $psi.Arguments = "-m pip install flask"
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $null = $p.WaitForExit(120000)
        if ($p.ExitCode -ne 0) {
            Write-Host "  Install failed! Run: python -m pip install flask" -ForegroundColor Red
            Write-Host ""
            Read-Host "  Press Enter to exit"
            exit 1
        }
        Write-Host "  [OK] Flask installed!" -ForegroundColor Green
    } else {
        Write-Host "  Skipped. Run: python -m pip install flask" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "  Press Enter to exit"
        exit 1
    }
}
Write-Host "  [OK] All dependencies ready" -ForegroundColor Green

Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host "  [3/3] Starting YoyangScript server..." -ForegroundColor Green
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -LiteralPath $PSScriptRoot
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = "start.py"
$psi.UseShellExecute = $false
$psi.WorkingDirectory = $PSScriptRoot
$p = [System.Diagnostics.Process]::Start($psi)
$null = $p.WaitForExit()

Write-Host ""
Read-Host "  Press Enter to exit"
