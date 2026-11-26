@echo off
setlocal
title ARC RACE - private workout validation
py -3-64 "%~dp0windows_jvlink_workout_pair_study.py"
set "READ_EXIT=%ERRORLEVEL%"
pause
exit /b %READ_EXIT%
