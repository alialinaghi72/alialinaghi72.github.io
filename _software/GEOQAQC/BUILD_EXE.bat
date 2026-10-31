@echo off
setlocal
title GEOQAQC 2.0 - build standalone EXE
cd /d "%~dp0"
echo.
echo  ================================================================
echo   GEOQAQC 2.0  --  building standalone Windows executables
echo  ================================================================
echo.
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo   Python was not found. Install 3.9+ from https://www.python.org/downloads/
  echo   Tick "Add python.exe to PATH" and keep "tcl/tk and IDLE" enabled.
  pause
  exit /b 1
)
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo   Could not install the build tools. Check the internet connection.
  pause
  exit /b 1
)
echo   Building ... this takes a few minutes.
%PY% -m PyInstaller --noconfirm --clean GEOQAQC.spec
if errorlevel 1 (
  echo.
  echo   BUILD FAILED. The messages above explain why.
  pause
  exit /b 1
)
echo.
echo  ================================================================
echo   Done.  dist\GEOQAQC.exe  and  dist\GEOQAQC_console.exe
echo  ================================================================
echo.
pause
endlocal
