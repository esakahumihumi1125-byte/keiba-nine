@echo off
setlocal
title ARC RACE - saved course-match gap diagnosis (offline)
echo.
echo ARC RACE / saved past-runs comparability check
echo Only your EXISTING private sanitized JSON is read.
echo NO JRA-VAN, JRDB, Internet, new paid calls or bets.
echo This is NOT a scored forecast or a ticket.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_COMPARABILITY=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
py -3-64 "%~dp0windows_arc_race_saved_comparability_diagnose.py"
set "DIAG_EXIT=%ERRORLEVEL%"
echo.
echo Share only NUMBER and REASON if needed; no JSON or API keys.
pause
exit /b %DIAG_EXIT%
