@echo off
echo Cloning Podcast Generator Repository
echo =====================================
echo.

REM Add Git to the PATH for this session
set PATH=%PATH%;C:\Program Files\Git\cmd

echo Checking Git installation...
git --version

echo.
echo Cloning repository...
git clone https://github.com/dharshini66/podcast-generator.git

echo.
echo If successful, the repository has been cloned to:
echo %CD%\podcast-generator
echo.

pause
