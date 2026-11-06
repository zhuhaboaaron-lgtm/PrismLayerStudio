param([switch]$Rebuild)
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $root
if ($Rebuild -or -not (Test-Path -LiteralPath 'release\PrismLayerStudio.exe')) {
    & (Join-Path $PSScriptRoot 'build.ps1')
} else {
    & (Join-Path $PSScriptRoot 'prepare-runtime.ps1')
}
$compiler = Join-Path $root '.tools\inno6\ISCC.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    $candidates = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")
    foreach ($candidate in $candidates) { if (Test-Path -LiteralPath $candidate) { $compiler = $candidate; break } }
}
if (-not (Test-Path -LiteralPath $compiler)) { $compiler = & (Join-Path $PSScriptRoot 'prepare-inno.ps1') }
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Inno Setup compiler missing. Install Inno Setup 6.6.1 from jrsoftware.org.' }
& (Join-Path $root '.venv-build\Scripts\python.exe') (Join-Path $PSScriptRoot 'prepare-installer-licenses.py')
if ($LASTEXITCODE -ne 0) { throw 'Preparing short-path installer licenses failed.' }
& $compiler '/Qp' 'installer\PrismLayerStudio.iss'
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }
Get-FileHash -LiteralPath 'release\PrismLayerStudio-Setup.exe' -Algorithm SHA256 | Format-List
Write-Host 'Built release\PrismLayerStudio-Setup.exe (offline WebView2 installer included).'
