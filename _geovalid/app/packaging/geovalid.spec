# PyInstaller spec: one-folder build with two executables sharing one runtime (01 §14, decision A15).
#   GEOVALID.exe      windowed GUI (also accepts CLI commands)
#   geovalid-cli.exe  console build for batch use:  geovalid-cli run --files ... --out ...
import os

here = os.path.abspath(os.path.join(SPECPATH, ".."))
res = os.path.join(here, "geovalid_pro", "resources")
icon = os.path.join(res, "icon.ico") if os.path.exists(os.path.join(res, "icon.ico")) else None

a = Analysis(
    [os.path.join(here, "packaging", "launch.py")],
    pathex=[here],
    datas=[(res, "geovalid_pro/resources")],
    hiddenimports=["scipy.spatial", "scipy.interpolate", "scipy.stats", "openpyxl", "xlrd", "charset_normalizer",
                   "matplotlib.backends.backend_agg", "yaml", "geovalid_pro.gui.app", "geovalid_pro.cli"],
    excludes=["tkinter", "IPython", "pytest", "playwright", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
              "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore", "PySide6.QtMultimedia",
              "PySide6.QtBluetooth", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner"],
    noarchive=False,
)
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name="GEOVALID", console=False, icon=icon)
cli = EXE(pyz, a.scripts, [], exclude_binaries=True, name="geovalid-cli", console=True, icon=icon)
coll = COLLECT(gui, cli, a.binaries, a.datas, name="GEOVALID")
