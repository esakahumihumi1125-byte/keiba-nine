@echo off
setlocal
title ARC RACE - combined local retrospective validation
py -3-64 "%~dp0windows_arc_race_validate_history.py"
set "READ_EXIT=%ERRORLEVEL%"
pause
exit /b %READ_EXIT%
