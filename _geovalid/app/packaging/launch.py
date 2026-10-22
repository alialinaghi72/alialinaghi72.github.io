"""PyInstaller entry point (GEOVALID.exe = GUI, geovalid-cli.exe = console)."""
import sys

from geovalid_pro.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
