@echo off
setlocal
title ARC RACE - PC-only past-run 3-ren-tan research
echo.
echo ARC RACE / JRA-VAN historical observations -> study only.
echo NO new JV-Link call, NO internet, NO automatic betting.
echo Requires an already saved prestart one-race JSON.
echo The 10-factor score and JRA final starter check remain unverified.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_LOCAL_TRIFECTA=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
py -3-64 "%~dp0windows_arc_race_saved_trifecta_trial.py"
set "STUDY_EXIT=%ERRORLEVEL%"
echo.
echo If the race is eligible, the PC-only study opens.
echo Never paste passwords, source files or paid horse data to chat.
pause
exit /b %STUDY_EXIT%
