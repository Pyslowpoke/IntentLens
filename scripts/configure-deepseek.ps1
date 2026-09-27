param([string]$Model = 'deepseek-flash')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$directory = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$secret = Read-Host 'DeepSeek API Key (hidden input)' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
  $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
  if ([string]::IsNullOrWhiteSpace($key)) { throw 'API key cannot be empty' }
  $path = Join-Path $directory 'model.json'
  @{ provider='deepseek'; model=$Model; base='https://api.deepseek.com'; key=$key.Trim() } | ConvertTo-Json | Set-Content -LiteralPath $path -Encoding UTF8
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
  & icacls $path /inheritance:r /grant:r "${identity}:(F)" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Failed to restrict model configuration permissions' }
  Write-Host 'DeepSeek configured locally. Refresh the workbench. Environment variables override this file.'
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
  $key = $null
}
