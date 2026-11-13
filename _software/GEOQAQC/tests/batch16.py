"""A synthetic batch built to the pattern of NLR Batch 16 (spec section 5):
one laboratory job, Cu_PPm (four-acid) and Au_ppb (fire assay), certificate
rows for alternative methods (Au_AR, CuSol) beside the primary ones,
G913-4 with no certified Cu, GBM922-12 Cu with a 2-2s step on results 1-3,
G913-4 Au failing on its last result, two '>5%' Cu values, five #N/A gold
values, seven coarse and three pulp Cu mix-ups, and only eight field pairs.
It stands in for BATH16.csv until the real file is in tests/data."""

import random

ELS = ("Cu_PPm", "Au_ppb")

# 25 certificate rows, as in the project file: primary and alternative methods
CERTS = [
    ("G913-4", "Au", 1.37, 0.04, "ppm"), ("G913-4", "Au_AR", 1.35, 0.08, "ppm"),
    ("G913-4", "Ag", 1.9, 0.2, "ppm"), ("G913-4", "As", 410, 25, "ppm"),
    ("GBM922-12", "Cu", 1.3975, 0.0556, "%"), ("GBM922-12", "CuSol", 1.12, 0.05, "%"),
    ("GBM922-12", "Zn", 0.52, 0.03, "%"), ("GBM922-12", "Mo", 120, 8, "ppm"),
    ("GBM922-12", "Ag", 5.4, 0.4, "ppm"),
    ("OREAS906", "Cu", 0.310, 0.008, "%"), ("OREAS906", "CuSol", 0.259, 0.009, "%"),
    ("OREAS906", "Mo", 4.05, 0.3, "ppm"), ("OREAS906", "Au", 0.012, 0.002, "ppm"),
    ("OREAS906", "Ag", 0.55, 0.05, "ppm"),
    ("G920-5", "Au", 0.52, 0.06, "ppm"), ("G920-5", "Au_AR", 0.49, 0.07, "ppm"),
    ("G920-5", "Cu", 0.084, 0.004, "%"), ("G920-5", "Mo", 18, 2, "ppm"),
    ("OREAS501d", "Cu", 0.271, 0.009, "%"), ("OREAS501d", "Au", 0.234, 0.011, "ppm"),
    ("OREAS501d", "Au_AR", 0.225, 0.012, "ppm"), ("OREAS501d", "Mo", 79, 4, "ppm"),
    ("OREAS501d", "CuSol", 0.041, 0.003, "%"), ("OREAS501d", "Ag", 0.8, 0.1, "ppm"),
    ("OREAS501d", "S", 0.57, 0.03, "%"),
]

GBM_CU = ["12480", "12590", "12450", "13900", "14050"]   # 13975 +/- 556 ppm
G913_AU = ["1290", "1320", "1300", "1330", "1216"]       # 1370 +/- 40 ppb


def rows(seed=16):
    rng = random.Random(seed)
    out = []
    gbm = g913 = 0
    mix_c = mix_p = 0

    def add(**r):
        r.setdefault("BATCH", "B16")
        out.append(r)
    for i in range(200):
        cu = rng.lognormvariate(6.5, 1.0)                 # ~ 660 ppm median
        au = rng.lognormvariate(4.5, 1.1)                 # ~ 90 ppb median
        cu_s = "<1" if i % 37 == 3 else f"{cu:.0f}"
        au_s = "<5" if i % 31 == 4 else f"{au:.0f}"
        if i in (60, 140):
            cu_s = ">5%"
        if i in (11, 52, 97, 133, 171):
            au_s = "#N/A"
        add(SAMPLE_ID=f"NLR-{i:04d}", SAMPLE_TYPE="SAMPLE", Cu_PPm=cu_s, Au_ppb=au_s)
        if i % 40 == 0:                                   # GBM922-12: results 1-5
            add(SAMPLE_ID=f"STD-GBM-{gbm}", SAMPLE_TYPE="CRM", CRM_ID="GBM922-12",
                Cu_PPm=GBM_CU[gbm], Au_ppb=f"{210 * rng.uniform(0.97, 1.03):.0f}")
            gbm += 1
        if i % 40 == 20:                                  # G913-4: results 1-5
            add(SAMPLE_ID=f"STD-G913-{g913}", SAMPLE_TYPE="CRM", CRM_ID="G913-4",
                Cu_PPm=f"{rng.uniform(30, 90):.0f}", Au_ppb=G913_AU[g913])
            g913 += 1
        if i % 25 == 10:
            add(SAMPLE_ID=f"CB-{i}", SAMPLE_TYPE="COARSE BLANK", Cu_PPm="<1", Au_ppb="<5")
        if i % 25 == 15:
            add(SAMPLE_ID=f"PB-{i}", SAMPLE_TYPE="PULP BLANK", Cu_PPm="<1", Au_ppb="<5")
        base_ok = cu_s[0].isdigit() and au_s[0].isdigit()
        if i % 5 == 1 and base_ok:
            f = (5 + 52 * mix_c / 6.0) if mix_c < 7 else rng.uniform(0.92, 1.08)
            mix_c += 1
            add(SAMPLE_ID=f"CD-{i}", SAMPLE_TYPE="COARSE DUP", PARENT_ID=f"NLR-{i:04d}",
                Cu_PPm=f"{cu * f:.0f}", Au_ppb=f"{au * rng.uniform(0.7, 1.3):.0f}")
        if i % 5 == 2 and base_ok:
            # the pulp mix-ups sit at low grade, where they inflate the
            # Thompson-Howarth precision
            mixed = mix_p < 3 and cu < 400
            f = (8.0 + 6 * mix_p) if mixed else rng.uniform(0.97, 1.03)
            mix_p += mixed
            add(SAMPLE_ID=f"PD-{i}", SAMPLE_TYPE="PULP DUP", PARENT_ID=f"NLR-{i:04d}",
                Cu_PPm=f"{cu * f:.0f}", Au_ppb=f"{au * rng.uniform(0.9, 1.1):.0f}")
        if i % 25 == 7 and base_ok:
            add(SAMPLE_ID=f"FD-{i}", SAMPLE_TYPE="FIELD DUP", PARENT_ID=f"NLR-{i:04d}",
                Cu_PPm=f"{cu * rng.uniform(0.85, 1.15):.0f}",
                Au_ppb=f"{au * rng.uniform(0.6, 1.4):.0f}")
    return out


def oreas906_rows():
    """A small fixture with OREAS906 (not in Batch 16)."""
    out = [{"SAMPLE_ID": "LOW", "Cu_PPm": "<1", "Au_ppb": "<5", "Mo_ppm": "<1"}]
    for i in range(12):
        out.append({"SAMPLE_ID": f"S{i}", "Cu_PPm": f"{500 + 40 * i}", "Au_ppb": "50",
                    "Mo_ppm": f"{5 + i}"})
        out.append({"SAMPLE_ID": f"O906-{i}", "SAMPLE_TYPE": "CRM", "CRM_ID": "OREAS906",
                    "Cu_PPm": f"{3100 * (1 + (i % 3 - 1) * 0.01):.0f}", "Au_ppb": "12",
                    "Mo_ppm": f"{4.05 * (1 + (i % 3 - 1) * 0.05):.2f}"})
    return out
