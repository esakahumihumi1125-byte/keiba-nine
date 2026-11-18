@echo off
setlocal
title ARC RACE - this-week JRA-VAN local data check
echo.
echo ARC RACE / JRA-VAN weekly RA+SE candidate read
echo This attempts ONE local JV-Link weekly data fetch.
echo No registration key is entered here. No bets or predictions are made.
echo.
set /p "TARGET_DAY=Race date YYYYMMDD (example: 20261121): "
if "%TARGET_DAY%"=="" (
  echo No race date entered.
  pause
  exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher is unavailable. Please install 64-bit Python first.
  pause
  exit /b 3
)
py -3 "%~dp0windows_jvlink_weekly_read.py" --date "%TARGET_DAY%"
set "READ_EXIT=%ERRORLEVEL%"
echo.
if "%READ_EXIT%"=="0" (
  echo Private racecard candidates saved under %LOCALAPPDATA%\ARC-RACE-private.
  echo These are not independently verified JRA official final starters.
) else (
  echo No complete candidate file was saved. Keep the error status above.
  echo If PYWIN32_NOT_INSTALLED appears, install pywin32 in the same Python.
)
pause
exit /b %READ_EXIT%
