param()
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$tools = Join-Path $root '.tools'
$toolDir = Join-Path $tools 'inno6'
$compiler = Join-Path $toolDir 'ISCC.exe'
if (Test-Path -LiteralPath $compiler) { Write-Output $compiler; exit 0 }
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$setup = Join-Path $tools 'innosetup-6.6.1.exe'
if (-not (Test-Path -LiteralPath $setup)) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/jrsoftware/issrc/releases/download/is-6_6_1/innosetup-6.6.1.exe' -OutFile $setup
}
# SHA256 published by the immutable official GitHub release API.
# https://api.github.com/repos/jrsoftware/issrc/releases/tags/is-6_6_1
$expected = 'd243ce440c02705530699554fb9612b9b2bd7a2a90629cdb7f41e66f5faeb91f'
if ((Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Inno Setup SHA256 verification failed.' }
$signature = Get-AuthenticodeSignature -LiteralPath $setup
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Pyrsys B.V.(?:,|$)') { throw 'Inno Setup Authenticode verification failed.' }
if (-not $toolDir.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe tools directory.' }
$arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CURRENTUSER',('/DIR="' + $toolDir + '"'))
$process = Start-Process -FilePath $setup -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Installing the verified local Inno build tool failed with exit code $($process.ExitCode)." }
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Inno Setup compiler missing after installation.' }
Write-Output $compiler
