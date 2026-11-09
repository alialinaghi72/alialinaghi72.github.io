# GEOVALID PRO 0.4.0 — راهنمای سریع / Quick start

## فارسی

**اجرا:** فایل `GEOVALID.exe` را دوبار کلیک کنید. نصب لازم نیست و برنامه کاملاً آفلاین کار می‌کند. پوشهٔ `_internal` را کنار فایل exe نگه دارید.

**گام‌ها**
1. **افزودن فایل…**: فایل‌های CSV/TXT/XLSX/XLS پایگاه داده را انتخاب کنید (دهانه، انحراف‌سنجی، آنالیز، سنگ‌شناسی، ژئوتکنیک، چگالی…). نوع هر جدول و نگاشت ستون‌ها، حتی با سرستون فارسی، خودکار تشخیص داده می‌شود. با «نگاشت فیلدها…» می‌توانید آن را اصلاح کنید.
2. **ورودی‌های اختیاری:**
   - توپوگرافی، با تشخیص خودکار قالب: GeoTIFF، شبکهٔ ESRI ASCII (`.asc`)، Surfer (`.grd`)، BIL/BIP/BSQ/FLT با `.hdr`، SRTM (`.hgt`)، فایل نقطه‌ای XYZ/CSV، DXF (نقطه، منحنی میزان، 3DFACE)، Surpac (`.str` و `.dtm`)، OBJ، STL، PLY، Shapefile و KML/KMZ. هر قالب گزارش می‌دهد چه چیزی خوانده است (گستره، تفکیک، تعداد نقاط، سیستم مختصات).
   - محدودهٔ پروانه: KML/KMZ، Shapefile، GeoJSON، DXF (چندضلعی بسته) یا فهرست رئوس در CSV/TXT/XLSX. چندبخشی و دارای حفره پشتیبانی می‌شود.
   - جدول مواد مرجع (گواهی CRM) با ستون‌های `CRM_ID, ELEMENT, CERTIFIED, SD, UNIT`؛ مقدار تأییدشده با واحد اعلام‌شده تبدیل و گزارش می‌شود.
   - **فایل آزمایشگاه / QA-QC** در قالب GEOQAQC (همان فایلی که برای GEOQAQC آماده می‌کنید) و **فایل آزمایشگاه داور**.
   - **پوشهٔ نسخهٔ قبلی داده‌ها** برای مقایسهٔ نسخه‌ها و **تصویر پذیرفته‌شده** (JSON) برای کنترل گمانه‌های قفل‌شده.
   - پروفایل YAML یا JSON.
3. **اجرای اعتبارسنجی**: پس از اجرا، «داشبورد» شمار مسائل، نمودارها و مهم‌ترین یافته‌ها را نشان می‌دهد. «مسائل» فهرست قابل جستجو و جزئیات هر مسئله است. «باز کردن گزارش» گزارش HTML را باز می‌کند.
4. **تحلیل عیار و نمودارها**: بیش از ۲۵ نمودار تعاملی (بزرگ‌نمایی، جابه‌جایی، ذخیره به PNG/SVG/PDF). عنصر، ویژگی توصیفی، گمانه و عیار حد را از بالای نمودار انتخاب کنید؛ پنل «تفسیر» آمار و دامنه‌های پیشنهادی را نشان می‌دهد. مهم‌ترین نمودارها:
   - ماتریس η²: هر ویژگی توصیفی (سنگ‌شناسی، دگرسانی، هوازدگی، شدت دگرسانی، رنگ، فاز حفاری…) چه سهمی از تغییرات عیار را توضیح می‌دهد؛
   - عیار به تفکیک واحد (جعبه‌ای لگاریتمی با میانگین وزنی طولی و عیار حد)، میانهٔ عیار در ترکیب دو ویژگی (مثلاً سنگ‌شناسی × دگرسانی)، V کرامر؛
   - تحلیل همبری (مرز سخت یا نرم)، ترکیب واحدها با عمق، لاگ ستونی گمانه، چگالی و RQD به تفکیک واحد؛
   - نمودارهای نواری (Swath)، نقشهٔ عیار × ضخامت، منحنی عیار–متراژ؛
   - احتمال لگاریتمی، همبستگی عناصر، نمودار پراکنش، نقشهٔ دهانه‌ها، کنترل CRM، بلانک و HARD.
5. **پوسته**: دکمهٔ «پوسته» بین نمای تیره (Obsidian) و روشن (Ivory) جابه‌جا می‌کند.
6. **کنترل انحراف‌سنجی**: برای هر گمانه نمودار شیب، آزیموت و شدت خمیدگی در طول گمانه و حساسیت موقعیت انتهای گمانه به روش محاسبهٔ مسیر.
7. **کنترل مقادیر**: شیوهٔ ثبت مقادیر زیر حد تشخیص در هر بچ، واحد عناصر و مسائل مقادیر.
8. **قواعد و پروفایل**: فعال یا غیرفعال کردن هر قاعده، تغییر شدت (بحرانی، خطا، هشدار، اطلاعات)، ویرایش آستانه‌ها، بارگذاری فهرست کدها (فایل با ستون‌های field و code) و ذخیرهٔ همه در یک پروفایل JSON.
9. **بستهٔ مستندات**: مستندات راستی‌آزمایی داده‌ها بر پایهٔ بندهای JORC، NI 43-101، S-K 1300 و CIM. سه بخش «روش‌ها»، «محدودیت‌ها» و «نظر دربارهٔ کفایت» خالی می‌ماند تا شخص صلاحیت‌دار بنویسد. دکمهٔ «تأیید و اعمال اصلاحات» دسته‌های قابل‌اصلاح (نگاشت شناسهٔ گمانه، آزیموت ۳۶۰، تکراری‌های یکسان) را نشان می‌دهد؛ فقط پس از تأیید، نسخهٔ اصلاح‌شده و گزارش اصلاح (fix_log.csv) در پوشهٔ `corrected` نوشته می‌شود.
10. **مسائل**: فیلتر بر پایهٔ شدت، دسته (A تا J)، قاعده، جدول و گمانه؛ دوبار کلیک روی هر مسئله فایل و شمارهٔ ردیف منبع را نشان می‌دهد؛ خروجی فهرست فیلترشده.
11. **سازگاری جدول‌ها**: کدهای کانه‌دار و بی‌کانهٔ پروژه را از میان کدهای لاگ‌شده انتخاب کنید. برنامه زون‌های کانه‌دار بدون آنالیز، پوشش هر جدول در هر گمانه (نقشهٔ حرارتی)، وارونگی نیمرخ هوازدگی، عیار بالا در واحد بی‌کانه، بازیافت و RQD، و چگالی خارج از بازهٔ هر سنگ را نشان می‌دهد.
12. **آزمایشگاه و QA/QC**: تطبیق پایگاه داده با فایل آزمایشگاه بر پایهٔ شناسهٔ نمونه: نمونهٔ گم‌شده در هر دو سو، مغایرت مقدار (رواداری ½ حد تشخیص یا ۰٫۱ درصد)، خطای واحد یا مقیاس، تفاوت کدگذاری زیر حد تشخیص، جابه‌جایی شناسهٔ نمونه هنگام ادغام، نتایج آنالیز مجدد (همه فهرست می‌شوند و برنامه انتخاب نمی‌کند)، نمونهٔ کنترلی ثبت‌شده به‌صورت بازهٔ درون‌چاهی، و نرخ خطای پروژه با حد بالای ۹۵ درصد. همچنین ماده مرجع با برچسب اشتباه، جابه‌جایی ماده مرجع و بلانک، و اریبی آزمایشگاه داور. **ممیزی تصادفی:** چک‌لیست با انتخاب تصادفی تکرارپذیر (بذر ثابت) خروجی بگیرید، با اسناد اصلی مقایسه کنید و نتیجه را وارد کنید تا در بستهٔ مستندات بیاید.
13. **توپوگرافی و محدوده**: آنچه خوانده شد، و بررسی‌های اولیه پیش از هر مقایسه: نبود هم‌پوشانی (جابه‌جایی شرقی و شمالی، زون UTM دیگر، شرقی کاذب)، نسبت ارتفاع حدود ۳٫۲۸ (فوت در برابر متر) و دهانه‌های خارج از توپوگرافی («بررسی‌نشده»، نه «قبول»). توپوگرافی جغرافیایی (SRTM، KML) خودکار به UTM تبدیل می‌شود. گمانه‌های زیرزمینی یا ترانشه با فیلد انتخابی معاف می‌شوند و می‌توان توپوگرافی را بر پایهٔ تاریخ (پیش از معدن‌کاری / فعلی) برگزید.
14. **نسخه‌ها**: مقایسه با نسخهٔ قبلی: گمانه‌های بدون تغییر با اثرانگشت کنار گذاشته می‌شوند. گونه‌های تغییر عبارت‌اند از گمانهٔ افزوده یا حذف‌شده، جابه‌جایی دهانه، تغییر انحراف‌سنجی (با جابه‌جایی انتهای گمانه)، بازهٔ افزوده یا حذف‌شده، تقسیم‌بندی دوباره، آنالیز مجدد، تغییر کد و تغییر فراداده. تغییر فلز Σ(طول × عیار) برای همهٔ گمانه‌ها و گمانه‌های مشترک محاسبه می‌شود. با «پذیرش این نسخه» تصویر پذیرفته‌شده (نام بازبین، تاریخ، یادداشت، گمانه‌های قفل‌شده) ذخیره می‌شود؛ هر تغییری در گمانهٔ قفل‌شده در اجرای بعدی **بحرانی** گزارش می‌شود.
15. **دادهٔ نمونه**: یک پایگاه دادهٔ مصنوعی پورفیری با ۳۷ خطای عمدی بارگذاری می‌کند. فایل آزمایشگاه و فایل داور هم‌خوان با آن ساخته می‌شود و نسخهٔ بدون خطا به‌عنوان «نسخهٔ قبلی» تنظیم می‌شود. فهرست خطاها در `manifest.csv` است. عیار در این داده تابع سنگ میزبان، دگرسانی و هوازدگی است تا تحلیل‌ها معنادار باشند.

**خروجی‌ها** (در پوشهٔ `GEOVALID_<تاریخ>`؛ داده‌های اصلی هرگز تغییر نمی‌کنند)
- `report_fa.html` و `report_en.html`: گزارش فنی با نمودارها، از جمله بخش «تحلیل عیار بر پایهٔ واحدهای توصیفی».
- `evidence_pack_fa.html`، `evidence_pack_en.html` و `evidence_pack.json`: بستهٔ مستندات راستی‌آزمایی.
- `issues.json` و `hole_hashes.csv`: فهرست مسائل به قالب JSON و اثرانگشت هر گمانه برای مقایسهٔ نسخه‌ها.
- `change_log.csv`، `version_metal.csv` و `version_metal_by_hole.csv`: گزارش تغییرات و تغییر فلز نسبت به نسخهٔ قبلی.
- `lab_reconciliation.csv`: نتیجهٔ تطبیق با فایل آزمایشگاه برای هر ستون.
- `grade_vs_geology.xlsx`: جدول ارتباط (η²، کروسکال–والیس)، آمار عیار هر واحد، دامنه‌های پیشنهادی تخمین، نتیجهٔ تحلیل همبری و میانهٔ عیار سنگ‌شناسی × دگرسانی.
- `issue_log.xlsx` و `issues.csv`: فهرست کامل مسائل، با خلاصه بر پایهٔ قاعده، جدول و گمانه، ماتریس اجرای قواعد، آمار آنالیزها، روش برداشت دهانه و ΔZ.
- `flagged_tables/*.csv`: نسخه‌ای از هر جدول ورودی با ستون‌های `QC_FLAG` (C/E/W/I) و `QC_COMMENT` (شمارهٔ قواعد).
- `desurveyed_traces.csv`: مسیر محاسبه‌شدهٔ گمانه‌ها به روش کمینهٔ انحنا.
- `run_metadata.json` و `profile_used.yaml`: نسخهٔ نرم‌افزار، هش SHA-256 ورودی‌ها و پارامترها، برای ممیزی.

**خط فرمان:** `geovalid-cli.exe run --files collar.csv survey.csv assay.xlsx --dem dem.tif --licence lic.kml --lab lab.csv --umpire ump.csv --crm crm.csv --baseline D:\old_version --snapshot accepted.json --out D:\out --lang both`
گزینه‌های دیگر: `--accept-snapshot out.json --reviewer "نام" --note "یادداشت" --lock all`، `--audit-export checklist.xlsx`، `--audit-results filled.xlsx`، `--topo-format tif`.

**عیار حد** تحلیل‌ها از بخش `analysis_cutoffs` پروفایل خوانده می‌شود (مثلاً Cu ۰٫۲ درصد، Au ۰٫۳ گرم بر تن)؛ برای عناصر دیگر صدک ۷۵ داده به کار می‌رود و در برنامه قابل تغییر است.

**محدودیت‌های نسخهٔ ۰٫۴:**
- ۱۰۹ قاعده اجرا می‌شود (فهرست کامل در `docs/RULE_CATALOGUE.md`).
- فقط مبنای WGS84 برای تبدیل مختصات پشتیبانی می‌شود؛ مبنای دیگر گزارش می‌شود ولی جابه‌جایی مبنا اعمال نمی‌شود. GeoTIFF با فشرده‌سازی JPEG و فرمت‌های اختصاصی (Vulcan `.00t`، Datamine `.dm`) پشتیبانی نمی‌شوند و برنامه همین را اعلام می‌کند.
- پروژه‌های ذخیره‌شده، اجرای بی‌واسط با `--project`، تحلیل تداخل فضایی و گمانه‌های جفت در فاز ۳ می‌آیند.
- روش برداشت دهانه (COL-010) نسخهٔ پیش‌نمایش است.

این نرم‌افزار ابزار پشتیبان تصمیم است. پذیرش نهایی داده‌ها برای گزارش‌دهی عمومی بر عهدهٔ شخص صلاحیت‌دار (CP/QP) است.

## English

**Run:** double-click `GEOVALID.exe`. No installation is needed and the program works fully offline. Keep the `_internal` folder next to the exe.

1. **Add files…** Choose CSV/TXT/XLSX/XLS tables. Table types and column mapping are detected automatically, including Persian headers. Adjust them with **Field mapping…** if needed.
2. **Optional inputs:**
   - Topography, format detected automatically: GeoTIFF, ESRI ASCII (`.asc`), Surfer (`.grd`), BIL/BIP/BSQ/FLT with `.hdr`, SRTM (`.hgt`), XYZ/CSV points, DXF (points, contours, 3DFACE), Surpac (`.str` + `.dtm`), OBJ, STL, PLY, Shapefile and KML/KMZ. Each reader reports what it read (extent, resolution, point count, CRS).
   - Licence boundary: KML/KMZ, Shapefile, GeoJSON, DXF closed polylines, or a CSV/TXT/XLSX vertex list; multipart polygons and holes are handled.
   - CRM certificates with the columns `CRM_ID, ELEMENT, CERTIFIED, SD, UNIT`; certified values are converted by the declared unit, and each conversion is reported.
   - **Laboratory / QA-QC file** in the GEOQAQC format (the same file you prepare for GEOQAQC) and the **umpire laboratory file**.
   - **Previous version (folder)** for version comparison, and an **accepted snapshot** (JSON) to protect locked holes.
   - A YAML or JSON profile, or edit thresholds directly with **Thresholds…**.
3. **Run validation.** The **Dashboard** shows issue counts, charts and key findings; **Issues** is the searchable list with details; **Open report** opens the HTML report.
4. **Survey QA:** downhole dip, azimuth and dogleg severity per hole, and desurvey sensitivity at EOH. **Values:** below-detection coding by batch, analyte units, value issues. **Rules & profiles:** enable rules, change severities and thresholds, load a code dictionary (`field, code` table) and save everything as a JSON profile. **Evidence pack:** data-verification evidence by JORC, NI 43-101, S-K 1300 and CIM clauses, with three empty sections for the Qualified Person; **Approve and apply fixes** writes corrected copies and `fix_log.csv` only for the fix classes you approve. **Issues:** filter by severity, category, rule, table and hole; double-click shows the source file and line; export the filtered view.
5. **Grade analysis & charts:** more than 25 interactive charts (zoom, pan, save as PNG/SVG/PDF). Choose the analyte, logged attribute, hole and cut-off above the chart; the **Interpretation** panel shows statistics and suggested domains. Highlights:
   - η² matrix: how much of the grade variation each logged attribute (lithology, alteration, weathering, intensity, colour, campaign…) explains;
   - grade by unit (log box plots with length-weighted mean and cut-off), median grade for attribute × attribute (e.g. lithology × alteration), Cramér's V;
   - contact analysis (hard or soft boundaries), units with depth, downhole strip log, density and RQD by unit;
   - swath plots, grade × thickness map, grade–length curve;
   - log-probability, inter-element correlation, scatter, collar map, CRM, blank and HARD charts.
6. **Theme** switches between the dark (Obsidian) and light (Ivory) look.
7. **Cross-table:** pick the project's mineralised and barren codes from the codes actually logged. The page shows mineralised zones without assays, table coverage per hole (heat map), weathering inversions, high grade in barren units, recovery and RQD, and density outside the range set for each rock.
8. **Lab & QA/QC:** the database is reconciled with the laboratory file by sample ID: missing samples both ways, value mismatches (tolerance ½ DL or 0.1 %), unit or scale errors, below-detection coding differences, sample-ID offsets from a bad merge, re-assays (all listed; the program never chooses), QC samples stored as downhole intervals, and the project error rate with its 95 % upper bound. Also mislabelled CRMs, CRM/blank swaps and umpire bias. **Random audit:** export a reproducible (seeded) checklist, check it against the source documents and import it back into the evidence pack.
9. **Topography & boundary:** what was read, and sanity checks before any comparison: no overlap (swapped E/N, another UTM zone, false easting), elevation ratio ≈ 3.28 (feet vs metres), collars outside the topography ("not checked", never "passed"). Geographic topography (SRTM, KML) is converted to UTM. Underground or trench holes can be exempted through a chosen field, and the topography can be chosen by date (pre-mining vs current).
10. **Versions:** comparison with the previous version. Unchanged holes are skipped by hash. Change classes are hole added or deleted, collar moved, survey changed (with the end-of-hole shift), interval added or removed, re-segmented, re-assayed, code changed and metadata changed. Metal change Σ(length × grade) is given for all holes and for common holes. **Accept this version** saves a snapshot (reviewer, date, note, locked holes); any later change to a locked hole is reported as **CRITICAL**.
11. **Sample data** loads a synthetic porphyry database with 37 deliberate errors, listed in `manifest.csv`. Matching laboratory and umpire files are generated, and the error-free twin is set as the previous version. Its grades depend on host rock, alteration and weathering, so the analyses have something to find.

**Outputs.** Source files are never modified; every run writes a new `GEOVALID_<timestamp>` folder containing:
- HTML reports (fa/en), including the section "Grade versus logged geology", PASS/FAIL per rule and status by hole;
- Data Verification Evidence Pack (`evidence_pack_<lang>.html`, `evidence_pack.json`), `issues.json`, `hole_hashes.csv`;
- `change_log.csv`, `version_metal.csv`, `version_metal_by_hole.csv` (version comparison) and `lab_reconciliation.csv`;
- `grade_vs_geology.xlsx`: association (η², Kruskal–Wallis), grade statistics per unit, suggested estimation domains, contact analysis and the lithology × alteration median grade;
- an Excel issue log with summary sheets;
- flagged copies of every table (`QC_FLAG`, `QC_COMMENT`);
- desurveyed traces;
- run metadata with SHA-256 hashes of the inputs.

**Command line:** `geovalid-cli.exe run --files ... [--dem dem.tif] [--licence lic.kml] [--crm crm.csv] [--lab lab.csv] [--umpire ump.csv] [--baseline old_folder] [--snapshot accepted.json] --out folder --lang fa|en|both`. Also `--accept-snapshot out.json --reviewer NAME --note TEXT --lock all|none|H1,H2`, `--audit-export checklist.xlsx`, `--audit-results filled.xlsx`, `--topo-format tif`. Exit codes: 0 = clean, 1 = ERROR issues found, 2 = CRITICAL issues found, 3 = the run itself failed.

**Cut-offs** for the analyses come from the profile's `analysis_cutoffs` (e.g. Cu 0.2 %, Au 0.3 g/t); other analytes use the 75th percentile, and the value can be changed in the program.

**v0.4 limits:**
- 109 rules run (see `docs/RULE_CATALOGUE.md`).
- Coordinate conversion supports WGS 84 only; another declared datum is reported, never shifted. JPEG-compressed GeoTIFF and proprietary formats (Vulcan `.00t`, Datamine `.dm`) are not supported, and the program says so.
- Saved projects, headless `--project` runs, spatial clash and twin-hole analysis come in Phase 3.
- Collar-method inference (COL-010) is a preview.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
