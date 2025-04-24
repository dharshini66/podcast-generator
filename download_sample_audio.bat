@echo off
echo Downloading Sample Audio for Testing
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Run the sample audio download script
"%PYTHON_PATH%" download_sample_audio.py

pause
