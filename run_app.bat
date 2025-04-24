@echo off
echo Meeting to Podcast AI Agent
echo ========================
echo.
echo Setting up environment...

REM Create necessary directories
mkdir uploads 2>nul
mkdir output_podcasts 2>nul
mkdir temp_audio 2>nul

echo.
echo Installing dependencies...
echo (This may take a few minutes if packages need to be installed)
echo.

REM Try to find Python in common installation locations
set PYTHON_FOUND=0

REM Check for standard Python installations
for %%p in (
  python
  python3
  C:\Python39\python.exe
  C:\Python38\python.exe
  C:\Python37\python.exe
  C:\Python310\python.exe
  C:\Python311\python.exe
  C:\Python312\python.exe
  C:\Program Files\Python39\python.exe
  C:\Program Files\Python38\python.exe
  C:\Program Files\Python37\python.exe
  C:\Program Files\Python310\python.exe
  C:\Program Files\Python311\python.exe
  C:\Program Files\Python312\python.exe
  C:\Program Files (x86)\Python39\python.exe
  C:\Program Files (x86)\Python38\python.exe
  C:\Program Files (x86)\Python37\python.exe
  C:\Program Files (x86)\Python310\python.exe
  C:\Program Files (x86)\Python311\python.exe
  C:\Program Files (x86)\Python312\python.exe
  %LOCALAPPDATA%\Programs\Python\Python39\python.exe
  %LOCALAPPDATA%\Programs\Python\Python38\python.exe
  %LOCALAPPDATA%\Programs\Python\Python37\python.exe
  %LOCALAPPDATA%\Programs\Python\Python310\python.exe
  %LOCALAPPDATA%\Programs\Python\Python311\python.exe
  %LOCALAPPDATA%\Programs\Python\Python312\python.exe
) do (
  %%p --version >nul 2>&1
  if not errorlevel 1 (
    set PYTHON_CMD=%%p
    set PYTHON_FOUND=1
    goto python_found
  )
)

:python_found
if %PYTHON_FOUND%==0 (
  echo Python not found! Please install Python 3.7+ and make sure it's in your PATH.
  echo.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)

echo Found Python: %PYTHON_CMD%
echo.

REM Install dependencies
%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Starting the application...
echo.
echo Once the application is running, open your browser and go to:
echo http://localhost:5000
echo.

REM Run the Flask application
%PYTHON_CMD% app.py

echo.
echo Application stopped.
echo Press any key to exit...
pause >nul
