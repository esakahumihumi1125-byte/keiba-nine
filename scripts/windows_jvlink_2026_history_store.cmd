@echo off
setlocal
title ARC RACE - private 2026 RACE history
py -3-64 "%~dp0windows_jvlink_2026_history_store.py"
set "READ_EXIT=%ERRORLEVEL%"
echo Only share status and record counts, never private files.
pause
exit /b %READ_EXIT%
