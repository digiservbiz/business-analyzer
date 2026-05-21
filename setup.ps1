# ============================================================
#  Business Analyzer — Automated Setup Script for Windows
#  Run from PowerShell as: .\setup.ps1
# ============================================================

param(
    [switch]$SkipPythonCheck,
    [switch]$SkipGitCheck
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Business Analyzer Setup"

# ── Colors ───────────────────────────────────────────────────
function Write-Step   { param($msg) Write-Host "`n► $msg" -ForegroundColor Cyan }
function Write-OK     { param($msg) Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn   { param($msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Fail   { param($msg) Write-Host "  ✘ $msg" -ForegroundColor Red }
function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║       Business Analyzer — Setup Wizard       ║" -ForegroundColor Blue
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

Write-Banner

# ── Step 1: Execution Policy ──────────────────────────────────
Write-Step "Checking PowerShell execution policy..."
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Restricted") {
    Write-Warn "Execution policy is Restricted. Updating to RemoteSigned..."
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
    Write-OK "Execution policy set to RemoteSigned"
} else {
    Write-OK "Execution policy OK ($policy)"
}

# ── Step 2: Check Python ──────────────────────────────────────
Write-Step "Checking Python installation..."
if (-not $SkipPythonCheck) {
    try {
        $pyVersion = python --version 2>&1
        if ($pyVersion -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -lt 10) {
                Write-Fail "Python 3.10+ required. Found: $pyVersion"
                Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
                exit 1
            }
            Write-OK "Found $pyVersion"
        } else {
            throw "Not Python 3"
        }
    } catch {
        Write-Fail "Python not found in PATH."
        Write-Host ""
        Write-Host "  Please install Python 3.10+ from:" -ForegroundColor Yellow
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "  ⚠ Check 'Add Python to PATH' during install!" -ForegroundColor Yellow
        Write-Host ""
        $open = Read-Host "  Open download page now? (Y/N)"
        if ($open -eq "Y" -or $open -eq "y") {
            Start-Process "https://www.python.org/downloads/"
        }
        exit 1
    }
}

# ── Step 3: Check Git ─────────────────────────────────────────
Write-Step "Checking Git installation..."
if (-not $SkipGitCheck) {
    try {
        $gitVersion = git --version 2>&1
        Write-OK "Found $gitVersion"
    } catch {
        Write-Fail "Git not found in PATH."
        Write-Host "  Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
        $open = Read-Host "  Open download page now? (Y/N)"
        if ($open -eq "Y" -or $open -eq "y") {
            Start-Process "https://git-scm.com/download/win"
        }
        exit 1
    }
}

# ── Step 4: Clone or update repo ─────────────────────────────
Write-Step "Setting up project files..."

$projectDir = Join-Path $PSScriptRoot ""
$isExistingRepo = Test-Path (Join-Path $projectDir ".git")

if ($isExistingRepo) {
    Write-OK "Already inside the project directory"
} else {
    # Running the script from outside — clone the repo
    $repoUrl = "https://github.com/digiservbiz/business-analyzer.git"
    $cloneDir = Join-Path $PSScriptRoot "business-analyzer"
    if (Test-Path $cloneDir) {
        Write-OK "Directory already exists — skipping clone"
    } else {
        Write-Host "  Cloning repository..." -ForegroundColor Gray
        git clone $repoUrl $cloneDir
        Write-OK "Repository cloned"
    }
    Set-Location $cloneDir
}

# Checkout the working branch
Write-Host "  Switching to branch: claude/analyze-project-method-jPHyK" -ForegroundColor Gray
git fetch origin 2>&1 | Out-Null
git checkout claude/analyze-project-method-jPHyK 2>&1 | Out-Null
Write-OK "Branch checked out"

# ── Step 5: Virtual environment ───────────────────────────────
Write-Step "Creating Python virtual environment..."
$venvPath = Join-Path $PWD ".venv"
if (Test-Path $venvPath) {
    Write-OK "Virtual environment already exists — reusing"
} else {
    python -m venv .venv
    Write-OK "Virtual environment created at .venv\"
}

# Activate
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript
Write-OK "Virtual environment activated"

# ── Step 6: Install dependencies ─────────────────────────────
Write-Step "Installing Python dependencies..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-OK "All dependencies installed"

# ── Step 7: Create .env file ──────────────────────────────────
Write-Step "Configuring environment variables..."
$envFile = Join-Path $PWD ".env"
if (Test-Path $envFile) {
    Write-OK ".env file already exists — skipping (not overwriting)"
} else {
    # Interactive prompts for the essentials
    Write-Host ""
    Write-Host "  Enter your admin credentials (used to log in to the app):" -ForegroundColor White
    $adminUser = Read-Host "  Admin username [admin]"
    if ([string]::IsNullOrWhiteSpace($adminUser)) { $adminUser = "admin" }

    $adminPass = Read-Host "  Admin password [admin123]" -AsSecureString
    $adminPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPass)
    )
    if ([string]::IsNullOrWhiteSpace($adminPassPlain)) { $adminPassPlain = "admin123" }

    # Generate a random secret key
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 48 | ForEach-Object { [char]$_ })

    $envContent = @"
# Business Analyzer — Environment Configuration
# Generated by setup.ps1 on $(Get-Date -Format 'yyyy-MM-dd HH:mm')

# ── Admin login ──────────────────────────────
ADMIN_USERNAME=$adminUser
ADMIN_PASSWORD=$adminPassPlain

# ── Flask ────────────────────────────────────
FLASK_SECRET_KEY=$secretKey
FLASK_DEBUG=false

# ── Google Maps Places API ───────────────────
# Get free key: https://console.cloud.google.com → Enable Places API
GOOGLE_MAPS_API_KEY=

# ── Apollo.io (decision-maker search) ────────
# Free plan: https://app.apollo.io → Settings → API Keys
APOLLO_API_KEY=

# ── Anthropic Claude AI ───────────────────────
# https://console.anthropic.com → API Keys
ANTHROPIC_API_KEY=

# ── Email sending (SMTP) ──────────────────────
# Gmail: use App Password from https://myaccount.google.com → Security → App Passwords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=
SMTP_PASS=
SMTP_FROM=

# ── IMAP reply detection (optional) ──────────
IMAP_HOST=imap.gmail.com
IMAP_USER=
IMAP_PASS=

# ── n8n webhook security (optional) ──────────
WEBHOOK_TOKEN=

# ── HTTPS (set true when behind nginx/SSL) ───
HTTPS=false
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-OK ".env file created with your credentials"
    Write-Warn "API keys are empty — fill them in .env to enable full features"
}

# ── Step 8: Initialize database ───────────────────────────────
Write-Step "Initializing database..."
python database/schema.py
Write-OK "Database ready (businesses.db)"

# ── Step 9: Run quick smoke test ─────────────────────────────
Write-Step "Running syntax checks..."
$files = @("app.py","domain_routes.py","sequence_routes.py","scheduler.py","database/schema.py")
$allOK = $true
foreach ($f in $files) {
    $result = python -m py_compile $f 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "$f — $result"
        $allOK = $false
    }
}
if ($allOK) { Write-OK "All core files pass syntax check" }

# ── Step 10: Create launch shortcut ──────────────────────────
Write-Step "Creating launch shortcut..."
$launchScript = Join-Path $PWD "start.ps1"
$launchContent = @"
# Business Analyzer — Quick Launch
Set-Location "`$PSScriptRoot"
& "`$PSScriptRoot\.venv\Scripts\Activate.ps1"
Write-Host "Starting Business Analyzer on http://localhost:8080 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
python app.py
"@
Set-Content -Path $launchScript -Value $launchContent -Encoding UTF8
Write-OK "Created start.ps1 — run this any time to launch the app"

# ── Done ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  ✔ Setup Complete!                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  1. (Optional) Open .env and add your API keys" -ForegroundColor Gray
Write-Host "     - GOOGLE_MAPS_API_KEY  → business search" -ForegroundColor Gray
Write-Host "     - APOLLO_API_KEY       → find decision-makers" -ForegroundColor Gray
Write-Host "     - ANTHROPIC_API_KEY    → AI emails + scoring" -ForegroundColor Gray
Write-Host "     - SMTP_*               → real email sending" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the app:" -ForegroundColor White
Write-Host "     .\start.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Open your browser:" -ForegroundColor White
Write-Host "     http://localhost:8080" -ForegroundColor Yellow
Write-Host ""

# Ask to launch now
$launch = Read-Host "  Launch the app now? (Y/N)"
if ($launch -eq "Y" -or $launch -eq "y") {
    Write-Host "`n  Starting app... (Ctrl+C to stop)" -ForegroundColor Cyan
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:8080"
    python app.py
}
