@echo off
setlocal
title ARC RACE - saved all-flat race history study (offline)
echo.
echo ARC RACE / saved all-flat historical 3-ren-tan study
echo Uses ONLY previously saved local jvdata-all-flat-races JSON.
echo NO JRA-VAN, JRDB, network, betting, or paid API requests.
echo The result is not official JRA verification or a 10-factor prediction.
echo.
set /p "TARGET_DAY=Date YYYYMMDD (Enter = today in Japan): "
where py >nul 2>nul
if errorlevel 1 (
  echo ARC_RACE_ALL_FLAT_STUDY=PYTHON_LAUNCHER_UNAVAILABLE
  pause
  exit /b 3
)
if "%TARGET_DAY%"=="" (
  py -3-64 "%~dp0windows_arc_race_saved_all_flat_trifecta_trial.py"
) else (
  py -3-64 "%~dp0windows_arc_race_saved_all_flat_trifecta_trial.py" --date "%TARGET_DAY%"
)
set "READ_EXIT=%ERRORLEVEL%"
echo.
echo Study only. Do not use as final wagers or import into real ROI.
pause
exit /b %READ_EXIT%
