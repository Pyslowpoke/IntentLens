param([switch]$Install, [switch]$Check)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
# Explorer does not inherit the development terminal's PATH. Refresh installed
# paths and optionally load machine-local runtime locations (never committed).
$installedPaths = @([Environment]::GetEnvironmentVariable('Path','Machine'), [Environment]::GetEnvironmentVariable('Path','User'))
$env:Path = (@($env:Path) + $installedPaths) -join ';'
$runtimeConfig = Join-Path $projectRoot '.local/runtime-paths.json'
if (Test-Path -LiteralPath $runtimeConfig) {
  $runtimePaths = Get-Content -LiteralPath $runtimeConfig -Raw | ConvertFrom-Json
  foreach ($runtimeDirectory in $runtimePaths.directories) {
    if (Test-Path -LiteralPath $runtimeDirectory -PathType Container) {
      $env:Path = "$runtimeDirectory;$env:Path"
    }
  }
}
$standardNode = Join-Path $env:ProgramFiles 'nodejs'
if (-not (Get-Command node -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath (Join-Path $standardNode 'node.exe'))) {
  $env:Path = "$standardNode;$env:Path"
}
if (-not (Test-Path -LiteralPath '.env')) {
  Copy-Item -LiteralPath '.env.example' -Destination '.env'
  Write-Host 'Created .env. Default rule mode works without an API key.'
}
foreach ($required in @('node', 'pnpm')) {
  if (-not (Get-Command $required -ErrorAction SilentlyContinue)) {
    throw "Missing $required. See START-HERE.md for installation steps."
  }
}
if ($Install) {
  if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv and add it to PATH: https://docs.astral.sh/uv/getting-started/installation/' }
  uv sync --frozen
  if ($LASTEXITCODE -ne 0) { throw 'uv sync failed' }
  pnpm install --frozen-lockfile
  if ($LASTEXITCODE -ne 0) { throw 'pnpm install failed' }
  pnpm --dir apps/web prepare-assets
  if ($LASTEXITCODE -ne 0) { throw 'Asset preparation failed' }
  uv run playwright install chromium
  if ($LASTEXITCODE -ne 0) { throw 'Browser installation failed' }
  uv run python scripts/generate_samples.py
  if ($LASTEXITCODE -ne 0) { throw 'Sample generation failed' }
}
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Missing .venv; run with -Install or follow README pip setup.' }
if (-not (Test-Path -LiteralPath 'apps/web/node_modules/next')) { throw 'Frontend dependencies missing. See START-HERE.md, then run scripts/start.ps1 -Install.' }
if ($Check) {
  node --version
  if ($LASTEXITCODE -ne 0) { throw 'Node runtime failed' }
  pnpm --version
  if ($LASTEXITCODE -ne 0) { throw 'pnpm runtime failed' }
  & $pythonExe -c 'import fastapi, pandas'
  if ($LASTEXITCODE -ne 0) { throw 'Python dependencies failed' }
  Write-Host 'Startup checks passed. No servers started.'
  exit 0
}
foreach ($port in @(3000,8000)) {
  if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $port is in use. If IntentLens is running, open http://127.0.0.1:3000. Stop the old instance before restarting."
  }
}
$apiProcess = $null
$workerProcess = $null
try {
$apiProcess = Start-Process -FilePath $pythonExe -ArgumentList '-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port','8000' -WindowStyle Hidden -PassThru -RedirectStandardOutput 'api.log' -RedirectStandardError 'api-error.log'
$workerProcess = Start-Process -FilePath $pythonExe -ArgumentList '-m','services.worker.main' -WindowStyle Hidden -PassThru -RedirectStandardOutput 'worker.log' -RedirectStandardError 'worker-error.log'
Write-Host 'Open http://127.0.0.1:3000 after Next.js shows Ready. Keep this window open.'
Write-Host 'Ctrl+C stops this launch. Logs: api-error.log and worker-error.log.'
pnpm dev
} finally {
  foreach ($ownedProcess in @($apiProcess, $workerProcess)) {
    if ($ownedProcess -and -not $ownedProcess.HasExited) {
      & taskkill.exe /PID $ownedProcess.Id /T /F 2>$null | Out-Null
    }
  }
}
