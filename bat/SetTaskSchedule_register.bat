@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0SetTaskSchedule_register.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [エラー] 登録失敗。 終了コード: %errorlevel%
    pause
)
