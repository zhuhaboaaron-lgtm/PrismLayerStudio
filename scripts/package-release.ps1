param()
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv-build\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run build.bat first to create the build environment.' }
& $python (Join-Path $PSScriptRoot 'package-release.py')
if ($LASTEXITCODE -ne 0) { throw 'Release packaging failed.' }
