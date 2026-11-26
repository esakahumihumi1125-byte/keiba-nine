@echo off
setlocal
title ARC RACE - retrospective course research
py -3-64 "%~dp0windows_jvlink_history_walkforward.py"
set "READ_EXIT=%ERRORLEVEL%"
pause
exit /b %READ_EXIT%
