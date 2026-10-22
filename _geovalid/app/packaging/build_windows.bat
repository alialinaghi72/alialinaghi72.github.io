@echo off
rem Build GEOVALID PRO for Windows (run from the _geovalid\app folder; needs Python 3.12 x64).
py -3.12 -m venv .venv || goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller==6.22.3 pytest || goto :error
python -m pytest -q || goto :error
python tools\make_icon.py
pyinstaller --noconfirm --clean packaging\geovalid.spec || goto :error
dist\GEOVALID\geovalid-cli.exe sample --out dist\GEOVALID
copy /Y README_RUN.md dist\GEOVALID\
echo.
echo Built: dist\GEOVALID\GEOVALID.exe
goto :eof
:error
echo Build failed.
exit /b 1
