@echo off
setlocal
title ARC RACE - saved past-runs evidence check (offline only)
echo.
echo ARC RACE / OFFLINE 10-factor input-coverage review
echo Reads only an existing sanitized one-race JSON from this PC.
echo No JRA-VAN / JV-Link / JRDB / internet requests, no bets.
echo This is NOT a formal forecast or a 3-ren-tan ticket.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_OFFLINE_EVIDENCE=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
py -3-64 "%~dp0windows_arc_race_saved_history_review.py"
set "READ_EXIT=%ERRORLEVEL%"
echo.
echo If a local report exists for today, its factor-evidence HTML opens.
echo Only share ARC_RACE_OFFLINE_EVIDENCE=... status if needed.
pause
exit /b %READ_EXIT%
