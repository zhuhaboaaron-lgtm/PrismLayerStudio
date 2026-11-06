param([switch]$SkipRuntime)
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $root
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required.' }
$python = Join-Path $root '.venv-build\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $created = $false
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        foreach ($version in @('-3.13','-3.12','-3.11','-3.14')) {
            try { & py.exe $version -c 'import sys,struct; sys.exit(not (struct.calcsize(chr(80))==8))' 2>$null }
            catch { continue }
            if ($LASTEXITCODE -eq 0) {
                & py.exe $version -m venv '.venv-build'
                if ($LASTEXITCODE -ne 0) { throw 'Creating build environment failed.' }
                $created = $true
                break
            }
        }
    }
    if (-not $created -and (Get-Command python.exe -ErrorAction SilentlyContinue)) {
        & python.exe -c 'import sys,struct; sys.exit(not ((3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize(chr(80))==8))'
        if ($LASTEXITCODE -eq 0) {
            & python.exe -m venv '.venv-build'
            if ($LASTEXITCODE -ne 0) { throw 'Creating build environment failed.' }
            $created = $true
        }
    }
    if (-not $created) { throw 'Install official Windows x64 Python 3.11-3.14, then run build.bat again.' }
}
& $python -c 'import sys,struct; assert (3,11)<=sys.version_info[:2]<=(3,14) and struct.calcsize(chr(80))==8'
if ($LASTEXITCODE -ne 0) { throw 'Unsupported build environment.' }
Write-Host '[1/4] Installing pinned build dependencies...'
$pipArgs = @('-m','pip','install','--disable-pip-version-check','-r','requirements-build.txt')
if (Test-Path -LiteralPath 'vendor\wheels') { $pipArgs += @('--no-index','--find-links','vendor\wheels') }
& $python @pipArgs
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
& $python 'scripts\collect-licenses.py'
if ($LASTEXITCODE -ne 0) { throw 'Collecting third-party license texts failed.' }
New-Item -ItemType Directory -Force -Path 'release','release\runtime' | Out-Null
Write-Host '[2/4] Building windowed Windows x64 single-file executable...'
& $python -m PyInstaller --noconfirm --clean --distpath release 'PrismLayerStudio.spec'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
Write-Host '[3/4] Preparing offline WebView2 prerequisite...'
if (-not $SkipRuntime) { & (Join-Path $PSScriptRoot 'prepare-runtime.ps1') }
Write-Host '[4/4] Recording build identity...'
$deps = & $python -m pip freeze
$deps | Set-Content -LiteralPath 'release\build-environment.txt' -Encoding UTF8
$manifest = [ordered]@{
    product = 'Prism Layer Studio'; version = '2.6.0'; architecture = 'x64';
    python = (& $python --version 2>&1 | Out-String).Trim();
    built_utc = [DateTime]::UtcNow.ToString('o');
    executable_sha256 = (Get-FileHash -LiteralPath 'release\PrismLayerStudio.exe' -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath 'release\build-manifest.json' -Encoding UTF8
Write-Host 'Built release\PrismLayerStudio.exe'
Write-Host 'For machines without WebView2, keep release\runtime beside the EXE or use the offline Setup.'
