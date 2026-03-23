@echo off
setlocal

set BAT_DIR=%~dp0
for %%i in ("%BAT_DIR%..\..") do set WORK_DIR=%%~fi
set LOGFILE=%BAT_DIR%SetTaskSchedule.log
set ENVFILE=%BAT_DIR%SetTaskSchedule_config.env

:: デバッグログ（ウィンドウとファイル両方に書き込む）
echo [DEBUG] BAT起動
echo [DEBUG] BAT起動 > "%LOGFILE%"
echo [DEBUG] BAT_DIR=%BAT_DIR%
echo [DEBUG] BAT_DIR=%BAT_DIR% >> "%LOGFILE%"
echo [DEBUG] WORK_DIR=%WORK_DIR%
echo [DEBUG] WORK_DIR=%WORK_DIR% >> "%LOGFILE%"
echo [DEBUG] LOGFILE=%LOGFILE%
echo [DEBUG] LOGFILE=%LOGFILE% >> "%LOGFILE%"
echo [DEBUG] ENVFILE=%ENVFILE%
echo [DEBUG] ENVFILE=%ENVFILE% >> "%LOGFILE%"
if exist "%ENVFILE%" (
    echo [DEBUG] config.env 存在あり
    echo [DEBUG] config.env 存在あり >> "%LOGFILE%"
) else (
    echo [DEBUG] config.env が見つからない!
    echo [DEBUG] config.env が見つからない! >> "%LOGFILE%"
    pause
    exit /b 1
)

:: 設定ファイル読み込み
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%ENVFILE%") do (
    if not "%%a"=="" set "%%a=%%b"
)
echo [DEBUG] STEP: env読み込み完了 >> "%LOGFILE%"
echo [DEBUG] PROCEDURE_FILE=%PROCEDURE_FILE%
echo [DEBUG] PROCEDURE_FILE=%PROCEDURE_FILE% >> "%LOGFILE%"
echo [DEBUG] MODE=%MODE%
echo [DEBUG] MODE=%MODE% >> "%LOGFILE%"
echo [DEBUG] CLAUDE_CODE_EXEC_DIR=%CLAUDE_CODE_EXEC_DIR%
echo [DEBUG] CLAUDE_CODE_EXEC_DIR=%CLAUDE_CODE_EXEC_DIR% >> "%LOGFILE%"

:: CLAUDE_CODE_EXEC_DIR が設定されていればそちらを使用
if not "%CLAUDE_CODE_EXEC_DIR%"=="" set WORK_DIR=%CLAUDE_CODE_EXEC_DIR%
echo [DEBUG] 実行ディレクトリ(決定)=%WORK_DIR%
echo [DEBUG] 実行ディレクトリ(決定)=%WORK_DIR% >> "%LOGFILE%"

:: モード判定
echo [DEBUG] STEP: モード判定 >> "%LOGFILE%"
if "%~1"=="--prod" (
    set MODE=prod
) else if "%~1"=="--dev" (
    set MODE=dev
) else if "%MODE%"=="" (
    set MODE=dev
)
if "%MODE%"=="prod" (
    set "MODE_LABEL=本番(prod)で、"
) else (
    set MODE=dev
    set "MODE_LABEL=開発(dev)で、"
)
echo [DEBUG] MODE(決定)=%MODE% >> "%LOGFILE%"

echo [DEBUG] STEP: PROCEDURE_FILEチェック >> "%LOGFILE%"
if "%PROCEDURE_FILE%"=="" (
    echo [ClaudeMapApp] エラー: PROCEDURE_FILE が未指定です。
    echo [ClaudeMapApp] エラー: PROCEDURE_FILE が未指定です。 >> "%LOGFILE%"
    pause
    exit /b 1
)

echo [DEBUG] STEP: cd前 >> "%LOGFILE%"
echo [ClaudeMapApp] 開始: %date% %time%
echo [ClaudeMapApp] 開始: %date% %time% >> "%LOGFILE%"
echo [ClaudeMapApp] モード: %MODE% >> "%LOGFILE%"
echo [ClaudeMapApp] 手順書: %PROCEDURE_FILE% >> "%LOGFILE%"
echo [ClaudeMapApp] 実行ディレクトリ: %WORK_DIR% >> "%LOGFILE%"
cd /d "%WORK_DIR%"
echo [DEBUG] STEP: cd完了 >> "%LOGFILE%"
echo [ClaudeMapApp] Claude実行中...
echo [ClaudeMapApp] Claude実行中... >> "%LOGFILE%"

claude --verbose -p "%MODE_LABEL%次の手順書に従ってタスクを実行してください: @%PROCEDURE_FILE%" >> "%LOGFILE%" 2>&1
set CLAUDE_EXIT=%errorlevel%

echo [DEBUG] STEP: claude終了 errorlevel=%CLAUDE_EXIT% >> "%LOGFILE%"
if %CLAUDE_EXIT% neq 0 (
    echo [ClaudeMapApp] エラー発生！ 終了コード: %CLAUDE_EXIT%
    echo [ClaudeMapApp] エラー発生！ 終了コード: %CLAUDE_EXIT% >> "%LOGFILE%"
) else (
    echo [ClaudeMapApp] 完了: %date% %time%
    echo [ClaudeMapApp] 完了: %date% %time% >> "%LOGFILE%"
)
echo [ClaudeMapApp] 終了。キーを押すと閉じます。
pause
