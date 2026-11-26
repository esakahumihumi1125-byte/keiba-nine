@echo off
setlocal
title ARC RACE - private workout archive
py -3-64 "%~dp0windows_jvlink_workout_store.py"
set "READ_EXIT=%ERRORLEVEL%"
pause
exit /b %READ_EXIT%
