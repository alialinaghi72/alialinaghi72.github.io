# -*- coding: utf-8 -*-
"""HTML -> PDF with a Chromium browser in headless mode. Microsoft Edge ships
with every Windows 10/11, so no extra software is needed on the user's side;
Chrome or Chromium are used when Edge is absent. GEOQAQC_BROWSER overrides the
search."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_WIN = [
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
]
_MAC = ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium"]
_PATH = ["msedge", "microsoft-edge", "google-chrome", "google-chrome-stable",
         "chromium", "chromium-browser", "chrome"]

# Windows: a profile of its own for each print. On the user's shared profile an
# Edge window that is already open (or Edge's startup boost) takes the job over
# and prints nothing. Elsewhere the default profile is kept: a full Chromium in
# a bare Linux container stalls on a fresh profile.
PRIVATE_PROFILE = os.name == "nt"

NO_BROWSER = ("Microsoft Edge, Google Chrome or Chromium was not found, so the PDF "
              "could not be made. Open the HTML report in any browser and print it "
              "to PDF (A4, no headers and footers). — مرورگر Edge یا Chrome پیدا نشد؛ "
              "گزارش HTML را در مرورگر باز کنید و با گزینهٔ چاپ به PDF ذخیره کنید.")


def find_browser():
    env = os.environ.get("GEOQAQC_BROWSER")
    if env and os.path.isfile(env):
        return env
    for c in _WIN:
        p = os.path.expandvars(c)
        if "%" not in p and os.path.isfile(p):
            return p
    for p in _MAC:
        if os.path.isfile(p):
            return p
    for name in _PATH:
        p = shutil.which(name)
        if p:
            return p
    return None


def html_to_pdf(html_path, pdf_path, browser=None, timeout=240):
    browser = browser or find_browser()
    if not browser:
        raise RuntimeError(NO_BROWSER)
    pdf_path = str(Path(pdf_path).resolve())
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    profile = tempfile.mkdtemp(prefix="geoqaqc_browser_") if PRIVATE_PROFILE else None
    args = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            f"--print-to-pdf={pdf_path}", Path(html_path).resolve().as_uri()]
    if profile:
        args.insert(-2, f"--user-data-dir={profile}")
    if os.name != "nt":
        args.insert(1, "--no-sandbox")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=timeout, creationflags=flags, check=False)
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise RuntimeError(f"The browser could not print the report: {ex}")
    finally:
        if profile:
            shutil.rmtree(profile, ignore_errors=True)
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
        raise RuntimeError("The browser ran but wrote no PDF. " + NO_BROWSER)
    return pdf_path
