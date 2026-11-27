@echo off
setlocal
title ARC RACE - 2026 private history workflow
py -3-64 "%~dp0windows_jvlink_history_workflow.py"
set "READ_EXIT=%ERRORLEVEL%"
pause
exit /b %READ_EXIT%
