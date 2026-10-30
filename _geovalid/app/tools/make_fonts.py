"""Build the chart fonts bundled in resources/fonts (all SIL OFL 1.1):
Vazirmatn Regular/Bold static TTF instances cut from the variable WOFF2, and Inter Regular/Medium/SemiBold."""
import shutil
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

res = Path(__file__).resolve().parents[1] / "geovalid_pro" / "resources"
out = res / "fonts"
out.mkdir(exist_ok=True)
for name, w in (("Regular", 400), ("Bold", 700)):
    f = TTFont(res / "Vazirmatn.woff2")
    f.flavor = None
    inst = instantiateVariableFont(f, {"wght": w})
    inst.save(out / f"Vazirmatn-{name}.ttf")
inter_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/usr/share/fonts/opentype/inter")
for name in ("Regular", "Medium", "SemiBold"):
    shutil.copy(inter_dir / f"Inter-{name}.otf", out / f"Inter-{name}.otf")
print(sorted(p.name for p in out.iterdir()))
