#!/usr/bin/env pwsh
# ============================================================
#  Domain Extractor - One-Click Deploy Script
#  Usage: Right-click push.ps1 -> "Run with PowerShell"
#         OR in terminal:  .\push.ps1
# ============================================================

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   DOMAIN EXTRACTOR - DEPLOY TOOL    " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "[SETUP] No git repo found. Initializing..." -ForegroundColor Yellow
    git init
    git branch -M main

    $remote = Read-Host "Enter your GitHub repository URL (e.g. https://github.com/USERNAME/REPO.git)"
    git remote add origin $remote
    Write-Host "[SETUP] Remote set." -ForegroundColor Green
}

# Check if there are any changes to commit
$status = git status --porcelain
if (-not $status) {
    Write-Host "[INFO] No changes detected. Nothing to push." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 0
}

# Show what will be staged
Write-Host "[CHANGES] The following files have been modified:" -ForegroundColor White
git status --short
Write-Host ""

# Prompt for commit message
$commitMsg = Read-Host "Enter a commit message (leave blank to use timestamp)"

if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "chore: update $timestamp"
}

# Stage all changes
Write-Host ""
Write-Host "[GIT] Staging all changes..." -ForegroundColor Cyan
git add .

# Commit
Write-Host "[GIT] Committing: '$commitMsg'" -ForegroundColor Cyan
git commit -m $commitMsg

# Push
Write-Host "[GIT] Pushing to GitHub (main)..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Green
    Write-Host "  ✅ PUSHED SUCCESSFULLY TO GITHUB!  " -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Vercel will auto-deploy in ~1 min." -ForegroundColor White
    Write-Host "  DB migrations auto-apply via GHA.  " -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "  ❌ PUSH FAILED. Check error above.  " -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor Red
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
