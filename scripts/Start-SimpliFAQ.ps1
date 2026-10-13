$ErrorActionPreference = 'Stop'
$projectPath = '/mnt/c/repos/simpliFAQ'
wsl -d AlmaLinux-10 -- bash "$projectPath/scripts/start.sh"
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar o SimpliFAQ.' }
Start-Process 'http://localhost:8080'
