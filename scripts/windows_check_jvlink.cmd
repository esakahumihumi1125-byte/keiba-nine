@echo off
setlocal
title ARC RACE - JV-Link local check
echo.
echo ARC RACE / JRA-VAN Data Lab - local JV-Link check
echo This only checks Windows COM and JVInit. No race data is read.
echo.
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "POWERSHELL_EXE=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows_check_jvlink.ps1"
set "CHECK_EXIT=%ERRORLEVEL%"
echo.
if "%CHECK_EXIT%"=="0" (
  echo RESULT: Local JV-Link initialization passed. Official data NOT imported.
) else (
  echo RESULT: Check was not successful. Exit code: %CHECK_EXIT%
)
echo You may close this window. No credentials should be pasted or shared.
pause
exit /b %CHECK_EXIT%
