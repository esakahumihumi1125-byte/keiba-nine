@echo off
setlocal
title ARC RACE - all upcoming flat races, local history only
echo.
echo ARC RACE / all upcoming flat racecards + partial RCVN history
echo Single owner-triggered RACE read + single RCVN read only.
echo No JRA final verification, automatic purchases, or external uploads.
echo Saves one local all-flat-races JSON and HTML only.
echo Existing per-race files are never overwritten.
echo.
set /p "CONFIRM=Type YES to read RACE + RCVN once (Enter = cancel): "
if /I not "%CONFIRM%"=="YES" (
  echo ARC_RACE_ALL_FLAT=CANCELLED
  pause
  exit /b 0
)
set /p "TARGET_DAY=Race date YYYYMMDD (Enter = today Sat/Sun, else next Saturday): "
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_ALL_FLAT=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
if "%TARGET_DAY%"=="" (
  py -3-64 "%~dp0windows_jvlink_day_history_preview.py" --all-flat-races
) else (
  py -3-64 "%~dp0windows_jvlink_day_history_preview.py" --all-flat-races --date "%TARGET_DAY%"
)
set "READ_EXIT=%ERRORLEVEL%"
echo.
echo Multi-race local research is NOT verified JRA final starters or formal 10-factor forecasts.
echo Only share status lines, never credentials or private files.
pause
exit /b %READ_EXIT%
