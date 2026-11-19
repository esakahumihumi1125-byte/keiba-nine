@echo off
setlocal EnableExtensions
title ARC RACE - Windows environment check
echo.
echo ========================================================
echo   ARC RACE / JRA-VAN Windows one-click readiness check
echo ========================================================
echo No racing data, password, license key or personal files are read.
echo No software will be installed or settings changed.
echo.

set "OVERALL=0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "POWERSHELL_EXE=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"

echo [1/3] Check 64-bit Python launcher...
where py >nul 2>nul
if errorlevel 1 (
    echo PYTHON64_CHECK=MISSING_LAUNCHER
    set "OVERALL=1"
    goto :check_com
)
py -3-64 -c "import struct; raise SystemExit(0 if struct.calcsize('P')==8 else 2)" >nul 2>nul
if errorlevel 1 (
    echo PYTHON64_CHECK=NOT_AVAILABLE
    set "OVERALL=1"
    goto :check_com
)
echo PYTHON64_CHECK=OK

echo [2/3] Check pywin32 in the SAME Python...
py -3-64 -c "import win32com.client" >nul 2>nul
if errorlevel 1 (
    echo PYWIN32_CHECK=NOT_INSTALLED
    set "OVERALL=1"
) else (
    echo PYWIN32_CHECK=OK
)

:check_com
echo [3/3] Check installed 64-bit JV-Link COM and JVInit...
"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows_check_jvlink.ps1"
if errorlevel 1 set "OVERALL=1"

echo.
if "%OVERALL%"=="0" (
    echo ARC_RACE_PC_READY=YES
    echo Local prerequisites passed. This does NOT verify paid data access.
    echo When you choose to fetch this week's data, run windows_jvlink_weekly_read.cmd.
) else (
    echo ARC_RACE_PC_READY=NO
    echo Only share the CHECK status lines, never passwords, license keys or screenshots of account details.
    echo Missing Python or pywin32 must be installed separately before any live read.
)
echo.
pause
exit /b %OVERALL%
