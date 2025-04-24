@echo off
echo AI Podcast Generator
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Run the AI podcast generator
"%PYTHON_PATH%" ai_podcast_generator.py

pause
