$envFile = Join-Path $PSScriptRoot "SetTaskSchedule_config.env"
$config  = @{}
Get-Content $envFile -Encoding Default |
    Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } |
    ForEach-Object {
        $parts = $_ -split '=', 2
        $config[$parts[0].Trim()] = $parts[1].Trim()
    }

$taskName    = $config['TASK_NAME']
$runner      = Join-Path $PSScriptRoot "SetTaskSchedule_runner.bat"
$action      = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$runner`""
$intervalMin = [int]$config['INTERVAL_MINUTES']
$times       = $config['SCHEDULE_TIMES'] -split ',' | ForEach-Object { $_.Trim() }
$procFile    = $config['PROCEDURE_FILE']

Write-Host ""
Write-Host "タスク名: $taskName"
Write-Host "手順書  : $procFile"

if ($intervalMin -gt 0) {
    Write-Host "モード  : $intervalMin 分ごと"
    $trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                    -RepetitionInterval (New-TimeSpan -Minutes $intervalMin)
    $settings = New-ScheduledTaskSettingsSet `
                    -ExecutionTimeLimit (New-TimeSpan -Minutes ($intervalMin - 1)) `
                    -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $taskName -Action $action `
        -Trigger $trigger -Settings $settings -Force | Out-Null
} else {
    Write-Host "モード  : 時刻指定 ($($times -join ', '))"
    $triggers = $times | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }
    $settings = New-ScheduledTaskSettingsSet `
                    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
                    -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $taskName -Action $action `
        -Trigger $triggers -Settings $settings -Force | Out-Null
}

Disable-ScheduledTask -TaskName $taskName | Out-Null

Write-Host ""
Write-Host "登録完了（無効状態）。確認:"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, TaskPath
Read-Host "`nEnterキーで閉じる"
