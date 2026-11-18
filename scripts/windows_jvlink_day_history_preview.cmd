@echo off
setlocal
title ARC RACE - local horse-history research (RACE + RCVN)
echo.
echo ARC RACE / local current-runners + past-results preview
echo This makes TWO Data Lab. JVOpen requests: RACE and RCVN.
echo Download size and JVOpen duration are controlled by JRA-VAN.
echo No automatic retries, real bets, or external raw-data uploads.
echo You must have valid JRA-VAN use rights and local disk space.
echo.
set /p "CONFIRM=Type YES to read RACE+RCVN once (Enter = cancel): "
if /I not "%CONFIRM%"=="YES" (
  echo ARC_RACE_DAY_HISTORY=CANCELLED
  pause
  exit /b 0
)
set /p "TARGET_DAY=Race date YYYYMMDD (Enter = next Saturday): "
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_DAY_HISTORY=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
if "%TARGET_DAY%"=="" (
  py -3-64 "%~dp0windows_jvlink_day_history_preview.py"
) else (
  py -3-64 "%~dp0windows_jvlink_day_history_preview.py" --date "%TARGET_DAY%"
)
set "READ_EXIT=%ERRORLEVEL%"
echo.
echo Only a PRIVATE research preview; not current JRA final starters or bets.
echo You may share only ARC_RACE_DAY_HISTORY=... status. No license keys.
pause
exit /b %READ_EXIT%
