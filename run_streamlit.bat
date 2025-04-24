@echo off
echo Meeting to Podcast AI Agent - Streamlit App
echo =========================================
echo.
echo Setting up environment...

REM Create necessary directories
mkdir uploads 2>nul
mkdir output_podcasts 2>nul
mkdir temp_audio 2>nul
mkdir static\img 2>nul

REM Create a placeholder logo if it doesn't exist
if not exist static\img\logo.png (
    echo Creating placeholder logo...
    copy nul static\img\logo.png >nul 2>&1
)

echo.
echo Using Python installation: C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe
echo.
echo Installing dependencies...
echo (This may take a few minutes if packages need to be installed)
echo.

REM Use the specific Python installation
set PYTHON_CMD="C:\Users\dhars\AppData\Local\Programs\Python\Python313\python.exe"

REM Install dependencies
%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Starting the Streamlit application...
echo.
echo Once the application is running, open your browser and go to:
echo http://localhost:8501
echo.

REM Run the Streamlit application
%PYTHON_CMD% -m streamlit run streamlit_app.py

echo.
echo Application stopped.
echo Press any key to exit...
pause >nul
