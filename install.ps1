# install.ps1 — Install claude-cold-email on Windows
# Usage: iwr https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.ps1 -useb | iex

$ErrorActionPreference = "Stop"

$RepoUrl   = "https://github.com/cmj-hub/claude-cold-email"
$SkillsDir = "$env:USERPROFILE\.claude\skills"
$AgentsDir = "$env:USERPROFILE\.claude\agents"

Write-Host "Installing claude-cold-email..."

# Check git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is required but not installed."
    exit 1
}

New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
New-Item -ItemType Directory -Force -Path $AgentsDir | Out-Null

$TempDir = Join-Path $env:TEMP "claude-cold-email-$([guid]::NewGuid().ToString('N'))"
try {
    Write-Host "Cloning repository..."
    git clone --depth 1 $RepoUrl $TempDir 2>$null | Out-Null

    Write-Host "Installing main orchestrator skill (cold-email/)..."
    $dest = Join-Path $SkillsDir "cold-email"
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Copy-Item -Recurse (Join-Path $TempDir "cold-email") $SkillsDir
    Write-Host "  + cold-email"

    Write-Host "Installing sub-skills..."
    Get-ChildItem (Join-Path $TempDir "skills") -Directory -Filter "cold-email-*" | ForEach-Object {
        $dest = Join-Path $SkillsDir $_.Name
        if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
        Copy-Item -Recurse $_.FullName $SkillsDir
        Write-Host "  + $($_.Name)"
    }

    Write-Host "Installing agents..."
    Get-ChildItem (Join-Path $TempDir "agents") -Filter "cold-email-*.md" | ForEach-Object {
        Copy-Item $_.FullName $AgentsDir -Force
        Write-Host "  + $($_.BaseName)"
    }

    Write-Host ""
    Write-Host "Done. Restart Claude Code to pick up the new skill."
    Write-Host ""
    Write-Host "Try it:"
    Write-Host "  > Write a cold email to <name>, <role> at <company>. They just <signal>."
    Write-Host ""
    Write-Host "Course:  https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft"
    Write-Host "Source:  $RepoUrl"
} finally {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    }
}
