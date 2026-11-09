# GEOVALID PRO 0.3.0 — rule catalogue (generated)

Generated from the rule registry by `tools/gen_rule_catalogue.py`; do not edit by hand. The design specification of every
rule, including those not yet implemented, is `03_rule_catalogue.md`.

90 rules run in this version. Severities: Critical = CRITICAL, Major = ERROR, Minor = WARNING, Info = INFO.

## Categories

| Cat. | Name | فارسی |
|---|---|---|
| A | Schema and identifiers | ساختار و شناسه‌ها |
| B | Collars | دهانهٔ گمانه‌ها |
| C | Downhole survey | انحراف‌سنجی درون‌چاهی |
| D | Intervals and samples | بازه‌ها و نمونه‌ها |
| E | Values | مقادیر |
| F | Cross-table consistency | سازگاری میان جداول |
| G | Laboratory and QA/QC reconciliation | تطبیق آزمایشگاه و کنترل کیفیت |
| H | Spatial, topography and boundary | مکانی، توپوگرافی و محدوده |
| I | Versions | نسخه‌ها |
| J | Profiles and process | پروفایل و فرایند |

## Standards tags

| Tag | Clause |
|---|---|
| `JORC-T1-S1-Verification` | JORC Table 1 §1 Verification of sampling and assaying |
| `JORC-T1-S1-Location` | JORC Table 1 §1 Location of data points |
| `JORC-T1-S3-DBIntegrity` | JORC Table 1 §3 Database integrity |
| `NI43101-F1-Item12` | NI 43-101 Form 43-101F1 Item 12 Data verification |
| `SK1300-601b96-iii-B-9` | S-K 1300 Item 601(b)(96)(iii)(B)(9) Data verification |
| `CIM2019-4.2` | CIM MRMR Best Practice 2019 §4.2 Database: unintended changes, edits, archiving, units as received |
| `CIM2019-4.5` | CIM MRMR Best Practice 2019 §4.5 Data verification: collars, deviation, log consistency, certificates |
| `CIM2019-6.2` | CIM MRMR Best Practice 2019 §6.2 Unsampled intervals, below-detection and over-limit values, mixed methods |

## Rules

| ID | v2 ID | Cat. | Name | Default severity (catalogue) | Profile override | Thresholds | Standards |
|---|---|---|---|---|---|---|---|
| COL-003 | SCH-05 | A | HoleID format inconsistent or near-duplicate IDs / ناهمگونی قالب شمارهٔ گمانه یا شناسه‌های تقریباً تکراری | ERROR (v2 SCH-05: one issue per normalised-key group across all tables) |  | `strip_leading_zeros` True | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-003 |  | A | Character normalisation applied (digits, letters, invisible characters, whitespace) / اعمال یکسان‌سازی نویسه‌ها (ارقام، حروف، نویسه‌های نامرئی، فاصله‌ها) | INFO; ↑WARNING when the step made two distinct raw IDs (`hole_id`, `sample_id`) coincide |  |  | JORC-T1-S3-DBIntegrity, CIM2019-6.2, CIM2019-4.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-004 |  | A | Decimal or thousands separator ambiguous in a numeric column / ابهام جداکنندهٔ اعشار یا هزارگان در ستون عددی | WARNING |  |  | JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-005 | SCH-02 | A | Value not parseable for its type, or unknown enum value / مقدار غیرقابل تبدیل به نوع استاندارد یا مقدار شمارشی ناشناخته | WARNING; ↑ERROR for `x, y, z, eoh_m, depth_m, from_m, to_m, dip, azimuth` |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-006 | SCH-06 | A | Placeholder or sentinel set to NULL in a non-assay field / جایگزینی مقدار جانشین یا نگهبان با تهی در فیلد غیرعیاری | WARNING (two or more missing-value forms, v2 SCH-06); INFO otherwise, ↑WARNING in coordinate, depth or angle fields |  | `sentinels` [-99, -999, -9999, 9999] | JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-010 | SCH-01 | A | Required canonical field unmapped or absent for the table type / عدم نگاشت یا نبود فیلد الزامی استاندارد برای نوع جدول | CRITICAL (required); WARNING (recommended) |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-011 |  | A | Depth unit inferred, unconfirmed or mixed within a table / واحد عمق استنتاجی، تأییدنشده یا مختلط در یک جدول | WARNING (a); ERROR (b, never bulk-converted) |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-6.2, CIM2019-4.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-012 | COL-04 | A | Coordinate format or CRS undeclared, inferred or implausible / قالب یا سیستم مختصات اعلام‌نشده، استنتاجی یا غیرمحتمل | ERROR (outside the declared zone; separate offset cluster); INFO (CRS undeclared) |  | `cluster_sep_km` 20 | JORC-T1-S1-Location, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| IMP-014 |  | A | Date calendar or format ambiguous, Jalali detected, or calendars mixed / ابهام قالب تاریخ، تشخیص تقویم جلالی یا تقویم‌های مختلط | (a) INFO, ↑WARNING until the CALENDAR inference is confirmed; (b) ERROR; (c) WARNING |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, JORC-T1-S1-Location, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SMP-001 | INT-07 | A | Sample ID not unique project-wide / شناسهٔ نمونه در کل پروژه یکتا نیست | CRITICAL (v2 INT-07) |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-001 | SCH-03 | B | Duplicate HoleID / شمارهٔ گمانهٔ تکراری | CRITICAL |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-002 | COL-01 | B | Missing, zero or non-numeric X, Y, Z or EOH / مختصات X، Y، Z یا عمق نهایی گمشده، صفر یا غیرعددی | ERROR | ERROR→CRITICAL | `z_zero_tol_m` 20, `dummy_values` [-99, -999, -9999, 9999, 99999] | JORC-T1-S1-Location, JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-004 | COL-02, SPA-03 | B | Duplicate or near-duplicate collar coordinates (twins, wedges, re-drills, true duplicates) / مختصات تکراری یا بسیار نزدیک دهانه (دوقلو، گُوِه، بازحفاری، تکرار واقعی) | WARNING; ↑ERROR for TRUE_DUPLICATE under different hole IDs (double counting) | WARNING→ERROR | `near_dup_distance_m` 1.0, `near_dup_dz_m` 2.0 | JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-006 | COL-03 | B | Swapped X/Y, wrong UTM zone, lat/long in UTM fields, wrong horizontal datum / جابجایی X و Y، زون UTM اشتباه، طول/عرض جغرافیایی در فیلد UTM، دیتوم افقی اشتباه | CRITICAL |  |  | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-007 | COL-07 | B | EOH shallower than the maximum depth in survey or interval tables / عمق نهایی کمتر از بیشینهٔ عمق جداول انحراف‌سنجی یا بازه‌ای | ERROR | ERROR→CRITICAL | `eoh_tol_m` 0.05 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-008 | SCH-04 | B | Collar without survey / دهانهٔ فاقد انحراف‌سنجی | WARNING |  |  | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-009 | SCH-04 | B | Collar without any interval data / دهانهٔ فاقد هرگونه دادهٔ بازه‌ای | INFO | INFO→WARNING |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-010 |  | B | Inferred collar survey method is handheld GPS, planned or digitised / روش برداشت استنتاجی دهانه: جی‌پی‌اس دستی، طراحی‌شده یا رقومی‌شده از نقشه | WARNING; campaign ↑ERROR (§1.4 E2) |  | `grid_steps_m` [100, 50, 25], `round_decimals_max` 0 | JORC-T1-S1-Location, NI43101-F1-Item12, CIM2019-4.5, SK1300-601b96-iii-B-9 |
| COL-013 |  | B | Repeated identical Z values / تکرار مقادیر یکسان ارتفاع دهانه | WARNING |  | `min_group_n` 3 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-014 | COL-08 | B | Date inconsistencies or drilling-rate outliers / ناسازگاری تاریخ‌ها یا نرخ حفاری غیرعادی | WARNING |  | `min_year` 1950, `max_rate_m_day` 300, `drill_types` ['DD', 'DDH', 'DIA', 'DIAMOND', 'CORE', 'NQ', 'HQ', 'PQ', 'BQ', 'NQ2', 'HQ3', 'RC', 'RCD', 'RC_DD', 'RCDD', 'RC/DD', 'PRE-COLLAR', 'PC', 'RAB', 'AC', 'AIR', 'AIRCORE', 'PERC', 'PERCUSSION', 'AUGER', 'SONIC', 'ROTARY', 'TRENCH', 'TR', 'CH', 'CHANNEL', 'PIT', 'WEDGE', 'UG'] | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-015 |  | B | Spacing outlier or clustered drilling (declustering needed) / فاصله‌داری غیرعادی یا حفاری خوشه‌ای (نیاز به واخوشه‌بندی) | INFO |  | `isolation_x_median` 3.0, `ce_clustered` 0.8 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-016 |  | B | Coordinate outlier in X, Y or Z / مختصات پرت X، Y یا Z | WARNING |  | `z_range_m` [-50, 5700], `robust_z` 5.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-019 |  | B | No survey and no collar orientation: trace silently assumed vertical / بدون انحراف‌سنجی و بدون جهت دهانه: مسیر گمانه به‌طور ضمنی قائم فرض می‌شود | ERROR |  | `vertical_tol_deg` 0.5 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-001 | SCH-04, SCH-04b | C | Survey HoleID not in collar / شمارهٔ گمانهٔ انحراف‌سنجی در جدول دهانه وجود ندارد | ERROR | ERROR→CRITICAL |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-002 | SRV-04, SCH-03 | C | Duplicate survey depth / عمق تکراری ایستگاه انحراف‌سنجی | ERROR; ↓INFO if identical | INFO→WARNING | `dup_angle_tol_deg` 0.1 | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-003 | SRV-02 | C | Dip out of range / شیب خارج از محدودهٔ مجاز | ERROR | ERROR→CRITICAL |  | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-004 | SRV-02 | C | Azimuth out of range / آزیموت خارج از محدودهٔ مجاز | ERROR; ↓INFO for 360 | ERROR→CRITICAL |  | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-005 | SRV-03 | C | Mixed dip sign convention / ناسازگاری قرارداد علامت شیب | ERROR |  | `near_horizontal_deg` 5 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-006 | SRV-06 | C | Survey depth beyond EOH / عمق ایستگاه انحراف‌سنجی بیشتر از عمق نهایی | ERROR; ↓INFO below tolerance |  | `survey_overrun_tol_m` 0.5 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-007 | SRV-01 | C | First station too deep, or no collar orientation / نخستین ایستگاه بسیار عمیق یا نبود جهت دهانه | WARNING (v2 SRV-01: any missing 0 m station) |  | `first_station_max_m` 30 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-008 | SRV-10 | C | Station spacing too large or irregular; trace extrapolated / فاصلهٔ ایستگاه‌ها بسیار زیاد یا نامنظم؛ برون‌یابی مسیر | WARNING; ↓INFO for (c) |  | `max_spacing_m` 50, `extrap_max_m` 50, `extrap_max_frac` 0.2 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-009 | SRV-15 | C | Design-only or constant survey (unsurveyed hole) / برداشت طراحی‌شده یا ثابت (گمانهٔ برداشت‌نشده) | WARNING |  | `min_length_m` 50, `const_tol_deg` 0.01, `straight_min_m` 100 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-010 | SRV-08 | C | Dogleg severity above threshold / شدت خمیدگی (داگ‌لگ) بیش از حد آستانه | WARNING/ERROR (banded) |  | `warn_deg_30m` 3.0, `error_deg_30m` 6.0, `min_dmd_m` 3 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-011 |  | C | Large dip change between stations / تغییر زیاد شیب بین ایستگاه‌ها | WARNING |  | `max_dip_change_deg` 5, `max_dip_change_deg_30m` 10 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-012 | SRV-11 | C | Large azimuth change (dip shallower than −85° only) / تغییر زیاد آزیموت (فقط برای شیب کم‌تر از ۸۵− درجه) | WARNING |  | `max_az_change_deg` 10, `max_az_change_deg_30m` 20, `near_vertical_incl_deg` 3 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-013 | SRV-09 | C | Azimuth spike: probable magnetic interference / جهش آزیموت: احتمال تداخل مغناطیسی | ERROR (v2 SRV-09) |  | `dev_deg` 2.0, `agree_dls_30m` 1.0, `unreliable_n` 3 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-014 | SRV-12 | C | Azimuth reference (magnetic / true / grid) inconsistency / ناسازگاری مرجع آزیموت (مغناطیسی، جغرافیایی، شبکه) | WARNING |  | `declination_deg` None, `grid_convergence_deg` 0.0, `tol_deg` 1.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-015 | SRV-14 | C | Desurvey-method EOH difference above threshold / اختلاف موقعیت انتهای گمانه بین روش‌های محاسبهٔ مسیر بیش از حد آستانه | INFO (project summary); WARNING per hole above `eoh_diff_m` (v2 SRV-14) |  | `eoh_diff_m` 2.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-017 | SRV-05 | C | Negative station depth, or stations out of source order / عمق منفی ایستگاه یا ترتیب نادرست ایستگاه‌ها در منبع | ERROR (a); WARNING (b) |  |  | JORC-T1-S1-Location, JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-020 |  | C | Survey station with null or dummy dip or azimuth (partial station) / ایستگاه برداشت با شیب یا آزیموت تهی یا ساختگی (ایستگاه ناقص) | ERROR; WARNING/INFO as stated |  | `sentinels` [-99, -999, -9999, 999, 9999], `steep_dip_cutoff_deg` -85 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-023 | SRV-07 | C | Collar orientation conflicts with the near-collar station; synthetic stations tagged / تعارض جهت دهانه با ایستگاه نزدیک دهانه؛ شناسایی ایستگاه‌های ساختگی | ERROR (v2 SRV-07) |  | `max_first_depth_m` 50, `dip_tol_deg` 5, `az_tol_deg` 10 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-027 | SRV-13 | C | Magnetic azimuth unreliable: station QC failure or magnetic environment / آزیموت مغناطیسی نامعتبر: شکست کنترل کیفی ایستگاه یا محیط مغناطیسی | WARNING; ERROR for casing or rods |  | `expected_field_nt` None, `field_tol_nt` 300, `dip_stable_deg` 0.5, `az_swing_deg` 5.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-001 | INT-01, INT-02 | D | From ≥ To, zero-length or negative depth / عمق «از» بزرگ‌تر یا مساوی «تا»، بازهٔ با طول صفر یا عمق منفی | CRITICAL (From > To, negative depth); ERROR (zero length) — v2 INT-01/INT-02 |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-002 | INT-03 | D | Overlapping intervals / همپوشانی بازه‌ها | CRITICAL (v2 INT-03); overlaps ≤ the depth tolerance are INT-012 |  |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-003 | SCH-03 | D | Duplicate or conflicting intervals (and point records) / بازه‌ها یا رکوردهای نقطه‌ای تکراری یا متناقض | ERROR | ERROR→CRITICAL |  | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-004 | INT-04 | D | Top, internal or bottom gaps / فاصلهٔ خالی در ابتدا، میانه یا انتهای گمانه | WARNING; ↓INFO as stated |  | `top_gap_tol_m` 0.5, `bottom_gap_tol_m` 0.5, `micro_gap_m` 0.01 | JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-005 | INT-05 | D | Interval or point beyond EOH / بازه یا نقطهٔ فراتر از عمق نهایی | ERROR | ERROR→CRITICAL |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-006 | SCH-04, SCH-04b | D | HoleID not in collar / شمارهٔ گمانه در جدول دهانه وجود ندارد | ERROR | ERROR→CRITICAL |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-007 | INT-06 | D | Non-standard or extreme sample length / طول نمونهٔ غیراستاندارد یا بسیار کوتاه/بلند | WARNING (v2 INT-06); INFO for the length–grade correlation |  | `by_drill_type` {'default': [0.1, 6.0], 'RC': [0.5, 6.0], 'DD': [0.1, 6.0], 'RAB': [0.5, 6.0], 'AC': [0.5, 6.0]}, `long_logging_m` 50 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-008 |  | D | Sample crosses a geological contact / عبور نمونه از مرز زمین‌شناسی | INFO |  | `contact_tol_m` 0.05 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-009 |  | D | Copy-paste repetition pattern / الگوی تکرار ناشی از کپی‌برداری | WARNING |  | `min_window_n` 5 | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-010 |  | D | Missing or non-numeric HoleID, From or To / شمارهٔ گمانه، «از» یا «تا» گمشده یا غیرعددی | ERROR |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-012 | INT-03, INT-04 | D | Depth precision or rounding artefacts / دقت عمق ناسازگار یا اثر گردکردن | WARNING (v2 §5.4 precision artefacts ≤ `depth_eps_m`) |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-013 |  | D | Unmerged consecutive identical records / رکوردهای پیاپی یکسان ادغام‌نشده | INFO |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SMP-002 | INT-07 | D | Sample-number sequence gaps or unused tickets / شکاف در توالی شمارهٔ نمونه یا بلیت‌های استفاده‌نشده | WARNING (missing numbers, out-of-order downhole); INFO (number blocks) |  | `max_gap_n` 100 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-001 | VAL-03 | E | Assay unit unknown or inferred / واحد عیار نامعلوم یا استنتاجی | WARNING |  |  | JORC-T1-S1-Verification, CIM2019-6.2, CIM2019-4.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-002 | VAL-01 | E | Text codes, placeholders and negative detection-limit codes / کدهای متنی، مقادیر جانشین و کدهای منفی حد تشخیص | INFO; ↑WARNING when TXT > 1 % of an analyte's determinations |  |  | JORC-T1-S1-Verification, JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-003 | VAL-05 | E | Impossible value (> 100 %, negative real grade, oxide sum) / مقدار ناممکن (بیش از ۱۰۰ درصد، عیار منفی واقعی، مجموع اکسیدها) | ERROR | ERROR→CRITICAL | `total_max_pct` 105, `au_max_ppm` 10000, `element_sum_max_pct` 100 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-004 | VAL-03 | E | Mixed units within a column / واحدهای مختلط در یک ستون | ERROR |  | `min_minority_frac` 0.05, `min_n` 200, `min_separation_decades` 2.5, `group_gap_decades` 1.0, `group_separation_decades` 2.0, `min_group_n` 10 | JORC-T1-S1-Verification, CIM2019-6.2, CIM2019-4.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-005 | VAL-02 | E | Over-range value not re-assayed / مقدار فراتر از حد بالای روش بدون آنالیز مجدد | WARNING | WARNING→ERROR |  | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-006 |  | E | Stoichiometric or ratio inconsistency (Cu–S, Fe–Fe2O3/FeO, CuAS > Cu) / ناسازگاری استوکیومتری یا نسبت عناصر (مس–گوگرد، آهن–اکسیدهای آهن، مس محلول بیش از مس کل) | WARNING |  | `fe_rel_tol_frac` 0.05, `partial_tol_frac` 0.05, `cu_s_max_ratio` 4.0, `cu_min_pct` 0.5 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-007 |  | E | Statistical outlier (and top-cut candidate) / مقدار پرت آماری (و نامزد سقف‌گذاری عیار) | INFO |  | `tukey_k` 3, `cv_topcut` 2.0 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-010 | VAL-04 | E | Detection limit changes between labs, batches or periods / تغییر حد تشخیص بین آزمایشگاه‌ها، بچ‌ها یا دوره‌ها | WARNING (v2 VAL-04) |  |  | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-011 |  | E | High proportion below detection for a key analyte / سهم بالای مقادیر کمتر از حد تشخیص برای عنصر کلیدی | WARNING / INFO |  | `bdl_share_warn_frac` 0.3, `bdl_share_info_frac` 0.8 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-012 |  | E | Value inconsistent with the detection limit (below DL, at DL, `<x` ≠ DL) / ناسازگاری مقدار با حد تشخیص (کمتر از حد، برابر حد، اختلاف حد اعلام‌شده) | WARNING; INFO for (c) |  |  | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-014 |  | E | Zero versus null confusion / ابهام بین مقدار صفر و مقدار تهی | WARNING |  |  | JORC-T1-S1-Verification, JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-015 | VAL-07 | E | Major-oxide total outside 98–101 % / مجموع اکسیدهای اصلی خارج از بازهٔ ۹۸ تا ۱۰۱ درصد | WARNING | WARNING→ERROR | `total_min_pct` 97, `total_max_pct` 102 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-019 | VAL-04 | E | Mixed analytical method or digestion within one element field / آمیختگی روش آنالیز یا نوع هضم در یک فیلد عنصر | WARNING (v2 VAL-04) |  |  | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-028 | VAL-06 | E | Value above the mineral-stoichiometric cap / مقدار بیش از سقف استوکیومتری کانی | ERROR |  | `caps_pct` {'Cu': 79.9, 'Pb': 86.6, 'Zn': 67.1, 'Fe': 72.4, 'S': 53.4, 'Mo': 59.9, 'Ba': 58.8} | JORC-T1-S1-Verification, JORC-T1-S3-DBIntegrity, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-029 | VAL-09 | E | Downhole spike / جهش درون‌چاهی عیار | INFO |  | `factor` 10, `quantile` 0.95 | JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| ASY-030 | VAL-10 | E | Repeated identical values downhole (copy-paste or fill-down) / تکرار مقادیر یکسان پشت سر هم (کپی یا پرکردن خودکار) | WARNING |  | `min_run` 5 | JORC-T1-S3-DBIntegrity, JORC-T1-S1-Verification, CIM2019-6.2, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| INT-015 | VAL-08 | E | Value outside controlled vocabulary / مقدار خارج از واژه‌نامهٔ کنترل‌شده | ERROR (v2 VAL-08) |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| LIT-001 |  | E | Lithology code not in the dictionary, or synonym variants / کد سنگ‌شناسی خارج از فرهنگ کدها یا گونه‌های هم‌معنا | WARNING; INFO (inventory) |  |  | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| LIT-002 |  | E | Thin interval or unmerged consecutive identical units / بازهٔ بسیار نازک یا واحدهای یکسان پیاپی ادغام‌نشده | INFO; ↑WARNING (over-splitting) |  | `thin_m` 0.5, `thin_share_frac` 0.2 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| LIT-003 |  | E | Illogical downhole sequence / توالی غیرمنطقی در طول گمانه | WARNING (a, b); INFO (c) |  | `cover_codes` ['OB', 'OVB', 'OVBD', 'ALL', 'ALLUV', 'ALV', 'SOIL', 'SOL', 'COLL', 'QAL', 'QT', 'CV', 'COVER', 'TILL', 'SCREE', 'FILL'] | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| CRS-004 |  | F | Candidate estimation domains not statistically separated / عدم تفکیک آماری دامنه‌های پیشنهادی تخمین | INFO |  | `alpha` 0.01, `effect_min` 0.2, `min_n` 30, `cv_mixed` 2.0, `eta2_weak` 0.02 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| CRS-005 |  | F | Contact behaviour (hard vs soft boundary) / رفتار همبری (مرز سخت یا نرم) | INFO |  | `max_dist_m` 20 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| DEN-001 | XTB-04 | F | Implausible density for the lithology / چگالی غیرمحتمل برای سنگ‌شناسی | WARNING; ↑ERROR outside the absolute bounds (physically implausible) |  | `abs_bounds_gcm3` [1.0, 6.5], `k_mad` 4 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| GEO-001 | XTB-02 | F | Core recovery above 100 % or below 0 / بازیافت مغزه بیش از ۱۰۰ درصد یا منفی | ERROR; INFO within tolerance |  | `cr_tol_pct` 5 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| GEO-002 | XTB-03 | F | RQD greater than core recovery, or above 100 % / RQD بزرگ‌تر از بازیافت مغزه یا بیش از ۱۰۰ درصد | ERROR |  | `tol_pct` 1 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| GEO-003 |  | F | Recorded and recomputed CR or RQD disagree / مغایرت CR یا RQD ثبت‌شده با مقدار بازمحاسبه‌شده | WARNING |  | `diff_tol_pct` 2, `len_tol_m` 0.02 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| GEO-004 |  | F | Recovery–grade bias / اریبی بین بازیافت و عیار | WARNING |  | `low_pct` 85, `high_pct` 95, `alpha` 0.01, `min_n_per_class` 30 | JORC-T1-S3-DBIntegrity, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| QAQ-001 |  | G | Insufficient insertion rate or no QA/QC / نرخ درج ناکافی یا نبود کنترل کیفیت | CRITICAL (a); ERROR / WARNING (b, banded); WARNING (c) |  | `target_crm_pct` 5, `target_blank_pct` 3, `target_field_dup_pct` 2, `target_coarse_dup_pct` 2, `target_pulp_dup_pct` 2, `min_originals_n` 100 | JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| QAQ-002 |  | G | CRM failure (±3 SD), Westgard violation or bias / شکست ماده مرجع (±۳ انحراف معیار)، نقض قواعد وستگارد یا اریبی | ERROR / WARNING as stated |  | `sd_warn` 2, `sd_fail` 3, `bias_warn_pct` 3, `bias_err_pct` 5, `min_n_bias` 10 | JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| QAQ-003 |  | G | Blank contamination or carry-over / آلودگی بلانک یا انتقال آلودگی | ERROR / WARNING |  | `blank_warn_x_dl` 5, `blank_fail_x_dl` 10 | JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| QAQ-004 |  | G | Duplicate precision failure (HARD) / شکست دقت نمونه‌های تکراری (HARD) | WARNING; ↑ERROR (pulp, > 2× allowed) |  | `hard_limit_pct` {'FIELD_DUP': 30, 'COARSE_DUP': 20, 'PULP_DUP': 10}, `max_fail_frac` 0.1, `min_mean_x_dl` 10 | JORC-T1-S1-Verification, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-005 | COL-05 | H | Collar outside licence boundary or project extent / دهانه خارج از محدودهٔ پروانه یا گسترهٔ پروژه | ERROR (INFO near boundary) |  | `edge_buffer_m` 25 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-011 | COL-06 | H | Collar–topography \|ΔZ\| above threshold / اختلاف ارتفاع دهانه و توپوگرافی بیش از حد آستانه | WARNING/ERROR (banded) |  | `warn_m` 2.0, `error_m` 5.0, `handheld_warn_m` 10.0, `handheld_error_m` 20.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| COL-012 | COL-06b | H | Systematic ΔZ offset (datum suspicion) / جابجایی سیستماتیک ΔZ (احتمال اختلاف دیتوم) | WARNING |  | `min_n` 20, `offset_min_m` 1.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |
| SUR-016 | SPA-01, SPA-02 | H | Trace crosses another trace, or exits above topography / تقاطع مسیر با گمانهٔ دیگر یا خروج مسیر از سطح زمین | ERROR |  | `cross_dist_m` 1.0, `collar_zone_m` 5, `exit_tol_m` 2.0, `step_m` 1.0 | JORC-T1-S1-Location, CIM2019-4.5, NI43101-F1-Item12, SK1300-601b96-iii-B-9 |

## Logic

### ASY-001 — Assay unit unknown or inferred

*واحد عیار نامعلوم یا استنتاجی* · category E (Values) · v2 VAL-03

Catalogue logic: Per (source column or analyte × method × source): `unit_source` is CERT (certificate header rows: method/analyte/units/LOR), METHOD (method dictionary) or INFERRED (magnitude, legacy only). The rule fires for **INFERRED** units and for **conflicts between sources**. Evidence: magnitude priors; paired-column ratio (median ≈ 10 000 → % vs ppm); DL signature; method catalogue; Cu–S plausibility.

### ASY-002 — Text codes, placeholders and negative detection-limit codes

*کدهای متنی، مقادیر جانشین و کدهای منفی حد تشخیص* · category E (Values) · v2 VAL-01

Catalogue logic: Classifies every `value_raw` into `value_flag` (02 §4.9.1) and reports counts per analyte × class × source column **before conversion**. Negatives (02 §4.9.2): −x equal to a known DL (1e-9 relative) → BDL; a column whose negatives take ≤ 3 distinct magnitudes → DL-code signature; −99/−999/−9999 → SNT; any other negative stays VAL and goes to ASY-003. **A blank in a long source means "not analysed" and is never set to ½DL.** The report lists how many values each `bdl_policy` choice changed per element.

### ASY-003 — Impossible value (> 100 %, negative real grade, oxide sum)

*مقدار ناممکن (بیش از ۱۰۰ درصد، عیار منفی واقعی، مجموع اکسیدها)* · category E (Values) · v2 VAL-05

Catalogue logic: Flags: `value_num` < 0 after §4.9.2 (a negative real grade); `value_num` > `analyte.max_physical`; Σ major oxides + LOI > `total_max_pct`, counting Fe once (either Fe2O3T, or FeO + Fe2O3); Au > `au_max_ppm` (Au reported in % or a decimal shift) unless visible gold is logged; Σ of all reported analytes (ppm converted) > 100 %.

### ASY-004 — Mixed units within a column

*واحدهای مختلط در یک ستون* · category E (Values) · v2 VAL-03

Catalogue logic: A Gaussian mixture on log₁₀ values per source column and analyte (k ≤ 4, BIC) finds populations separated by a unit factor: ≈ 1.5 decades (oz/t vs g/t), 3 (ppb vs ppm) or 4 (% vs ppm, % vs g/t). The finding is strengthened when population membership aligns with `batch_id`, lab or campaign (Cramér's V ≥ 0.5). **Group test** (v0.2): when grades are naturally spread over several decades the column-level mixture can miss a mix-up, so the medians of log values per batch (then per hole) are also sorted and split at the widest gap; an ERROR is raised when that gap ≥ `group_gap_decades` (no group in between) and the cluster medians are ≥ `group_separation_decades` apart, naming the minority batches or holes.

### ASY-005 — Over-range value not re-assayed

*مقدار فراتر از حد بالای روش بدون آنالیز مجدد* · category E (Values) · v2 VAL-02

Catalogue logic: The preferred determination is `ODL`, or `value_num ≥ ul_value`, and no `OVERLIMIT` determination exists. The UL comes from `method_limit` or the certificate, never from a global number. Also flagged: a VAL exactly equal to the UL (a `>UL` value substituted by the UL, which truncates the high-grade tail). A `>` code that already has an over-limit result is not an issue, because ASY-009 selects the over-limit value.

### ASY-006 — Stoichiometric or ratio inconsistency (Cu–S, Fe–Fe2O3/FeO, CuAS > Cu)

*ناسازگاری استوکیومتری یا نسبت عناصر (مس–گوگرد، آهن–اکسیدهای آهن، مس محلول بیش از مس کل)* · category E (Values)

Catalogue logic: ⟦`drv_assay_wide`⟧ (a) **Sulphide S budget**, in `PRIMARY` material (WTH) or where CuAS/Cu < 0.1: S_min = 0.2523·Cu + 0.4904·Zn + 0.1547·Pb + 0.6683·Mo (wt %; Cu as chalcocite, the minimum-S Cu sulphide). Flag S < S_min·(1 − `rel_tol_frac`). (b) **Iron**: Fe_total = 0.6994·Fe2O3 + 0.7773·FeO (or 0.6994·Fe2O3T); |Fe − Fe_total| / Fe > `rel_tol_frac`. (c) **Partial ≤ total**: CuAS ≤ Cu; CuAS + CuCN ≤ Cu (sequential leach); AvAl2O3 ≤ Al2O3; RxSiO2 ≤ SiO2; Fe_mag ≤ Fe_total; each × (1 + `rel_tol_frac`). (d) **Element vs oxide duplicates**: e.g. Cr vs 0.6842·Cr2O3, via `analyte.to_element_factor`.

### ASY-007 — Statistical outlier (and top-cut candidate)

*مقدار پرت آماری (و نامزد سقف‌گذاری عیار)* · category E (Values)

Catalogue logic: Per analyte and domain, on log values: Tukey far-out fence Q3 + `tukey_k`·IQR; robust z ≥ `z_robust`; top GMM population holding < 1 % of samples. Spatial outliers are SPA-001. Top-cut analysis is **suggestion only**: CV > `cv_topcut`, Parrish deciles (top decile > 40 % of metal or top percentile > 10 %), metal at risk, cumulative metal curve.

### ASY-010 — Detection limit changes between labs, batches or periods

*تغییر حد تشخیص بین آزمایشگاه‌ها، بچ‌ها یا دوره‌ها* · category E (Values) · v2 VAL-04

VAL-04 (detection limits): more than one detection limit within one analyte column, with counts and the batches
using each. WARNING (Minor): ½DL substitution then steps at the DL change and the low-grade tail mixes populations.

Catalogue logic: Per (analyte, method class): `dl_value` by batch and by period. Change point: a DL ratio ≥ `dl_change_ratio` between adjacent periods, each with ≥ 20 BDL results. The issue states the consequence: ½DL substitution creates an artificial step in the low-grade tail that shows up at low cut-offs. Fitness of the DL for the cut-off is ASY-023.

### ASY-011 — High proportion below detection for a key analyte

*سهم بالای مقادیر کمتر از حد تشخیص برای عنصر کلیدی* · category E (Values)

Catalogue logic: BDL share per analyte × domain or campaign. A key analyte in a mineralised domain with BDL share > `bdl_share_warn_frac` → WARNING (method insensitive for the grade range). Pathfinders or barren domains with BDL share > 0.8 → INFO.

### ASY-012 — Value inconsistent with the detection limit (below DL, at DL, `<x` ≠ DL)

*ناسازگاری مقدار با حد تشخیص (کمتر از حد، برابر حد، اختلاف حد اعلام‌شده)* · category E (Values)

Catalogue logic: The DL is resolved per (lab, method, analyte, batch) as certificate LOR > batch DL > method dictionary. (a) VAL with 0 < v < DL·(1 − 1e-6): it should have been `<DL`, so either the DL metadata or the value (typed or converted) is wrong. (b) **Values exactly at DL** (1e-6 relative) making up ≥ `at_dl_share_frac` of a batch: censored values were substituted by DL upstream and can no longer be told apart from measurements. (c) `<x` with x ≠ the resolved DL. (d) Dictionary DL ≠ certificate LOR. Negative −DL codes stay with ASY-002.

### ASY-014 — Zero versus null confusion

*ابهام بین مقدار صفر و مقدار تهی* · category E (Values)

Catalogue logic: (a) `value_num = 0` exactly for an analyte whose method DL > 0: zero is not a measurement, and the issue asks whether it was BDL, NS or a blank. (b) A source column holding both blanks and zeros, with the zeros aligned to whole unsampled holes or intervals (neighbours NS, no batch link). Counts are given per batch.

### ASY-015 — Major-oxide total outside 98–101 %

*مجموع اکسیدهای اصلی خارج از بازهٔ ۹۸ تا ۱۰۱ درصد* · category E (Values) · v2 VAL-07

Catalogue logic: For whole-rock packages (`method_class = TOTAL`, fusion XRF): total = Σ(SiO2, TiO2, Al2O3, Fe2O3T *or* FeO + Fe2O3, MnO, MgO, CaO, Na2O, K2O, P2O5, and Cr2O3, BaO, SrO, SO3, V2O5 when reported) + LOI. Total < `total_min_pct` → WARNING: a missing component or LOI, or an incomplete package. ↓INFO when S > 2 % or sulphides are logged, because sulphide oxidation during ignition offsets LOI. Totals > 101 % are ASY-003.

### ASY-019 — Mixed analytical method or digestion within one element field

*آمیختگی روش آنالیز یا نوع هضم در یک فیلد عنصر* · category E (Values) · v2 VAL-04

VAL-04 (laboratories and methods): an assay table whose rows come from more than one laboratory or analytical
method (mapped `lab` / `method` columns). WARNING (Minor): mixed methods in one field must be shown to be comparable.

Catalogue logic: ⟦`drv_assay_wide`⟧ The preferred values of one analyte come from ≥ 2 `method_class`/digestion groups. **Partial vs total** mixed for refractory or partially digested elements (Cr, Ti, Zr, Al, Ba, W, Sn, REE, K) → ERROR. Other mixtures (e.g. aqua regia vs four-acid Cu) → WARNING, with the systematic difference tested on spatially paired samples within the domain. Au charge (25/30/50 g), finish (AAS/gravimetric), PhotonAssay, screen fire or cyanide leach (LeachWELL/BLEG, partial) mixed → WARNING. Proposal: method-specific fields with the §6.1 preference.

### ASY-028 — Value above the mineral-stoichiometric cap

*مقدار بیش از سقف استوکیومتری کانی* · category E (Values) · v2 VAL-06

VAL-06: mineral-stoichiometric caps (wt %, by the dominant mineral; editable `caps_pct`). Defaults: Cu 79.9
(chalcocite), Pb 86.6 (galena), Zn 67.1 (sphalerite), Fe 72.4 (magnetite), S 53.4 (pyrite), Mo 59.9 (molybdenite),
Ba 58.8 (barite). A value above its cap cannot occur in any rock of that mineralogy. ERROR (Major).

Catalogue logic: Per analyte with a cap in `caps_pct` (wt %, by the dominant mineral): Cu 79.9 (chalcocite), Pb 86.6 (galena), Zn 67.1 (sphalerite), Fe 72.4 (magnetite), S 53.4 (pyrite), Mo 59.9 (molybdenite), Ba 58.8 (barite). A preferred value converted to wt % above its cap cannot occur in a rock of that mineralogy (a decimal, unit or keying error). Original samples only.

### ASY-029 — Downhole spike

*جهش درون‌چاهی عیار* · category E (Values) · v2 VAL-09

VAL-09: downhole spike: a value more than `factor` (10) times both downhole neighbours and above the field's
`quantile` (P95). INFO: often real (nugget), sometimes a decimal or sample-order error worth a look.

Catalogue logic: Original samples sorted downhole per hole: a value more than `factor` times both neighbours (both > 0, same hole) and above the field's `quantile` (P95). Often a real nugget, sometimes a decimal or sample-order error.

### ASY-030 — Repeated identical values downhole (copy-paste or fill-down)

*تکرار مقادیر یکسان پشت سر هم (کپی یا پرکردن خودکار)* · category E (Values) · v2 VAL-10

VAL-10: `min_run` (5) or more consecutive identical values above detection in one hole and analyte: possible
copy-paste or fill-down. "Above detection" means above the largest detection limit of the column and above its
lowest reported value (a reporting floor without `<` codes). WARNING (Minor). Block copies between holes are INT-009.

Catalogue logic: `min_run` or more consecutive original samples in one hole with exactly the same preferred value above the largest detection limit. Block copies between holes are INT-009.

### COL-001 — Duplicate HoleID

*شمارهٔ گمانهٔ تکراری* · category B (Collars) · v2 SCH-03

Catalogue logic: Exact duplicates of the canonical `hole_id` in `collar` (after N12). The issue shows both records side by side, with a field-by-field diff and the dependent row count per child table, and classifies them as *identical* or *conflicting*. With multiple sources, both records are kept under source-qualified keys and both sources are named. The later import never wins silently.

### COL-002 — Missing, zero or non-numeric X, Y, Z or EOH

*مختصات X، Y، Z یا عمق نهایی گمشده، صفر یا غیرعددی* · category B (Collars) · v2 COL-01

Catalogue logic: Flags: `x`, `y` or `z` NULL (including values nulled by IMP-005/006); `eoh_m` NULL or ≤ 0. A **zero** x or y is flagged only when it lies outside the project extent, because local grids legitimately have small values. Z = 0 on a `SURFACE` collar is flagged when |z_topo| > `z_zero_tol_m`, or, without a DEM, when the campaign median Z exceeds `z_zero_tol_m`. A missing `eoh_m` is derived for desurvey only (IMP-010).

### COL-003 — HoleID format inconsistent or near-duplicate IDs

*ناهمگونی قالب شمارهٔ گمانه یا شناسه‌های تقریباً تکراری* · category A (Schema and identifiers) · v2 SCH-05

SCH-05: hole IDs that differ only by case, spaces, `-`, `_`, `.` or (optionally) leading zeros of numeric parts,
across ALL tables (e.g. `DH-01`, `DH01`, `dh 01`). ERROR (Major), one issue per group, with a suggested target
(the collar ID; else the most frequent spelling). Suggestion only: merges happen through the approved ID-mapping
table (fix class ID_MAP), which is saved, applied to a corrected copy and logged.

Catalogue logic: (a) **Collisions under three normalisations**: exact; case-fold; case-fold + strip separators and leading zeros (= `hole_key`, 02 N12). For each group, the issue states which export targets would join the IDs and which would split them. (b) **Naming convention**: a profile regex (e.g. `^[A-Z]{2,4}-\d{2}-\d{3}[A-Z]?$`) and an allowed-character regex `^[A-Za-z0-9_\-./]+$` applied after normalisation; the offending code point goes in `value`. (c) Prefix outliers: a prefix used by < 1 % of holes.

### COL-004 — Duplicate or near-duplicate collar coordinates (twins, wedges, re-drills, true duplicates)

*مختصات تکراری یا بسیار نزدیک دهانه (دوقلو، گُوِه، بازحفاری، تکرار واقعی)* · category B (Collars) · v2 COL-02, SPA-03

Catalogue logic: ⟦`kdtree`, `drv_trace`⟧ Pairs with 2D distance < `near_dup_distance_m` and |ΔZ| < `near_dup_dz_m` are classified as: **TRUE_DUPLICATE** (identical surveys and intervals); **WEDGE** (shared collar and upper trace, divergence at depth; `parent_hole_id` or ID pattern); **REDRILL** (parent abandoned or EOH short of plan, later date); **TWIN** (separation at the mineralised pierce point ≤ `twin_max_distance_m`, declared or inferred). Divergence is measured on `drv_trace` at +50 m. Wedge pairs go to SUR-025 and CRS-010; twin pairs go to CRS-006.

### COL-005 — Collar outside licence boundary or project extent

*دهانه خارج از محدودهٔ پروانه یا گسترهٔ پروژه* · category H (Spatial, topography and boundary) · v2 COL-05

Catalogue logic: ⟦`drv_collar_spatial`, `layer:LICENCE`⟧ `in_licence = false` → issue with `dist_licence_edge_m`. A collar outside the project extent (profile `coord_plausibility` or a user extent) is always an issue, with or without a licence layer. Collars inside but within `edge_buffer_m` of the boundary → INFO "near boundary" (feeds SPA-004).

### COL-006 — Swapped X/Y, wrong UTM zone, lat/long in UTM fields, wrong horizontal datum

*جابجایی X و Y، زون UTM اشتباه، طول/عرض جغرافیایی در فیلد UTM، دیتوم افقی اشتباه* · category B (Collars) · v2 COL-03

Catalogue logic: N11 detection per collar and per campaign. Signatures: geographic magnitudes in projected fields; X in the northing range with Y in the easting range; implied longitude > 3.5° from the zone's central meridian; eastings in two clusters ≈ 600 km apart; **datum mismatch**, i.e. a constant offset vector of one campaign against other campaigns, the DEM (COL-024) or the map that matches a PROJ candidate. Candidates include ED50(ED77) → WGS 84 (≈ 175 m, mostly N–S; 02 §6.5) and the NCC Iran ED50 → WGS 84 transformation (EPSG:1514, translations ≈ −110/−98/−120 m).

### COL-007 — EOH shallower than the maximum depth in survey or interval tables

*عمق نهایی کمتر از بیشینهٔ عمق جداول انحراف‌سنجی یا بازه‌ای* · category B (Collars) · v2 COL-07

Catalogue logic: Per hole and child table t: `max_t` = max(to_m) for interval tables or max(depth_m) for point tables. Issue when `max_t − eoh_m > eoh_tol_m`. One issue per hole, naming the deepest table; measure = excess in m. **Fix evidence ranking:** driller's depth (COL-022) > last core block or run > last survey station > last sample. A round EOH (a multiple of 10 m) that disagrees with the data is probably the planned depth and is passed to COL-010 as evidence. EOH deeper than the data is an INT-004 bottom gap, not this rule.

### COL-008 — Collar without survey

*دهانهٔ فاقد انحراف‌سنجی* · category B (Collars) · v2 SCH-04

Catalogue logic: The hole has 0 accepted survey rows **but has a collar orientation** (`dip` not NULL). Without an orientation, COL-019 is raised instead. `PLANNED` holes are excluded.

### COL-009 — Collar without any interval data

*دهانهٔ فاقد هرگونه دادهٔ بازه‌ای* · category B (Collars) · v2 SCH-04

Catalogue logic: None of the registered interval or point tables except survey has rows for the hole. Reported by type ("logged but not assayed" is in INT-011; this rule is "neither logged nor sampled").

### COL-010 — Inferred collar survey method is handheld GPS, planned or digitised

*روش برداشت استنتاجی دهانه: جی‌پی‌اس دستی، طراحی‌شده یا رقومی‌شده از نقشه* · category B (Collars)

Catalogue logic: ⟦`drv_collar_method`, `drv_collar_spatial`⟧ The weights-of-evidence classifier (01 §6.10, evidence E1–E11) assigns a class in {HANDHELD_GPS, PLANNED, DIGITISED} with posterior ≥ `conf_min_frac`, or the declared method contradicts the inferred one ("declared RTK, evidence indicates handheld"). Additional evidence (RC): pickup date before drilling start; Z precision coarser than X/Y; X/Y on exact 100 m multiples; fence offsets equal to the design spacing; and COL-023 check-survey residuals, which carry the highest weight. The evidence list is shown in full.

### COL-011 — Collar–topography |ΔZ| above threshold

*اختلاف ارتفاع دهانه و توپوگرافی بیش از حد آستانه* · category H (Spatial, topography and boundary) · v2 COL-06

Catalogue logic: ⟦`drv_collar_spatial`, `drv_collar_method`, `dem_surface`⟧ `ΔZ = z − z_topo` (bilinear or TIN). **Adaptive band:** effective threshold = max(band, 2·σ_v,DEM, 2·σ_v,method), with σ_v,DEM from COL-025. The message gives the sign (floating above or buried below the surface). Not applicable to `UNDERGROUND` collars unless a development surface is supplied. No DEM coverage is reported by COL-025(f), never as a pass. Many collars with |ΔZ| < 0.05 m mean Z was draped from this DEM: such collars pass, and COL-010 receives the "derived Z" evidence.

### COL-012 — Systematic ΔZ offset (datum suspicion)

*جابجایی سیستماتیک ΔZ (احتمال اختلاف دیتوم)* · category H (Spatial, topography and boundary) · v2 COL-06b

Catalogue logic: ⟦`drv_collar_spatial`⟧ Robust (Huber) mean of ΔZ per group (campaign, inferred method, source CRS) with n ≥ `min_n`. Issue when |offset| ≥ max(`offset_min_m`, 3.86·s/√n) **and** the offset exceeds the residual robust SD. The offset is compared with the geoid undulation N (EGM96/EGM2008) at the project centroid: offset ≈ ±N within `geoid_tol_m` → "ellipsoidal heights stored as orthometric (or the reverse)". `vertical_crs_epsg` NULL is stated as context.

### COL-013 — Repeated identical Z values

*تکرار مقادیر یکسان ارتفاع دهانه* · category B (Collars)

Catalogue logic: Within a campaign, groups of ≥ `min_group_n` collars share exactly the same raw Z text, where the expected number of coincidences at the stated precision is ≤ 0.5 (Poisson, from the Z range and decimals). Also flagged: a constant Z across collars whose DEM relief exceeds `relief_m`.

### COL-014 — Date inconsistencies or drilling-rate outliers

*ناسازگاری تاریخ‌ها یا نرخ حفاری غیرعادی* · category B (Collars) · v2 COL-08

Dates (future, before `min_year`, completion before start, implausible drilling rate) and, v2 COL-08, drill-type
codes not in the known list (`drill_types`) or the `drill_method` code dictionary. WARNING (Minor).

Catalogue logic: Flags: `date_completed < date_started`; dates after the run date; dates before `min_year` or outside the campaign window; `collar_survey_date < date_started` (planned pickup, also COL-010 evidence); one `rig_id` on two holes whose date ranges overlap by > 1 day (double-booked rig: a date or rig error). **Rate** = eoh_m / (days + 1) per rig and method: robust z ≥ 4, or above `max_rate_m_day` for the method.

### COL-015 — Spacing outlier or clustered drilling (declustering needed)

*فاصله‌داری غیرعادی یا حفاری خوشه‌ای (نیاز به واخوشه‌بندی)* · category B (Collars)

Catalogue logic: ⟦`kdtree`, `drv_pierce_point`, `drv_composite`⟧ On collars **and** on pierce points at the mineralised-zone midpoint: (a) isolated holes with NN1 > `isolation_x_median` × median NN1; (b) Clark–Evans R (Donnelly) < `ce_clustered`; (c) cell declustering. Cell sizes run from the minimum NN to ½ the domain extent with ≥ 8 origin offsets. The size that minimises the declustered mean is chosen when high grades are preferentially drilled, but a size near the nominal sparse spacing is preferred. Issue when |naive − declustered| / declustered > `declus_diff_frac`.

### COL-016 — Coordinate outlier in X, Y or Z

*مختصات پرت X، Y یا Z* · category B (Collars)

Catalogue logic: (a) Robust Mahalanobis distance (MCD) on (x, y) per campaign > χ²₂(0.999). (b) A collar > `hull_dist_m` from the convex hull of all other collars. (c) Z: robust z ≥ 5 against the median Z of the k = 8 nearest collars when no DEM exists; with a DEM, COL-011 applies. (d) Z outside `z_range_m`. The issue proposes candidate corrections (adjacent-digit transposition, dropped or duplicated digit, sign) that would bring the collar into its cluster, as evidence only.

### COL-019 — No survey and no collar orientation: trace silently assumed vertical

*بدون انحراف‌سنجی و بدون جهت دهانه: مسیر گمانه به‌طور ضمنی قائم فرض می‌شود* · category B (Collars)

Catalogue logic: 0 survey rows **and** (`dip` NULL, or `azimuth` NULL with `dip` > −90 + `vertical_tol_deg`). The message states the consequence per export target: Datamine DESURV/HOLES3D treat the hole as vertical; Leapfrog cannot orient it. The trace is `ASSUMED_VERTICAL` and excluded from spacing at depth and proximity tests (01 §6.3). ↓WARNING when the design (`planned_dip`) or the hole type declares the hole vertical.

### CRS-004 — Candidate estimation domains not statistically separated

*عدم تفکیک آماری دامنه‌های پیشنهادی تخمین* · category F (Cross-table consistency)

Catalogue logic: On composites of each key analyte: Kruskal–Wallis across the lithology × alteration (and weathering) classes, then Holm-adjusted pairwise tests. Adjacent classes (ordered by median) with no significant difference **or** an effect < `effect_min` pooled MAD (v0.2: with thousands of samples even trivial differences are significant, so practical equivalence also counts) → INFO "merge candidates". Classes that differ significantly but sit in one profile domain → INFO "split candidate". CV > 2 within a domain → INFO "mixed populations". Produces the domain-suggestion table (report §11). MDE §1.9.

### CRS-005 — Contact behaviour (hard vs soft boundary)

*رفتار همبری (مرز سخت یا نرم)* · category F (Cross-table consistency)

Catalogue logic: Grade against signed distance along the hole to each contact between candidate domains, binned at composite length up to ± `max_dist_m`. A step model and a linear-ramp (gradational) model are fitted and compared by AIC. A transition width ≥ 2 composite lengths → INFO "soft boundary: share samples across the contact in estimation"; otherwise "hard boundary". Informs domaining; not an error test.

### DEN-001 — Implausible density for the lithology

*چگالی غیرمحتمل برای سنگ‌شناسی* · category F (Cross-table consistency) · v2 XTB-04

Catalogue logic: `density_gcm3` outside `abs_bounds_gcm3` → ↑ERROR (no rock has that density; a unit or keying error). Within the absolute bounds: outside the profile's `density_bounds_gcm3[group]` for the lithology group, or outside the robust fence median ± `k_mad`·1.4826·MAD of that lithology (n ≥ 20) → WARNING. The issue reports both bounds and the lithology statistics. Descriptive rule (§1.9).

### GEO-001 — Core recovery above 100 % or below 0

*بازیافت مغزه بیش از ۱۰۰ درصد یا منفی* · category F (Cross-table consistency) · v2 XTB-02

Catalogue logic: On `cr_pct_used`. CR < 0 → ERROR. CR > 100 + `cr_tol_pct` → ERROR. 100 < CR ≤ 100 + tolerance → INFO (measuring tolerance, swelling clays). **Diagnosis:** two consecutive runs, one above and one below 100 %, whose recovered lengths sum to within `cr_tol_pct` of the combined run length → "core-block misplacement", with a rebalancing proposal.

### GEO-002 — RQD greater than core recovery, or above 100 %

*RQD بزرگ‌تر از بازیافت مغزه یا بیش از ۱۰۰ درصد* · category F (Cross-table consistency) · v2 XTB-03

Catalogue logic: RQD and CR are both relative to run length (Deere; ISRM), so `rqd_length_m ≤ recovered_length_m` and RQD ≤ CR always. Flags: `rqd_pct_used` > `cr_pct_used` + `tol_pct`; RQD > 100 + `tol_pct`; RQD < 0 → ERROR.

### GEO-003 — Recorded and recomputed CR or RQD disagree

*مغایرت CR یا RQD ثبت‌شده با مقدار بازمحاسبه‌شده* · category F (Cross-table consistency)

Catalogue logic: Where raw lengths exist: |`cr_pct_rec` − `cr_pct`| > `diff_tol_pct` → WARNING; the same for RQD. Also `run_length_m` ≠ `to_m − from_m` beyond `len_tol_m`. **Pattern diagnosis per logger or campaign:** RQD computed against recovered length instead of run length (RQD_rec ≈ 100·rqd_length/recovered); a 2 × core-diameter piece threshold instead of 0.10 m; CR recorded on sample intervals (`interval_basis`).

### GEO-004 — Recovery–grade bias

*اریبی بین بازیافت و عیار* · category F (Cross-table consistency)

Catalogue logic: Per drilling method and domain, each sample gets the length-weighted CR of overlapping runs (core) or `recovery_mass_pct` (RC). Recovery classes per `classes_pct`. Kruskal–Wallis across classes and Mann–Whitney between the lowest and highest classes on log grade; Spearman ρ(recovery, grade). A significant difference with effect ≥ MDE (§1.9) → WARNING. The message states the direction and both readings: grade **lower** at low recovery suggests loss of soft or sulphide-rich fines; grade **higher** at low recovery more often reflects fractured mineralised structures than a bias, so the correlation within mineralised intervals only is also reported.

### IMP-003 — Character normalisation applied (digits, letters, invisible characters, whitespace)

*اعمال یکسان‌سازی نویسه‌ها (ارقام، حروف، نویسه‌های نامرئی، فاصله‌ها)* · category A (Schema and identifiers)

Catalogue logic: One issue per (table, field, step) from `normalisation_log`, covering N02–N04 and the N12/N13 folds: Persian/Arabic-Indic digits → Latin; `ي→ی`, `ك→ک`; ZWSP/BOM/LRM/RLM removed; NBSP → space; trim. `value` = count; evidence = ≤ 5 [raw, normalised] pairs.

### IMP-004 — Decimal or thousands separator ambiguous in a numeric column

*ابهام جداکنندهٔ اعشار یا هزارگان در ستون عددی* · category A (Schema and identifiers)

Catalogue logic: N05 per-column decision. The comma-bearing values fit neither decimal-comma (≥ 95 % `^-?\d+,\d+$`, no `.`) nor thousands-comma, or both fit (every value `d,ddd`). Also flags `1.234,56` mixed with `1,234.56`. Both alternatives are kept as a PROPOSED inference; values are provisional.

### IMP-005 — Value not parseable for its type, or unknown enum value

*مقدار غیرقابل تبدیل به نوع استاندارد یا مقدار شمارشی ناشناخته* · category A (Schema and identifiers) · v2 SCH-02

Catalogue logic: The typed parse failed (number, date, bool): canonical NULL, raw kept (02 E3). Or an enum value matches nothing and becomes `UNKNOWN` (E4). One issue per row, `value` = raw text; aggregated to one issue per (table, field) above `aggregate_above_n`. Excludes assay `TXT` (ASY-002) and placeholders (IMP-006).

### IMP-006 — Placeholder or sentinel set to NULL in a non-assay field

*جایگزینی مقدار جانشین یا نگهبان با تهی در فیلد غیرعیاری* · category A (Schema and identifiers) · v2 SCH-06

SCH-06: blank vs zero vs missing-code ambiguity in one numeric field. Per (table, field) the raw cells are classed
as blank, zero (only where zero is not a natural value: X, Y, EOH, density, run length, field strength), numeric
sentinel (`sentinels`) or text placeholder (`-`, `NA`, `?` …). Two or more of these representations of "missing" in
the same field → WARNING (Minor). Sentinels or placeholders alone → INFO, raised to WARNING in coordinate, depth or
angle fields. Nothing is converted: the counts are reported so the user can decide.

Catalogue logic: N07 counts per (table, field): placeholders (`-`, `?`, `NA`, `نامشخص` …) and numeric sentinels → NULL, raw kept.

### IMP-010 — Required canonical field unmapped or absent for the table type

*عدم نگاشت یا نبود فیلد الزامی استاندارد برای نوع جدول* · category A (Schema and identifiers) · v2 SCH-01

Catalogue logic: **Required sets:** collar {hole_id, x, y, z}; survey {hole_id, depth_m, azimuth, dip} or XYZ form {hole_id, depth_m, x, y, z} (SUR-024); interval {hole_id, from_m, to_m}, or to_m only (IMP-017); point {hole_id, depth_m}; assay {sample_id or (hole_id, from_m, to_m), analyte, value}. A missing required field makes dependent rules NOT_APPLICABLE. **Recommended:** collar.eoh_m, azimuth_ref, depth unit, survey instrument, assay sample_id and unit. Missing `eoh_m` is derived as the maximum child depth (provenance `DERIVED`), and the COL-007 and INT-004 bottom-gap results are labelled "not testable".

### IMP-011 — Depth unit inferred, unconfirmed or mixed within a table

*واحد عمق استنتاجی، تأییدنشده یا مختلط در یک جدول* · category A (Schema and identifiers)

Catalogue logic: N09 evidence: header tokens (`ft`, `فوت`), magnitude vs collar EOH, modal interval 1.524/3.048 m vs 1/2 m, modal run 3.048 m. (a) The inference is PROPOSED. (b) The table mixes units: the per-hole ratio of max depth to EOH clusters near 3.28 for some holes and 1 for others.

### IMP-012 — Coordinate format or CRS undeclared, inferred or implausible

*قالب یا سیستم مختصات اعلام‌نشده، استنتاجی یا غیرمحتمل* · category A (Schema and identifiers) · v2 COL-04

COL-04: CRS plausibility. (a) With a declared UTM zone (profile `crs: {utm_zone, hemisphere}` or `epsg`), collars
outside the zone's easting range (100–900 km) or the hemisphere's northing range → ERROR (Major). (b) Mixed
coordinate systems: clusters of ≥ 2 collars whose centre lies more than `cluster_sep_km` (20 km) from the main
cluster → ERROR, with the offset (a constant offset suggests a false-easting, zone or datum mix). (c) No CRS
declared → one INFO describing what the coordinates look like (never assumed).

Catalogue logic: N11 cases: format, CRS or zone set by a PROPOSED inference; a declared EPSG that is not projected in metres, or outside the Iran set (e.g. 32038 is probably a typo for 32638); MGRS band `S` read as southern hemisphere (+10 000 km); truncated northings; inferred zone ≠ declared zone. Systematic collar errors are reported by COL-006.

### IMP-014 — Date calendar or format ambiguous, Jalali detected, or calendars mixed

*ابهام قالب تاریخ، تشخیص تقویم جلالی یا تقویم‌های مختلط* · category A (Schema and identifiers)

Catalogue logic: After N04 digit folding, N08 applies. (a) Jalali values (year 1300–1499 or a Persian month name) are converted by `jalali_to_gregorian` (33-year arithmetic cycle) with month-length validation (1–6: 31 d; 7–11: 30 d; 12: 29/30 by leap rule). (b) Jalali and Gregorian mixed in one column. (c) DMY/MDY unresolved, or two-digit years. Corrected dates feed COL-014, SMP-008, SUR-014 and QA/QC time series.

### INT-001 — From ≥ To, zero-length or negative depth

*عمق «از» بزرگ‌تر یا مساوی «تا»، بازهٔ با طول صفر یا عمق منفی* · category D (Intervals and samples) · v2 INT-01, INT-02

Catalogue logic: Flags `from_m ≥ to_m − ε`, or either depth < 0. Zero-length rows are accepted only in tables registered as point/event; in sampled interval tables they are errors.

### INT-002 — Overlapping intervals

*همپوشانی بازه‌ها* · category D (Intervals and samples) · v2 INT-03

Real overlaps (> the global depth tolerance) are CRITICAL; smaller ones are precision artefacts (INT-012).

Catalogue logic: Sorted by (hole, from, to) with a **running maximum** of `to_m` per hole (01 §5.5), which also finds intervals contained in an earlier long interval. Overlap = `runmax_prev − from_m` > ε. Classified as partial, containment or full-span (a full span with identical values → INT-003). Overlaps ≤ `micro_overlap_m` → ↓INFO "precision artefact" with a snap proposal. Evaluated **within one logging version** (INT-018) and one sample set. Overlapping records of different sample support → ASY-027.

### INT-003 — Duplicate or conflicting intervals (and point records)

*بازه‌ها یا رکوردهای نقطه‌ای تکراری یا متناقض* · category D (Intervals and samples) · v2 SCH-03

Catalogue logic: Same (hole_id, from_m, to_m) within ε. **Scope extended to point tables** on (hole_id, depth_m, type); several structures at one depth are allowed when `struct_type` differs. Identical values → "duplicate", including mobile-capture **sync duplicates** (same values, different source record IDs or timestamps); the proposal is to VOID the newer copy. Different values → "conflict": both are kept and review is required. The latest record is never auto-selected.

### INT-004 — Top, internal or bottom gaps

*فاصلهٔ خالی در ابتدا، میانه یا انتهای گمانه* · category D (Intervals and samples) · v2 INT-04

Catalogue logic: Top gap: first `from_m` > `top_gap_tol_m`. Internal gap: `from_i − runmax_{i−1}` > ε. Bottom gap: `eoh_m − last runmax` > `bottom_gap_tol_m`. Gaps < `micro_gap_m` → ↓INFO (precision). **Policy by table kind:** tables expected to be contiguous (lithology, weathering, geotech_run) → WARNING. Discontinuous tables (sample) → ↓INFO, except gaps inside a logged mineralised interval (→ ASY-008) or whose samples are pending at the lab (SMP-005, INFO "pending"). The issue states the composite effect: Leapfrog skips gaps; Datamine COMPDH absorbs small gaps, fills medium gaps with a dummy sample and ends composites at large gaps.

### INT-005 — Interval or point beyond EOH

*بازه یا نقطهٔ فراتر از عمق نهایی* · category D (Intervals and samples) · v2 INT-05

Catalogue logic: `to_m − eoh_m` > ε (point tables: `depth_m`). Linked to the hole-level COL-007 issue, which carries the fix.

### INT-006 — HoleID not in collar

*شمارهٔ گمانه در جدول دهانه وجود ندارد* · category D (Intervals and samples) · v2 SCH-04, SCH-04b

Catalogue logic: As SUR-001, for every interval, point and sample table. The issue reports a `hole_key` match (join error) or no match (missing collar).

### INT-007 — Non-standard or extreme sample length

*طول نمونهٔ غیراستاندارد یا بسیار کوتاه/بلند* · category D (Intervals and samples) · v2 INT-06

v2 INT-06: sample length outside the limits for the hole's drill type (defaults 0.1–6 m; Minor).

Catalogue logic: Flags `length_m` < `short_m` or > `long_m`, or not within `std_tol_m` of a profile standard length. Per domain, Spearman ρ(length, grade) with |ρ| > `rho_thr` (p < 0.01, n ≥ 100) → INFO that unweighted statistics are biased and length weighting and compositing are mandatory (short samples concentrate in high grade where sampling follows geology).

### INT-008 — Sample crosses a geological contact

*عبور نمونه از مرز زمین‌شناسی* · category D (Intervals and samples)

Catalogue logic: ⟦`drv_interval_master`⟧ For `ORIGINAL` samples: count contact boundaries of the lithology, alteration and mineralisation tables inside (from + `contact_tol_m`, to − `contact_tol_m`). By default only contacts that change `mineralisation_class` or a profile domain group are counted. Reports the % of samples crossing per table, and the list.

### INT-009 — Copy-paste repetition pattern

*الگوی تکرار ناشی از کپی‌برداری* · category D (Intervals and samples)

A block of `min_window_n` (5) consecutive rows (values and codes) that occurs again elsewhere, in another hole or
the same one: possible copy-paste. Windows with fewer than 3 distinct rows are ignored (uniform runs are legitimate).
Vectorised: each window gets a 64-bit polynomial hash of its row hashes; repeated keys are the copies. WARNING.

Catalogue logic: Row hashes of the value columns; sliding windows of k ≥ `min_window_n` consecutive rows per hole; windows found in ≥ 2 holes, or twice in one hole at different depths, are verified exactly. **Low-information windows are excluded:** all BDL, one constant code, or < 3 distinct numeric values.

### INT-010 — Missing or non-numeric HoleID, From or To

*شمارهٔ گمانه، «از» یا «تا» گمشده یا غیرعددی* · category D (Intervals and samples)

Catalogue logic: Flags `hole_id` NULL or empty, or `from_m`/`to_m` NULL (including raw text nulled by IMP-005), per row. The row is kept, but interval rules cannot place it.

### INT-012 — Depth precision or rounding artefacts

*دقت عمق ناسازگار یا اثر گردکردن* · category D (Intervals and samples) · v2 INT-03, INT-04

v2 brief §5.4: overlaps and gaps no larger than the global depth tolerance (`depth_eps_m`, default 0.001 m) are
precision artefacts. They are reported here (Minor), never mixed with real overlaps (INT-002) or gaps (INT-004).

Catalogue logic: Distribution of `from_raw`/`to_raw` decimals per table, campaign and source. Flags: mixed precision within a campaign; core holes with whole-metre depths while runs are recorded to cm (INFO); depths on multiples of 0.3048/1.524/3.048 in a table declared in metres (WARNING, unit suspicion passed to IMP-011); float artefacts such as `12.499999` (INFO, snap proposal).

### INT-013 — Unmerged consecutive identical records

*رکوردهای پیاپی یکسان ادغام‌نشده* · category D (Intervals and samples)

Catalogue logic: Contiguous intervals (|to_i − from_{i+1}| ≤ ε) with identical values in every mapped attribute (comments and logger excluded), in logging tables. Not run on lithology, which LIT-002 owns, nor on sample tables.

### INT-015 — Value outside controlled vocabulary

*مقدار خارج از واژه‌نامهٔ کنترل‌شده* · category E (Values) · v2 VAL-08

VAL-08: logged codes not in the user's code dictionary (profile `code_dictionaries`, or a dictionary file).
Keys are canonical fields (lith_code, alt_type, weathering, drill_method …) or source column names. Matching ignores
case and surrounding spaces. ERROR (Major), one issue per (table, field, code) with its count.

Catalogue logic: Coded fields (`code<DOM>`) **not owned by** LIT-001, ALT-001, MIN-001, WTH-002 or STR-003, e.g. `grain_size`, `texture`, `strat_unit`, `core_size`, `contact_top_type`, codes in `ext_` tables. The raw code has no CONFIRMED synonym, so it was auto-added as `PROPOSED` (02 E5). Fuzzy candidates are listed with scores.

### LIT-001 — Lithology code not in the dictionary, or synonym variants

*کد سنگ‌شناسی خارج از فرهنگ کدها یا گونه‌های هم‌معنا* · category E (Values)

Catalogue logic: Inventory of raw codes with counts, metres, holes and loggers (always reported, INFO). (a) A raw code without a CONFIRMED mapping in `LITH`, auto-added as PROPOSED → WARNING. (b) **Synonym clusters:** after case, space and punctuation folding (02 §6.6), the Persian–English transliteration and abbreviation tables, Levenshtein ≤ `lev_max` (1 for codes ≤ 4 characters, 2 for longer) or Jaro–Winkler ≥ `jw_min`. A cluster with ≥ 2 raw variants → WARNING proposing one harmonised code. (c) A code absent from the project legend (`code.source ≠ LEGEND` when a legend was loaded) → WARNING. Applies equally to `strat_unit` (domain `STRAT`).

### LIT-002 — Thin interval or unmerged consecutive identical units

*بازهٔ بسیار نازک یا واحدهای یکسان پیاپی ادغام‌نشده* · category E (Values)

Catalogue logic: (a) `length_m < thin_m`, skipping `thin_exempt_codes` (veins, dykelets, gouge) → INFO. A hole whose share of thin intervals exceeds `thin_share_frac` → WARNING "over-splitting". (b) Consecutive intervals (|to_i − from_{i+1}| ≤ ε) with the same `lith_code`, `lith_code_2` and `strat_unit` → INFO with a merge proposal. Thickness distribution per unit is reported with the issue.

### LIT-003 — Illogical downhole sequence

*توالی غیرمنطقی در طول گمانه* · category E (Values)

Catalogue logic: (a) **Forbidden sequences** from the profile and project rules (`FAM-901…`): e.g. a cover unit (`is_cover`) below bedrock, unless `allow_cover_below` (karst infill, thrust repetition) → WARNING. (b) **Stratigraphic inversion:** codes with `sequence_rank` whose rank decreases downhole, with no FAULT structure or `contact_top_type = FAULTED` within `fault_buffer_m` of the contact → WARNING. (c) **Rare transitions:** embedded Markov chain of downhole contacts (self-transitions removed), `P(i→j) = n_ij / n_i`. A transition with `n_ij ≤ rare_n` and `P ≤ rare_p`, whose expected count under quasi-independence is ≥ 5 → INFO "rare transition". The transition-probability matrix is a report figure.

### QAQ-001 — Insufficient insertion rate or no QA/QC

*نرخ درج ناکافی یا نبود کنترل کیفیت* · category G (Laboratory and QA/QC reconciliation)

Catalogue logic: ⟦`drv_qaqc_batch`⟧ Insertion rate per company QC type = `100·n_type / n_ORIGINAL`, computed per campaign, lab and calendar quarter, and for the project. `LAB_*` types are excluded. (a) A campaign whose assays enter the estimation set has no company QC of any type → CRITICAL. (b) A type's rate below its target → WARNING; below half the target → ERROR. (c) Resource profiles: umpire share of mineralised pulps below target → WARNING. The full rate table (by type, campaign and lab) is always printed. Whether CRMs cover the right grades is tested by QAQ-009.

### QAQ-002 — CRM failure (±3 SD), Westgard violation or bias

*شکست ماده مرجع (±۳ انحراف معیار)، نقض قواعد وستگارد یا اریبی* · category G (Laboratory and QA/QC reconciliation)

Catalogue logic: ⟦`drv_qaqc_crm`⟧ Each result is compared with the **method-compatible** certified value (QAQ-008): `z = (v − certified)/sd_1`. (a) |z| > `qaqc.sd_fail` → ERROR, batch FAIL. |z| > `qaqc.sd_warn` → WARNING. (b) Westgard multi-rules per CRM × analyte × lab, in `analysed_date`/`seq_no` order: `2_2s` (two consecutive beyond 2 SD on the same side) and `R_4s` (two consecutive with range > 4 SD) → ERROR; `4_1s` (four consecutive beyond 1 SD on the same side) and `10_x` (ten consecutive on one side of the certified value) → WARNING. (c) **Bias** per CRM × analyte × lab × period: `bias_pct = 100·(mean − certified)/certified` with a 95 % CI. |bias| > `bias_warn_pct` with the CI excluding 0 → WARNING; > `bias_err_pct` → ERROR. MDE in §1.9. Indicative values (`is_certified = FALSE`) are charted but never fail a batch. A result flagged by QAQ-006 (probable mislabel) is held as REVIEW and not counted as a failure until resolved.

### QAQ-003 — Blank contamination or carry-over

*آلودگی بلانک یا انتقال آلودگی* · category G (Laboratory and QA/QC reconciliation)

Catalogue logic: ⟦`drv_qaqc_blank`⟧ (a) A result above `blank_warn_x_dl`·DL → WARNING. Above `blank_fail_x_dl`·DL, or above `blank_value.max_acceptable` → ERROR, batch FAIL. For certified blanks, the limit is `expected_value + 3·sd_1`. (b) **Diagnosis** of each elevated blank, from the preceding sample by `seq_no`: *carry-over* (predecessor ≥ the project's `carry_hi_quantile` grade; prep or instrument contamination); *contamination* (no high predecessor); *blank material* (persistent elevation within one blank lot: check the blank source). Spearman ρ of blank value against predecessor value, per lab. (c) Coarse blanks test preparation; pulp blanks test analysis; the message names which stage failed.

### QAQ-004 — Duplicate precision failure (HARD)

*شکست دقت نمونه‌های تکراری (HARD)* · category G (Laboratory and QA/QC reconciliation)

Catalogue logic: ⟦`drv_qaqc_pair`⟧ Only pairs with `valid_for_precision` and a valid linkage (QAQ-010) are used. Per pair type × analyte × lab × period: the share of pairs with `hard_pct > hard_limit_pct[type]`, tested against `max_fail_frac` (one-sided binomial; MDE §1.9). Exceeding → WARNING. A share above 2 × `max_fail_frac` on **pulp** duplicates (analytical precision) → ERROR. The issue carries RMS CV (§1.10), the ranked-HARD curve, signed MPD and the Thompson–Howarth fit `s = s₀ + k·c` (bins of ≥ 11 pairs ordered by pair mean), so the reviewer sees precision against concentration.

### SMP-001 — Sample ID not unique project-wide

*شناسهٔ نمونه در کل پروژه یکتا نیست* · category A (Schema and identifiers) · v2 INT-07

INT-07: a sample ID used by more than one row anywhere in the assay tables (QC samples included). CRITICAL: two
results under one ID cannot both be right, and the wrong one may be used in estimation.

Catalogue logic: The same `sample_id` on more than one register row → ERROR. IDs that coincide only after the shared normalisation key (case, leading zeros, separators; COL-003 key) → WARNING "near-duplicate".

### SMP-002 — Sample-number sequence gaps or unused tickets

*شکاف در توالی شمارهٔ نمونه یا بلیت‌های استفاده‌نشده* · category D (Intervals and samples) · v2 INT-07

INT-07: numbering of sample IDs (prefix + number). (a) Missing numbers inside a numbering run, counting QC
samples inserted in the same sequence as used numbers so CRMs, blanks and duplicates never create false gaps;
jumps larger than `max_gap_n` (100) start a new block (INFO). (b) Original samples whose numbers do not increase
(or decrease) monotonically downhole. WARNING (Minor).

Catalogue logic: The numeric part of each prefix series is parsed per dispatch and per hole. Gaps not explained by `sample_status` VOID, LOST or NOT_SENT, or by QC slots → INFO. ↑WARNING when the gap lies inside a mineralised interval, or exceeds `gap_share_max_frac` of a dispatch.

### SUR-001 — Survey HoleID not in collar

*شمارهٔ گمانهٔ انحراف‌سنجی در جدول دهانه وجود ندارد* · category C (Downhole survey) · v2 SCH-04, SCH-04b

Catalogue logic: Exact `isin` on the canonical `hole_id`. The issue states whether the orphan matches a collar under `hole_key` (case-fold, separators, leading zeros), which indicates a join error, not a missing collar.

### SUR-002 — Duplicate survey depth

*عمق تکراری ایستگاه انحراف‌سنجی* · category C (Downhole survey) · v2 SRV-04, SCH-03

Catalogue logic: Two stations of the same set with |depth_i − depth_j| ≤ ε. **Identical values** (|Δdip|, |ΔA|∘ ≤ 0.1°) → ↓INFO with a merge proposal. **Conflicting values** → ERROR, showing both stations. Coincident depths across *different* sets belong to SUR-021/022, never here.

### SUR-003 — Dip out of range

*شیب خارج از محدودهٔ مجاز* · category C (Downhole survey) · v2 SRV-02

Catalogue logic: Raw dip outside −90 … +90 after the declared convention is applied. Sentinels go to SUR-020 first and are not reported as dips. Values of 0–30 in a hole whose collar dip ≈ −90 indicate an **inclination-from-vertical** convention; they are passed to SUR-005, not reported as range errors.

### SUR-004 — Azimuth out of range

*آزیموت خارج از محدودهٔ مجاز* · category C (Downhole survey) · v2 SRV-02

Catalogue logic: Raw azimuth outside [0, 360). Exactly 360 → ↓INFO (normalised to 0). Values in (360, 720] usually mean a declination or convergence was added without a modulo: propose −360. Values in [−360, 0) mean west-negative notation: propose +360. A column whose values reach 400 with no other explanation → gon inference. Sentinels → SUR-020.

### SUR-005 — Mixed dip sign convention

*ناسازگاری قرارداد علامت شیب* · category C (Downhole survey) · v2 SRV-03

Catalogue logic: Within one hole: positive and negative dips, excluding UNDERGROUND up-holes and near-horizontal holes (−5° … +5°) that may legitimately cross horizontal. Within the project: campaigns using different conventions (`dip_convention_src`), or a hole whose survey sign contradicts its collar dip, design dip or hole type ("hole heading back to surface"). **The convention is never inferred from the majority sign when underground up-holes exist.** Evidence used instead: `collar_location`, hole type, design dip, and collar position relative to topography.

### SUR-006 — Survey depth beyond EOH

*عمق ایستگاه انحراف‌سنجی بیشتر از عمق نهایی* · category C (Downhole survey) · v2 SRV-06

Catalogue logic: `depth_m − eoh_m > survey_overrun_tol_m` → ERROR. Smaller overruns are ↓INFO, because tools legitimately log slightly past the driller's EOH (depth counter, stick-up). The fix proposal comes from COL-007, never "reset EOH to last station".

### SUR-007 — First station too deep, or no collar orientation

*نخستین ایستگاه بسیار عمیق یا نبود جهت دهانه* · category C (Downhole survey) · v2 SRV-01

SRV-01: no station at 0 m. States what the desurvey assumes between the collar and the first station: the collar
orientation when the collar has azimuth and dip, otherwise the first station's direction extended to the collar.
WARNING (Minor); the message adds "far from the collar" beyond `first_station_max_m` (30 m).

Catalogue logic: The first *measured* station is deeper than `first_station_max_m`. The message states whether the collar orientation is used as station 0 (02 §4.22) or, if there is none, that the top of the hole is extrapolated from the first station. Synthetic stations (SUR-023) do not count as measured.

### SUR-008 — Station spacing too large or irregular; trace extrapolated

*فاصلهٔ ایستگاه‌ها بسیار زیاد یا نامنظم؛ برون‌یابی مسیر* · category C (Downhole survey) · v2 SRV-10

Catalogue logic: Spacing includes the collar → first station and last station → EOH segments. (a) Any gap > `max_spacing_m`, or > `max_spacing_curved_m` where the bracketing DLS > 3°/30 m. (b) **Extrapolated length** = eoh_m − last station > `extrap_max_m` or > `extrap_max_frac` × hole length → "trace extrapolated" (Leapfrog and Datamine hold the last direction). (c) CV of spacing > 1.0 → ↓INFO "irregular".

### SUR-009 — Design-only or constant survey (unsurveyed hole)

*برداشت طراحی‌شده یا ثابت (گمانهٔ برداشت‌نشده)* · category C (Downhole survey) · v2 SRV-15

Catalogue logic: Hole length > `min_length_m` and any of: all measured stations identical within 0.01°; all stations equal to the collar design (`planned_azimuth`/`planned_dip`); `survey_type = PLANNED`. The hole is counted as unsurveyed in the T1.08 statistics and in the Survey component (01 §8.1 design-only = 10).

### SUR-010 — Dogleg severity above threshold

*شدت خمیدگی (داگ‌لگ) بیش از حد آستانه* · category C (Downhole survey) · v2 SRV-08

Catalogue logic: ⟦`drv_trace`⟧ For consecutive stations: **β = arccos(cos(I₂−I₁) − sin I₁·sin I₂·(1 − cos(A₂−A₁)))**, computed as arccos(t₁·t₂) from direction cosines for stability near vertical. **DLS = β·30/ΔMD** (°/30 m). When ΔMD < `min_dmd_m`, the absolute β is tested against the band value instead, so short spacing does not inflate DLS. A single station above the ERROR band, bracketed by normal stations, is labelled "probable reading error" (cf. SUR-013). Oasis curvature equivalent: 3°/30 m = 0.1°/m.

### SUR-011 — Large dip change between stations

*تغییر زیاد شیب بین ایستگاه‌ها* · category C (Downhole survey)

Catalogue logic: Flags |Δdip| > `max_dip_change_deg` per station pair (Micromine/Discover style), **or** |Δdip|·30/ΔMD > `max_dip_change_deg_30m` (Datamine style). The issue reports which test triggered. A large change between closely spaced stations points to an entry error.

### SUR-012 — Large azimuth change (dip shallower than −85° only)

*تغییر زیاد آزیموت (فقط برای شیب کم‌تر از ۸۵− درجه)* · category C (Downhole survey) · v2 SRV-11

Azimuth change between stations above `max_az_change_deg` (10°) or `max_az_change_deg_30m` (20°/30 m), WARNING.
SRV-11: stations with inclination below 3° are excluded from every azimuth-based check (SUR-012, SUR-013, SUR-023,
SUR-027); one INFO per hole states that the suppression was applied.

Catalogue logic: Flags |ΔA|∘ > `max_az_change_deg`, or > `max_az_change_deg_30m` normalised per 30 m. The difference is wrapped (359° → 1° = 2°). **Suppressed** (↓INFO context) where either station is steeper than `suppress_steeper_than_dip_deg`, because azimuth is unstable near vertical. This suppression is a GEOVALID improvement that is not described in the vendor checks.

### SUR-013 — Azimuth spike: probable magnetic interference

*جهش آزیموت: احتمال تداخل مغناطیسی* · category C (Downhole survey) · v2 SRV-09

SRV-09: neighbour-inconsistent station. Station i deviates by more than `dev_deg` (2°) from the direction
interpolated between stations i−1 and i+1, while i−1 and i+1 agree within `agree_dls_30m` (1°/30 m). Likely a typo
or magnetic interference. ERROR (Major); `unreliable_n` (3) such stations in one hole add a hole-level ERROR.
Near-vertical stations (SRV-11) are compared on dip only.

Catalogue logic: Per hole, for magnetic instruments (`is_magnetic`, or assumed under SUR-018), on stations that **passed SUR-027**. A spike is a single-station excursion that returns to trend: Δ⁻ = a_i − a_{i−1} and Δ⁺ = a_{i+1} − a_i exceed `spike_deg` with opposite signs, **and** the residual from a centred rolling median (window 5) exceeds `spike_deg`. In the CROSS stage the spike is correlated with logged magnetite/pyrrhotite, Fe, MS and EMS total-field anomalies within ±`corr_window_m`. Correlated, with a stable dip → "instrument (magnetic) error". Uncorrelated, with a co-varying dip → "real deviation".

### SUR-014 — Azimuth reference (magnetic

*true / grid) inconsistency / ناسازگاری مرجع آزیموت (مغناطیسی، جغرافیایی، شبکه)* · category C (Downhole survey) · v2 SRV-12

SRV-12: azimuth north reference. (a) Undeclared (no `north_ref` field and no profile `north_reference`): WARNING.
(b) Mixed references in one project: ERROR. (c) When magnetic and corrected azimuths both exist, their difference
must equal the declination (TRUE) or declination − grid convergence (GRID) within `tol_deg` (1°); without a
declination parameter, holes differing from the project median correction by more than `tol_deg` are flagged.
ERROR (Major).

Catalogue logic: Flags: `azimuth_ref = UNKNOWN` for a magnetic tool; a depth-constant ΔA between sets in one hole (e.g. gyro vs EMS, SD < 0.5°) or between design and first station per campaign that is ≈ the declination δ (IGRF14 at the station, survey date after IMP-014) or ≈ the convergence γ. The measured offset, model δ and γ are shown side by side. γ ≈ Δλ·sin φ reaches ≈ 1.3–1.9° at Iranian zone edges. A depth-localised ΔA correlated with magnetics is SUR-013/027, not this rule.

### SUR-015 — Desurvey-method EOH difference above threshold

*اختلاف موقعیت انتهای گمانه بین روش‌های محاسبهٔ مسیر بیش از حد آستانه* · category C (Downhole survey) · v2 SRV-14

SRV-14: desurvey sensitivity. EOH XYZ from tangential, balanced tangential and minimum curvature
(RF = (2/β)·tan(β/2), RF = 1 as β → 0); the largest pairwise distance per hole. One INFO summary for the project;
WARNING (Minor) for holes above `eoh_diff_m` (2 m).

Catalogue logic: ⟦`drv_trace_compare`⟧ Compares MIN_CURV (default) with BAL_TAN, TAN and the methods the enabled export targets actually use: Leapfrog spherical arc / balanced tangent, Datamine DESURV arcs, Vulcan balanced tangent, Leapfrog raw tangent for trenches. Reports EOH and maximum mid-hole offsets. **Includes the straight-line trace** where the source carries a linear/curved flag (Surpac): a hole flagged LINEAR but with total angular change > `linear_flag_deg` is reported with its offset.

### SUR-016 — Trace crosses another trace, or exits above topography

*تقاطع مسیر با گمانهٔ دیگر یا خروج مسیر از سطح زمین* · category H (Spatial, topography and boundary) · v2 SPA-01, SPA-02

Catalogue logic: ⟦`drv_trace`, `kdtree`, `dem_surface`⟧ (a) **Proximity:** KD-tree on 1 m trace points, refined by segment–segment distance; minimum 3D distance between two holes < `cross_dist_m` → probable survey or collar error. Excluded: the same hole, and parent–daughter pairs above the kick-off depth. (b) **Exit:** a trace point below `collar_zone_m` with z > z_topo + `exit_tol_m`. UNDERGROUND holes are tested against a development surface if one is supplied.

### SUR-017 — Negative station depth, or stations out of source order

*عمق منفی ایستگاه یا ترتیب نادرست ایستگاه‌ها در منبع* · category C (Downhole survey) · v2 SRV-05

Catalogue logic: (a) `depth_m` < 0 → ERROR. (b) In `src_row` order, depth decreases from the previous row of the same hole → WARNING. Sorting resolves the order, but a decreasing step that coincides with a change of survey date or instrument indicates a block of rows assigned to the wrong hole.

### SUR-020 — Survey station with null or dummy dip or azimuth (partial station)

*ایستگاه برداشت با شیب یا آزیموت تهی یا ساختگی (ایستگاه ناقص)* · category C (Downhole survey)

Catalogue logic: Sentinels are classified as missing before SUR-003/004 run. Null dip → ERROR. Null azimuth with dip steeper than `steep_dip_cutoff_deg` → INFO (azimuth immaterial). Null azimuth otherwise → WARNING. Null or sentinel `depth_m` → ERROR. For dip-only holes (acid tube, Tropari), the proposal is to carry the collar or previous azimuth flagged `ASSUMED`, never automatically.

### SUR-023 — Collar orientation conflicts with the near-collar station; synthetic stations tagged

*تعارض جهت دهانه با ایستگاه نزدیک دهانه؛ شناسایی ایستگاه‌های ساختگی* · category C (Downhole survey) · v2 SRV-07

SRV-07: collar azimuth/dip against the first survey station within `max_first_depth_m` (50 m). ERROR (Major) when
dip differs by more than `dip_tol_deg` (5°) or azimuth by more than `az_tol_deg` (10°, wrapped at 0/360; not tested
for near-vertical holes).

Catalogue logic: Holes with collar dip/azimuth and a measured station at depth ≤ `near_collar_m`. Flags d_dip = |dip_collar − dip_s| > `dip_tol_deg`, or d_az = |A_collar − A_s|∘ > `az_tol_deg` (only if dip_s is shallower than −85°). The collar values are labelled "design" when they equal `planned_*` or are round (−60/−90; 0/90/180/270). **Synthetic stations** (depth 0 equal to the collar orientation or to the next station within 0.01°) are tagged provenance `DERIVED` (INFO) and never count as measured in SUR-007, SUR-009 or SUR-028. The message states which orientation each target will use (the survey table governs in Leapfrog and Datamine).

### SUR-027 — Magnetic azimuth unreliable: station QC failure or magnetic environment

*آزیموت مغناطیسی نامعتبر: شکست کنترل کیفی ایستگاه یا محیط مغناطیسی* · category C (Downhole survey) · v2 SRV-13

SRV-13: magnetic interference indicators. (a) Total field strength (`mag_field`) differs from the expected value
(`expected_field_nt`, or the project median) by more than `field_tol_nt` (300 nT). (b) On magnetic instruments,
azimuth swings above `az_swing_deg` (5°) between consecutive stations while dip is stable within `dip_stable_deg`
(0.5°). WARNING (Minor). Gyro surveys and near-vertical stations are skipped.

Catalogue logic: (a) **Station QC**, where the tool reports raw QC values (`mag_field_nt`, `mag_dip_deg`, gravity). B_ref and I_ref come from IGRF14 at the station position and corrected date. |B − B_ref| > `b_tol_nt` or |I_m − I_ref| > `mag_dip_tol_deg` → azimuth invalid. |G − 1 g| > `g_tol_g` → dip and azimuth invalid. (b) **Environment**, magnetic tools only. Station depth ≤ casing depth + `casing_buffer_m`, or surveyed inside rods without non-magnetic spacing → ERROR. Within ±`neighbourhood_m` of MS > `magsus_thr_e3_si`, logged magnetite/pyrrhotite ≥ `mt_po_thr_pct`, or Fe ≥ the profile threshold → WARNING. This catches the smooth, persistent bias that never forms a SUR-013 spike.

