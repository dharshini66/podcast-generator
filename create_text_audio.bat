@echo off
echo Creating Simulated Audio for Testing
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Run the text audio simulation script
"%PYTHON_PATH%" create_text_audio.py

pause
