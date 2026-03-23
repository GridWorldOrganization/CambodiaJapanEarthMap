@echo off
setlocal
set ENVFILE=%~dp0SetTaskSchedule_config.env

:: 設定ファイル読み込み
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%ENVFILE%") do (
    if not "%%a"=="" set "%%a=%%b"
)

schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% equ 0 (
    echo.
    echo 登録削除完了。 [%TASK_NAME%]
) else (
    echo.
    echo 削除失敗（未登録の可能性あり）。 [%TASK_NAME%]
)
pause
