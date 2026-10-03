# Install cmj-hub/claude-cold-email into detected Windows agent skill directories.
# Path: npx skills add --all.
$ErrorActionPreference = "Stop"
$Repo = "cmj-hub/claude-cold-email"

function Have-Npx {
  return [bool](Get-Command npx -ErrorAction SilentlyContinue)
}

if (Have-Npx) {
  Write-Host "Installing $Repo via npx skills (all agents, global)..."
  npx -y skills add $Repo --all -g --copy --full-depth
  Write-Host "Done. Restart the agent."
  exit 0
}

Write-Host "npx not found. Install Node 18+ and rerun, or use:"
Write-Host "  npx skills add $Repo --all -g --full-depth"
exit 1
