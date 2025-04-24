@echo off
echo AI Podcast Generator - Web Interface
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Install required packages if needed
echo Installing required packages...
"%PYTHON_PATH%" -m pip install flask python-dotenv requests

REM Run the web interface
echo Starting web interface...
echo.
echo Once the server is running, open your browser and go to:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the server when you're done.
echo.

"%PYTHON_PATH%" web_interface.py

pause
