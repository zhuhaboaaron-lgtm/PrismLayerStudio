param([switch]$IncludeEnvironment)
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$targets = @('build','dist','__pycache__','tests\__pycache__')
if ($IncludeEnvironment) { $targets += '.venv-build' }
foreach ($relative in $targets) {
    $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force; Write-Host "Removed $relative" }
}
Write-Host 'Build caches removed. release/, vendor/, source and exported results are preserved.'
