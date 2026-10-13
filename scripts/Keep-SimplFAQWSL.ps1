param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[^"\r\n]+$')]
    [string]$LinuxScriptPath
)
$ErrorActionPreference = 'Stop'
$wslExecutable = Join-Path $env:WINDIR 'System32\wsl.exe'
$stateDirectory = Join-Path $env:LOCALAPPDATA 'SimplFAQ'
$statePath = Join-Path $stateDirectory 'wsl-session.json'
if (Test-Path -LiteralPath $statePath) {
    try {
        $record = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $existing = Get-Process -Id $record.processId -ErrorAction Stop
        if ($existing.Path -eq $wslExecutable -and
            [string]$existing.StartTime.ToUniversalTime().Ticks -eq $record.startedTicks) {
            return
        }
    } catch {
        # A stopped or restarted WSL session is replaced on the next explicit start.
    }
}
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$session = Start-Process -FilePath $wslExecutable -WindowStyle Hidden -PassThru -ArgumentList @(
    '-d', 'AlmaLinux-10', '--exec', 'bash', ('"{0}"' -f $LinuxScriptPath)
)
@{
    processId = $session.Id
    startedTicks = [string]$session.StartTime.ToUniversalTime().Ticks
} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
