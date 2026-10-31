@echo off
setlocal
title GEOQAQC 2.0 - Analytical Quality Control Suite
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo.
  echo   Python was not found on this computer.
  echo   Install Python 3.9 or newer from  https://www.python.org/downloads/
  echo   During setup, TICK  "Add python.exe to PATH"  and keep the
  echo   default "tcl/tk and IDLE" option enabled.
  echo.
  pause
  exit /b 1
)
%PY% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo   Tkinter is missing. Re-run the Python installer and enable "tcl/tk and IDLE".
  pause
  exit /b 1
)
%PY% -c "import matplotlib, docx" >nul 2>&1
if errorlevel 1 (
  echo   Installing the two packages GEOQAQC needs: matplotlib and python-docx ...
  %PY% -m pip install --upgrade pip
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo   Could not install the packages. Check the internet connection.
    pause
    exit /b 1
  )
)
%PY% GEOQAQC.py
if errorlevel 1 (
  echo.
  echo   GEOQAQC exited with an error. The message above explains why.
  pause
)
endlocal
