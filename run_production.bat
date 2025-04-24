@echo off
echo AI Podcast Generator - Production Version
echo =====================================
echo.

REM Find Python installation
set PYTHON_PATH=C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe

echo Using Python installation: %PYTHON_PATH%
echo.

REM Check if an audio file was provided
if "%~1"=="" (
    echo No audio file provided.
    echo Usage: run_production.bat [audio_file_path] [title]
    echo.
    echo Example: run_production.bat meeting_recording.mp3 "Quarterly Meeting"
    goto :end
)

REM Check if the audio file exists
if not exist "%~1" (
    echo Error: Audio file not found at %~1
    goto :end
)

echo Processing audio file: %~1
if not "%~2"=="" (
    echo Title: %~2
    echo.
    "%PYTHON_PATH%" production_podcast_generator.py "%~1" "%~2"
) else (
    echo.
    "%PYTHON_PATH%" production_podcast_generator.py "%~1"
)

:end
pause
