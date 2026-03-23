@echo off
setlocal
set BAT_DIR=%~dp0
set WORK_DIR=C:\sync_c\claude_code_akasaka2\mapapp
set LOGFILE=%BAT_DIR%SetTaskSchedule.log
set ENVFILE=%BAT_DIR%SetTaskSchedule_config.env

:: 設定ファイル読み込み
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%ENVFILE%") do (
    if not "%%a"=="" set "%%a=%%b"
)

if "%PROCEDURE_FILE%"=="" (
    echo [ClaudeMapApp] エラー: PROCEDURE_FILE が未指定です。SetTaskSchedule_config.env を確認してください。
    echo [ClaudeMapApp] エラー: PROCEDURE_FILE が未指定です。SetTaskSchedule_config.env を確認してください。 > "%LOGFILE%"
    pause
    exit /b 1
)

echo [ClaudeMapApp] 開始: %date% %time%
echo [ClaudeMapApp] 開始: %date% %time% > "%LOGFILE%"
echo [ClaudeMapApp] 手順書: %PROCEDURE_FILE%
echo [ClaudeMapApp] 手順書: %PROCEDURE_FILE% >> "%LOGFILE%"
echo [ClaudeMapApp] ディレクトリ移動中...
echo [ClaudeMapApp] ディレクトリ移動中... >> "%LOGFILE%"
cd /d "%WORK_DIR%"
echo [ClaudeMapApp] Claude実行中...
echo [ClaudeMapApp] Claude実行中... >> "%LOGFILE%"

claude --verbose -p "タスクを実行して　%PROCEDURE_FILE%" >> "%LOGFILE%" 2>&1

if %errorlevel% neq 0 (
    echo [ClaudeMapApp] エラー発生！ 終了コード: %errorlevel%
    echo [ClaudeMapApp] エラー発生！ 終了コード: %errorlevel% >> "%LOGFILE%"
    pause
) else (
    echo [ClaudeMapApp] 完了: %date% %time%
    echo [ClaudeMapApp] 完了: %date% %time% >> "%LOGFILE%"
)
