param()
. "$PSScriptRoot\windows-powershell.ps1"
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$vendor = Join-Path $root 'vendor'
$target = Join-Path $vendor 'MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
$lockPath = Join-Path $vendor 'webview2-runtime.lock.json'
$officialUrl = 'https://go.microsoft.com/fwlink/?linkid=2124701'
New-Item -ItemType Directory -Force -Path $vendor | Out-Null
$lock = $null
if (Test-Path -LiteralPath $lockPath) { $lock = Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8 | ConvertFrom-Json }
if (-not (Test-Path -LiteralPath $target)) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $url = $officialUrl
    if ($null -ne $lock) { $url = $lock.resolved_url }
    Write-Host 'Downloading official Microsoft offline WebView2 x64 installer...'
    $temp = $target + '.partial'
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $temp -PassThru -MaximumRedirection 10
    Move-Item -LiteralPath $temp -Destination $target -Force
    $resolved = $response.BaseResponse.ResponseUri.AbsoluteUri
} else {
    $resolved = $officialUrl
    if ($null -ne $lock) { $resolved = $lock.resolved_url }
}
$signature = Get-AuthenticodeSignature -LiteralPath $target
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(?:,|$)') {
    throw "WebView2 Microsoft Authenticode verification failed: $($signature.Status)"
}
$hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
if ($null -ne $lock -and $hash -ne $lock.sha256) { throw 'WebView2 SHA256 differs from the committed runtime lock. Restore the locked installer; update the lock only for a deliberate runtime upgrade.' }
if ((Get-Item -LiteralPath $target).Length -lt 20000000) { throw 'WebView2 download is too small for an offline standalone installer.' }
if ($null -eq $lock) {
    [ordered]@{
        artifact = 'MicrosoftEdgeWebView2RuntimeInstallerX64.exe'; architecture = 'x64';
        official_url = $officialUrl; resolved_url = $resolved;
        version = (Get-Item -LiteralPath $target).VersionInfo.ProductVersion;
        sha256 = $hash; signer = $signature.SignerCertificate.Subject;
        source_documentation = 'https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution'
    } | ConvertTo-Json | Set-Content -LiteralPath $lockPath -Encoding UTF8
}
$releaseRuntime = Join-Path $root 'release\runtime'
New-Item -ItemType Directory -Force -Path $releaseRuntime | Out-Null
Copy-Item -LiteralPath $target -Destination $releaseRuntime -Force
Copy-Item -LiteralPath $lockPath -Destination $releaseRuntime -Force
Write-Host "Verified Microsoft WebView2 offline installer SHA256 $hash"
