# Prevent a PowerShell 7 parent process from injecting Core-only modules into
# Windows PowerShell 5.1. Uses OS-owned absolute module paths, never a user module.
if ($PSVersionTable.PSEdition -eq 'Desktop') {
    $env:PSModulePath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules;$env:ProgramFiles\WindowsPowerShell\Modules"
    $systemModules = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules"
    Import-Module "$systemModules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1" -Force
    Import-Module "$systemModules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1" -Force
    Import-Module "$systemModules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1" -Force
}
