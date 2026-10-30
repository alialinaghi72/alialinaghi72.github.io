"""Visual identity shared by charts, report and app: palettes, colour maps, fonts, Persian text shaping.

Two themes: "ivory" (light, printed report) and "obsidian" (dark, desktop app).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources

import matplotlib
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

# Categorical palette: deep teal, copper, gold, indigo, sage, raspberry, azure, moss, clay, slate, plum, sand
CAT = ["#0F7173", "#D08C60", "#E9B44C", "#4F5D95", "#8FBFB0", "#B8336A", "#3E8EDE", "#7A9E7E", "#C1666B", "#5D737E",
       "#8E5572", "#D4B483"]
SEVERITY = {"CRITICAL": "#9B2226", "ERROR": "#CA6702", "WARNING": "#EE9B00", "INFO": "#0A9396", None: "#A6ADB4"}
METHOD = {"SURVEYED": "#0A9396", "HANDHELD_GPS": "#EE9B00", "PLANNED": "#CA6702", "DIGITISED": "#8E5572", "UNKNOWN": "#A6ADB4"}

SEQ = LinearSegmentedColormap.from_list("gv_seq", ["#FBF7EF", "#F1DFB0", "#E9B44C", "#5BA89B", "#0F7173", "#073B4C"])
SEQ_DARK = LinearSegmentedColormap.from_list("gv_seq_dark", ["#101820", "#0F4C5C", "#0F7173", "#5BA89B", "#E9B44C", "#F6E7C1"])
DIV = LinearSegmentedColormap.from_list("gv_div", ["#073B4C", "#0F7173", "#8FBFB0", "#F7F3EA", "#E9B44C", "#CA6702", "#9B2226"])
DIV_DARK = LinearSegmentedColormap.from_list("gv_div_dark", ["#8FD3D6", "#2A9D8F", "#1D4E5A", "#1B2530", "#6B4A2B", "#D08C60", "#F6C98F"])
GRADE = LinearSegmentedColormap.from_list("gv_grade", ["#2C3E50", "#3E6C8C", "#3FA7A3", "#9BD08A", "#F4D35E", "#EE964B", "#D1495B"])
for cm in (SEQ, SEQ_DARK, DIV, DIV_DARK, GRADE):
    try:
        matplotlib.colormaps.register(cm)
    except ValueError:
        pass


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    panel: str
    ink: str
    muted: str
    grid: str
    axis: str
    accent: str
    seq: object
    div: str = "gv_div"

    @property
    def dark(self) -> bool:
        return self.name == "obsidian"


IVORY = Theme("ivory", "#FFFFFF", "#FFFFFF", "#1E2A32", "#5F6B76", "#E7EBEE", "#9AA5AE", "#B07D3A", SEQ)
OBSIDIAN = Theme("obsidian", "#18202A", "#18202A", "#ECE6DA", "#9AA3AE", "#26303C", "#4A5563", "#D4A85A", SEQ_DARK, "gv_div_dark")

_FONTS_DONE = False
LATIN = "Inter"
PERSIAN = "Vazirmatn"


def register_fonts() -> None:
    """Make the bundled Inter and Vazirmatn available to matplotlib (identical look on every computer)."""
    global _FONTS_DONE
    if _FONTS_DONE:
        return
    import logging
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # "semibold → 700" substitutions are expected
    try:
        folder = resources.files("geovalid_pro.resources").joinpath("fonts")
        for f in folder.iterdir():
            if f.name.lower().endswith((".ttf", ".otf")):
                with resources.as_file(f) as path:
                    font_manager.fontManager.addfont(str(path))
    except Exception:
        pass
    # Font family is resolved when a figure is drawn, not when it is built, so it is set globally (same in both themes).
    # A list of families (not the generic "sans-serif") enables per-glyph fallback: Latin from Inter, Persian from Vazirmatn.
    matplotlib.rcParams["font.family"] = [LATIN, PERSIAN, "DejaVu Sans"]
    _FONTS_DONE = True


# Conventional colours for common logging codes (alteration, weathering, intensity); other codes take CAT in order.
KNOWN = {
    "POTASSIC": "#D1495B", "K": "#D1495B", "PHYLLIC": "#E9B44C", "SERICITIC": "#E9B44C", "QSP": "#E9B44C",
    "ARGILLIC": "#B8A99A", "ADVANCED_ARGILLIC": "#9D8189", "AARG": "#9D8189", "PROPYLITIC": "#5BA89B", "PROP": "#5BA89B",
    "SILICIC": "#8FA3BF", "SKARN": "#7A9E7E", "OXIDE": "#B5562E", "OX": "#B5562E", "LEACHED": "#C9B79C", "LEACH": "#C9B79C",
    "MIXED": "#D4A85A", "TRANSITION": "#D4A85A", "TRANS": "#D4A85A", "SUPERGENE": "#D08C60", "PRIMARY": "#3E6C8C",
    "FRESH": "#3E6C8C", "HYPOGENE": "#3E6C8C", "SULPHIDE": "#3E6C8C", "STRONG": "#9B2226", "MODERATE": "#CA6702",
    "WEAK": "#E9D8A6", "ALLUV": "#C9B79C", "COVER": "#C9B79C", "OB": "#C9B79C",
}


def cat_colours(categories) -> dict:
    """Stable colour per category: conventional colour when known, otherwise the categorical palette in order."""
    out, k = {}, 0
    for c in categories:
        key = str(c).upper()
        if key in KNOWN and KNOWN[key] not in out.values():
            out[c] = KNOWN[key]
        else:
            while CAT[k % len(CAT)] in out.values() and k < 3 * len(CAT):
                k += 1
            out[c] = CAT[k % len(CAT)]
            k += 1
    return out


def rc(theme: Theme = IVORY) -> dict:
    return {
        "font.family": [LATIN, PERSIAN, "DejaVu Sans"],
        "font.size": 9, "axes.titlesize": 10.5, "axes.titleweight": "semibold", "axes.titlelocation": "left",
        "axes.titlepad": 10, "axes.labelsize": 9, "axes.labelcolor": theme.muted, "axes.edgecolor": theme.axis,
        "axes.linewidth": 0.8, "axes.facecolor": theme.panel, "figure.facecolor": theme.bg,
        "savefig.facecolor": theme.bg, "text.color": theme.ink, "axes.titlecolor": theme.ink,
        "xtick.color": theme.muted, "ytick.color": theme.muted, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": theme.grid,
        "grid.linewidth": 0.7, "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 8,
        "axes.prop_cycle": matplotlib.cycler(color=CAT), "figure.dpi": 110, "savefig.dpi": 160,
        "image.cmap": "gv_seq", "figure.edgecolor": theme.bg, "patch.edgecolor": theme.bg,
    }


def apply(theme: Theme = IVORY) -> None:
    register_fonts()
    matplotlib.rcParams.update(rc(theme))


_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
_SHAPED = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")


def _native_rtl() -> bool:
    """Matplotlib ≥ 3.11 lays out text with libraqm (bidi + Arabic-script shaping): pass Persian through unchanged."""
    try:
        from matplotlib import ft2font
        return bool(getattr(ft2font, "__libraqm_version__", None))
    except Exception:
        return False


NATIVE_RTL = _native_rtl()


def fa(text: str, lang: str = "fa") -> str:
    """Persian text ready for matplotlib: unchanged with native layout, otherwise reshaped and reordered (fallback)."""
    if NATIVE_RTL or not text or not isinstance(text, str) or not _ARABIC.search(text) or _SHAPED.search(text):
        return text     # nothing to shape, or already shaped (idempotent)
    try:
        import arabic_reshaper
        from bidi import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def label(fa_text: str, en_text: str, lang: str) -> str:
    return fa(fa_text, lang) if lang == "fa" else en_text
