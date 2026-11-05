$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:DJANGO_DEBUG = 'true'
$env:LOCAL_SQLITE = '1'
$env:LOCAL_PREVIEW_NULL_ORIGIN = '1'
$env:PYTHONUTF8 = '1'
$secretFile = Join-Path (Get-Location) '.tools/dev-secret'
if (!(Test-Path -LiteralPath $secretFile)) {
    New-Item -ItemType Directory -Force -Path '.tools' | Out-Null
    $bytes = [byte[]]::new(64)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $secretFile
}
$env:DJANGO_SECRET_KEY = (Get-Content -LiteralPath $secretFile -Raw).Trim()
& './.venv/Scripts/python.exe' backend/manage.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
