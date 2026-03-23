@echo off
set LOGFILE=%~dp0SetTaskSchedule.log
echo ƒƒOŠÄ‹’†... (’â~: Ctrl+C)
echo.
powershell -Command "Get-Content '%LOGFILE%' -Wait -Encoding Default"
