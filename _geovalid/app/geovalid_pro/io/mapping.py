"""Automatic field mapping and table-type detection (brief §2.2; 02 §4 synonym columns)."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

import pandas as pd

from ..core.normalise import header_key

KINDS = ["collar", "survey", "assay", "lithology", "alteration", "weathering", "geotech", "density", "interval", "ignore"]

SYN: dict[str, list[str]] = {
    "hole_id": ["holeid", "hole", "bhid", "hole_id", "holeno", "holename", "drillhole", "dhid", "borehole", "bh", "bhno",
                "holenumber", "hole_name", "id", "شمارهگمانه", "گمانه", "نامگمانه", "کدگمانه", "شمارهچاه", "شماره"],
    "x": ["x", "east", "easting", "eastm", "utme", "utmeast", "e", "xcollar", "xutm", "coordx", "xcoord", "طول",
          "ایستینگ", "شرقی", "مختصاتx", "xm"],
    "y": ["y", "north", "northing", "northm", "utmn", "utmnorth", "n", "ycollar", "yutm", "coordy", "ycoord", "عرض",
          "نورثینگ", "شمالی", "مختصاتy", "ym"],
    "z": ["z", "rl", "elev", "elevation", "height", "alt", "altitude", "zcollar", "collarrl", "zm", "ارتفاع", "تراز", "رقوم"],
    "eoh_m": ["eoh", "eohm", "maxdepth", "maxdepthm", "depth", "totaldepth", "td", "length", "holelength", "finaldepth",
              "enddepth", "depthm", "عمق", "عمقنهایی", "طولگمانه", "عمقکل"],
    "azimuth": ["azimuth", "azi", "az", "bearing", "brg", "azim", "آزیموت", "امتداد", "سمت"],
    "dip": ["dip", "inclination", "inc", "incl", "angle", "plunge", "شیب", "زاویه"],
    "depth_m": ["depth", "at", "distance", "surveydepth", "md", "depthm", "atm", "عمق"],
    "from_m": ["from", "fromm", "depthfrom", "start", "startm", "از", "ازعمق", "عمقاز"],
    "to_m": ["to", "tom", "depthto", "end", "endm", "تا", "تاعمق", "عمقتا"],
    "sample_id": ["sample", "sampleid", "sampleno", "sampno", "samplenumber", "tag", "ticket", "شمارهنمونه", "کدنمونه", "نمونه"],
    "sample_type": ["sampletype", "samptype", "qctype", "qaqc", "qaqctype", "sampleclass", "type", "نوعنمونه"],
    "parent_id": ["parent", "parentid", "parentsample", "original", "origid", "originalsample", "dupof", "نمونهاصلی"],
    "crm_id": ["standard", "stdid", "crm", "crmid", "stdname", "standardid", "refmaterial", "استاندارد"],
    "batch": ["batch", "batchid", "job", "labjob", "jobno", "certificate", "workorder", "بچ"],
    "lith_code": ["lith", "lithology", "lith1", "lithcode", "rock", "rocktype", "rockcode", "geology", "geol", "unit",
                  "سنگشناسی", "لیتولوژی", "نوعسنگ", "سنگ", "واحدسنگی"],
    "alt_type": ["alt", "alteration", "alt1", "alttype", "دگرسانی"],
    "weathering": ["weath", "weathering", "wth", "ox", "oxidation", "oxzone", "هوازدگی", "اکسیداسیون"],
    "cr_pct": ["recovery", "rec", "cr", "corerec", "tcr", "recpct", "corerecovery", "بازیافت", "مغزهدهی"],
    "rqd_pct": ["rqd", "rqdpct"],
    "run_length_m": ["run", "runlength", "runlen", "drilled", "طولران"],
    "recovered_length_m": ["recm", "recovered", "recoveredm", "corerecm", "tcrm", "طولمغزه"],
    "rqd_length_m": ["rqdm", "rqdlength", "sum10cm", "l10"],
    "density": ["density", "sg", "bd", "bulkdensity", "dens", "specificgravity", "dbd", "چگالی", "وزنمخصوص", "دانسیته"],
    "date_started": ["startdate", "datestart", "started", "datestarted", "drillstart", "تاریخشروع"],
    "date_completed": ["enddate", "dateend", "finishdate", "completed", "datecompleted", "dateend", "تاریخپایان"],
    "drill_method": ["holetype", "drilltype", "method", "drillmethod", "drillingmethod", "نوعحفاری", "روشحفاری"],
    "rig": ["rig", "rigid", "rigno", "دستگاه", "دستگاهحفاری"],
    "campaign": ["campaign", "phase", "program", "programme", "فاز", "مرحله"],
    "collar_survey_method": ["surveymethod", "collarmethod", "locmethod", "coordmethod", "روشبرداشت"],
    "instrument": ["instrument", "tool", "surveytool", "surveytype", "ابزار"],
}

FIELDS: dict[str, tuple[list[str], list[str]]] = {   # kind: (required, optional)
    "collar": (["hole_id", "x", "y", "z"], ["eoh_m", "azimuth", "dip", "date_started", "date_completed", "drill_method",
                                           "rig", "campaign", "collar_survey_method"]),
    "survey": (["hole_id", "depth_m"], ["azimuth", "dip", "instrument"]),
    "assay": (["hole_id", "from_m", "to_m"], ["sample_id", "sample_type", "parent_id", "crm_id", "batch"]),
    "lithology": (["hole_id", "from_m", "to_m", "lith_code"], []),
    "alteration": (["hole_id", "from_m", "to_m", "alt_type"], []),
    "weathering": (["hole_id", "from_m", "to_m", "weathering"], []),
    "geotech": (["hole_id", "from_m", "to_m"], ["cr_pct", "rqd_pct", "run_length_m", "recovered_length_m", "rqd_length_m"]),
    "density": (["hole_id", "density"], ["from_m", "to_m", "depth_m", "sample_id"]),
    "interval": (["hole_id", "from_m", "to_m"], []),
    "ignore": ([], []),
}
INTERVAL_KINDS = {"assay", "lithology", "alteration", "weathering", "geotech", "interval"}

ELEMENTS = ("Au Ag Cu Mo Pb Zn Fe Mn Ni Co Cr As Sb Bi S Te Hg W Sn U Th V Ti Al Ca Mg Na K P Ba Sr Li Be B Cd In Re Se Tl "
            "Pt Pd Rh Ga Ge Nb Ta Zr Hf Y La Ce Nd Sc Rb Cs F C Si").split()
OXIDES = "SiO2 TiO2 Al2O3 Fe2O3 Fe2O3T FeO MnO MgO CaO Na2O K2O P2O5 Cr2O3 BaO SrO SO3 V2O5 LOI CuO ZnO PbO NiO".split()
_ANALYTE_SET = {a.lower(): a for a in ELEMENTS + OXIDES}
UNITS = {"ppm": "ppm", "ppb": "ppb", "pct": "%", "%": "%", "per": "%", "percent": "%", "gt": "g/t", "g/t": "g/t",
         "gpt": "g/t", "gpton": "g/t", "ozt": "oz/t", "oz/t": "oz/t", "opt": "oz/t", "درصد": "%"}
_PARTIAL = {"as", "ox", "ac", "cn", "sol", "asol", "oxide", "acid", "seq", "res"}


@dataclass
class AnalyteColumn:
    column: str
    analyte: str
    unit: str | None        # declared unit, None when absent
    qualifier: str          # method / repeat / partial tokens
    partial: bool = False   # acid-soluble, cyanide-soluble, oxide fraction


_ALL_ANALYTES = sorted(ELEMENTS + OXIDES, key=len, reverse=True)
_RESERVED_KEYS = {k for syns in SYN.values() for k in syns}
_REST_OK = re.compile(r"^([_\s\-\.\(\[%/]|\d|AS|OX|CN|SOL|RES|ppm|ppb|pct|gpt|PPM|PPB|PCT|GPT)")


def parse_analyte_header(col: str) -> AnalyteColumn | None:
    """Element or oxide column header: 'Au_ppm', 'Cu%', 'Fe2O3_pct', 'CuAS_pct', 'Au_FA_ppb', 'Ag (g/t)'."""
    raw = str(col).strip()
    for name in _ALL_ANALYTES:
        n = len(name)
        head = raw[:n]
        if name in OXIDES:
            ok = head.upper() == name.upper()
        else:
            ok = head == name or (n >= 2 and head == name.upper())
        if not ok:
            continue
        rest = raw[n:]
        if not rest:
            if header_key(raw) in _RESERVED_KEYS and head != name or header_key(raw) in {"y", "cr", "sg", "bd", "rec"}:
                return None
            return AnalyteColumn(raw, name, None, "", False)
        if not _REST_OK.match(rest):
            continue
        partial = bool(re.match(r"^(AS|OX|CN|SOL|RES)", rest))
        tokens = [t for t in re.split(r"[_\s\-\.\(\)\[\]]+", rest) if t]
        unit, quals = None, []
        for t in tokens:
            tl = t.lower().rstrip("%")
            if t.endswith("%") or tl in ("pct", "percent", "per"):
                unit = "%"
                if tl and tl not in ("pct", "percent", "per"):
                    quals.append(tl)
            elif tl in UNITS or tl.replace("/", "") in UNITS:
                unit = UNITS.get(tl, UNITS.get(tl.replace("/", "")))
            elif len(t) <= 8 and re.match(r"^[A-Za-z0-9/]+$", t):
                quals.append(tl)
            else:
                return None
        if rest.lstrip().startswith("%"):
            unit = "%"
        return AnalyteColumn(raw, name, unit, "_".join(quals), partial)
    return None


_SUFFIX_OK = {"", "m", "ft", "deg", "true", "mag", "grid", "utm", "pct", "percent", "gcm3", "tm3", "kgm3", "no", "id",
              "code", "name", "wgs84", "local", "final", "corr", "corrected", "mtr"}
_PREFIX_OK = {"depth", "dh", "hole", "sample", "collar", "survey", "utm", "core", "total", "final", "max", "corrected",
              "true", "grid", "mag", "local", "drill", "bh"}


def _score(key: str, syns: list[str]) -> float:
    if key in syns:
        return 1.0
    for s in syns:
        if len(s) < 2:
            continue
        if key.startswith(s):
            rest = key[len(s):]
            if rest in _SUFFIX_OK or rest.isdigit():
                return 0.85
        if key.endswith(s) and len(s) >= 3:
            pre = key[: -len(s)]
            if pre in _PREFIX_OK:
                return 0.85
    best = max((difflib.SequenceMatcher(None, key, s).ratio() for s in syns if len(s) >= 5), default=0.0)
    return 0.7 if best >= 0.9 else 0.0


@dataclass
class TableMapping:
    kind: str
    fields: dict[str, str | None] = field(default_factory=dict)     # canonical -> source column
    confidence: dict[str, float] = field(default_factory=dict)
    analytes: list[AnalyteColumn] = field(default_factory=list)
    depth_unit: str = "m"


def propose_mapping(df: pd.DataFrame, kind: str) -> TableMapping:
    req, opt = FIELDS[kind]
    keys = {c: header_key(c) for c in df.columns}
    used: set[str] = set()
    tm = TableMapping(kind)
    for f in req + opt:
        if kind == "collar" and f == "eoh_m":
            pass
        best_c, best_s = None, 0.0
        for c, k in keys.items():
            if c in used:
                continue
            s = _score(k, SYN[f])
            if f == "depth_m" and kind == "survey" and s == 0 and k in SYN["eoh_m"]:
                s = 0.6
            if s > best_s:
                best_c, best_s = c, s
        if best_c is not None and best_s > 0:
            tm.fields[f] = best_c
            tm.confidence[f] = best_s
            used.add(best_c)
        else:
            tm.fields[f] = None
    if kind in ("assay", "interval", "density"):
        for c in df.columns:
            if c in used:
                continue
            a = parse_analyte_header(c)
            if a:
                tm.analytes.append(a)
    return tm


def detect_kind(df: pd.DataFrame, name: str = "") -> str:
    """Table type from columns (brief §2.2) with the file/sheet name as a tie-breaker."""
    keys = [header_key(c) for c in df.columns]
    has = lambda f: any(_score(k, SYN[f]) >= 0.8 for k in keys)
    n_analytes = sum(1 for c in df.columns if parse_analyte_header(c))
    nm = header_key(name)
    if has("from_m") and has("to_m"):
        if n_analytes >= 1:
            return "assay"
        for kind, f in (("lithology", "lith_code"), ("geotech", "rqd_pct"), ("geotech", "cr_pct"),
                        ("alteration", "alt_type"), ("weathering", "weathering"), ("density", "density")):
            if has(f):
                return kind
        for kind in ("lithology", "geotech", "alteration", "weathering", "assay"):
            if kind[:4] in nm:
                return kind
        return "interval"
    if has("hole_id") and has("x") and has("y"):
        return "collar"
    if has("hole_id") and has("density"):
        return "density"
    if has("hole_id") and (has("dip") or has("azimuth")):
        return "survey"
    if "collar" in nm or "دهانه" in nm:
        return "collar"
    if "survey" in nm or "انحراف" in nm:
        return "survey"
    return "ignore"
