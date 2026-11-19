@echo off
setlocal
title ARC RACE - JRA-VAN RCVN horse history source check
echo.
echo ARC RACE / RCVN horse-history availability check
echo This is a SINGLE user-initiated LOCAL RCVN read.
echo Scans up to 80,000 records or 60 seconds after JVOpen.
echo Stops early if both historical RA and SE are observed.
echo Provider-controlled JVOpen downloads may take longer.
echo It can download Data Lab. data under your existing entitlement.
echo It does not save or upload any provider records or purchase tickets.
echo No licence key or password should be typed here.
echo.
set /p "CONFIRM=Type YES to make one RCVN check, or press Enter to cancel: "
if /I not "%CONFIRM%"=="YES" (
  echo ARC_RACE_RCVN_CHECK=CANCELLED
  pause
  exit /b 0
)
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_RCVN_CHECK=PYTHON_LAUNCHER_NOT_FOUND
  pause
  exit /b 3
)
py -3-64 "%~dp0windows_jvlink_horse_data_probe.py"
set "READ_EXIT=%ERRORLEVEL%"
echo.
echo No full horse history or production prediction was created.
echo Only share the ARC_RACE_RCVN_CHECK status, not any account details.
pause
exit /b %READ_EXIT%
