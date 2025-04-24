@echo off
echo AI Podcast Generator - Automated Demo
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Run the automated demo script
"%PYTHON_PATH%" run_demo.py

pause
