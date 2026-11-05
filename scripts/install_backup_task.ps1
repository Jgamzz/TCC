param(
    [string]$TaskName = "SGPV-MySQL-Daily-Backup",
    [string]$RunAt = "01:00"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $pythonCommand = Get-Command python -ErrorAction Stop
    $python = $pythonCommand.Source
}

$backupScript = Join-Path $PSScriptRoot "backup_mysql.py"
$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "`"$backupScript`"" `
    -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $RunAt
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Backup diário do banco MySQL do SGPV, com retenção de 30 dias." `
    -Force | Out-Null

Write-Output "Tarefa '$TaskName' registrada. Defina DB_* e MYSQLDUMP_BIN no ambiente do usuário que executa a tarefa."
