# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build of GEOQAQC 2.0: a windowed GEOQAQC.exe and a console
# GEOQAQC_console.exe (shows error messages; runs --selftest).
#     pyinstaller --noconfirm --clean GEOQAQC.spec
import glob

from PyInstaller.utils.hooks import collect_data_files

datas = [("geoqaqc/assets", "geoqaqc/assets")]
# python-docx reads its header/footer XML templates at run time, through paths
# such as docx/parts/../templates/... -- the templates must be bundled AND the
# docx package must exist as real folders, or Word export fails in the EXE
datas += collect_data_files("docx")
datas += [(f, "sample_data") for f in glob.glob("sample_data/*.csv")]

a = Analysis(
    ["GEOQAQC.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=["matplotlib.backends.backend_tkagg", "matplotlib.backends.backend_agg",
                   "matplotlib.backends.backend_svg", "matplotlib.backends.backend_pdf",
                   "docx"],
    excludes=["pytest", "IPython", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx"],
    noarchive=False,
    module_collection_mode={"docx": "pyz+py"},
)
pyz = PYZ(a.pure)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="GEOQAQC",
          console=False, upx=False, debug=False, strip=False)
exe_console = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="GEOQAQC_console",
                  console=True, upx=False, debug=False, strip=False)
