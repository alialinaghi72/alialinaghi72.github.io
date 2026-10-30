# GEOVALID PRO 0.2.0 — راهنمای سریع / Quick start

## فارسی

**اجرا:** فایل `GEOVALID.exe` را دوبار کلیک کنید. نصب لازم نیست و برنامه کاملاً آفلاین کار می‌کند. پوشهٔ `_internal` را کنار فایل exe نگه دارید.

**گام‌ها**
1. **افزودن فایل…**: فایل‌های CSV/TXT/XLSX/XLS پایگاه داده را انتخاب کنید (دهانه، انحراف‌سنجی، آنالیز، سنگ‌شناسی، ژئوتکنیک، چگالی…). نوع هر جدول و نگاشت ستون‌ها، حتی با سرستون فارسی، خودکار تشخیص داده می‌شود. با «نگاشت فیلدها…» می‌توانید آن را اصلاح کنید.
2. **ورودی‌های اختیاری:**
   - مدل رقومی ارتفاع: شبکهٔ ESRI ASCII با پسوند `.asc`، یا فایل نقطه‌ای `.xyz/.csv` با ستون‌های x، y، z.
   - محدودهٔ پروانه: فهرست رئوس x، y.
   - جدول مواد مرجع با ستون‌های `crm_id, analyte, certified, sd`.
   - پروفایل YAML.
3. **اجرای اعتبارسنجی**: پس از اجرا، «داشبورد» شمار مسائل، نمودارها و مهم‌ترین یافته‌ها را نشان می‌دهد. «مسائل» فهرست قابل جستجو و جزئیات هر مسئله است. «باز کردن گزارش» گزارش HTML را باز می‌کند.
4. **تحلیل عیار و نمودارها**: بیش از ۲۵ نمودار تعاملی (بزرگ‌نمایی، جابه‌جایی، ذخیره به PNG/SVG/PDF). عنصر، ویژگی توصیفی، گمانه و عیار حد را از بالای نمودار انتخاب کنید؛ پنل «تفسیر» آمار و دامنه‌های پیشنهادی را نشان می‌دهد. مهم‌ترین نمودارها:
   - ماتریس η²: هر ویژگی توصیفی (سنگ‌شناسی، دگرسانی، هوازدگی، شدت دگرسانی، رنگ، فاز حفاری…) چه سهمی از تغییرات عیار را توضیح می‌دهد؛
   - عیار به تفکیک واحد (جعبه‌ای لگاریتمی با میانگین وزنی طولی و عیار حد)، میانهٔ عیار در ترکیب دو ویژگی (مثلاً سنگ‌شناسی × دگرسانی)، V کرامر؛
   - تحلیل همبری (مرز سخت یا نرم)، ترکیب واحدها با عمق، لاگ ستونی گمانه، چگالی و RQD به تفکیک واحد؛
   - نمودارهای نواری (Swath)، نقشهٔ عیار × ضخامت، منحنی عیار–متراژ؛
   - احتمال لگاریتمی، همبستگی عناصر، نمودار پراکنش، نقشهٔ دهانه‌ها، کنترل CRM، بلانک و HARD.
5. **پوسته**: دکمهٔ «پوسته» بین نمای تیره (Obsidian) و روشن (Ivory) جابه‌جا می‌کند.
6. **دادهٔ نمونه**: یک پایگاه دادهٔ مصنوعی پورفیری با ۳۷ خطای عمدی بارگذاری می‌کند. فهرست خطاها در `manifest.csv` است. عیار در این داده تابع سنگ میزبان، دگرسانی و هوازدگی است تا تحلیل‌ها معنادار باشند.

**خروجی‌ها** (در پوشهٔ `GEOVALID_<تاریخ>`؛ داده‌های اصلی هرگز تغییر نمی‌کنند)
- `report_fa.html` و `report_en.html`: گزارش فنی با نمودارها، از جمله بخش «تحلیل عیار بر پایهٔ واحدهای توصیفی».
- `grade_vs_geology.xlsx`: جدول ارتباط (η²، کروسکال–والیس)، آمار عیار هر واحد، دامنه‌های پیشنهادی تخمین، نتیجهٔ تحلیل همبری و میانهٔ عیار سنگ‌شناسی × دگرسانی.
- `issue_log.xlsx` و `issues.csv`: فهرست کامل مسائل، با خلاصه بر پایهٔ قاعده، جدول و گمانه، ماتریس اجرای قواعد، آمار آنالیزها، روش برداشت دهانه و ΔZ.
- `flagged_tables/*.csv`: نسخه‌ای از هر جدول ورودی با ستون‌های `QC_FLAG` (C/E/W/I) و `QC_COMMENT` (شمارهٔ قواعد).
- `desurveyed_traces.csv`: مسیر محاسبه‌شدهٔ گمانه‌ها به روش کمینهٔ انحنا.
- `run_metadata.json` و `profile_used.yaml`: نسخهٔ نرم‌افزار، هش SHA-256 ورودی‌ها و پارامترها، برای ممیزی.

**خط فرمان:** `geovalid-cli.exe run --files collar.csv survey.csv assay.xlsx --dem dem.asc --out D:\out --lang both`

**عیار حد** تحلیل‌ها از بخش `analysis_cutoffs` پروفایل خوانده می‌شود (مثلاً Cu ۰٫۲ درصد، Au ۰٫۳ گرم بر تن)؛ برای عناصر دیگر صدک ۷۵ داده به کار می‌رود و در برنامه قابل تغییر است.

**محدودیت‌های نسخهٔ ۰٫۲:**
- ۷۶ قاعده از ۲۲۹ قاعدهٔ فهرست مصوب اجرا می‌شود (افزوده‌های این نسخه: CRS-004 پیشنهاد دامنه‌ها و CRS-005 تحلیل همبری).
- فرمت‌های اختصاصی (Datamine `.dm`، Micromine `.DAT`، MS Access) و GeoTIFF پشتیبانی نمی‌شوند؛ خروجی CSV یا `.asc` آن‌ها را بدهید.
- شاخص اطمینان داده، گزارش DOCX/PDF و نمایشگر نقشه و مقطع در فازهای بعدی می‌آیند.
- روش برداشت دهانه (COL-010) نسخهٔ پیش‌نمایش است.

این نرم‌افزار ابزار پشتیبان تصمیم است. پذیرش نهایی داده‌ها برای گزارش‌دهی عمومی بر عهدهٔ شخص صلاحیت‌دار (CP/QP) است.

## English

**Run:** double-click `GEOVALID.exe`. No installation is needed and the program works fully offline. Keep the `_internal` folder next to the exe.

1. **Add files…** Choose CSV/TXT/XLSX/XLS tables. Table types and column mapping are detected automatically, including Persian headers. Adjust them with **Field mapping…** if needed.
2. **Optional inputs:**
   - DEM: an ESRI ASCII grid (`.asc`) or an `.xyz/.csv` point file with x, y, z columns.
   - Licence polygon: an x, y vertex list.
   - CRM table with the columns `crm_id, analyte, certified, sd`.
   - A YAML profile, or edit thresholds directly with **Thresholds…**.
3. **Run validation.** The **Dashboard** shows issue counts, charts and key findings; **Issues** is the searchable list with details; **Open report** opens the HTML report.
4. **Grade analysis & charts:** more than 25 interactive charts (zoom, pan, save as PNG/SVG/PDF). Choose the analyte, logged attribute, hole and cut-off above the chart; the **Interpretation** panel shows statistics and suggested domains. Highlights:
   - η² matrix: how much of the grade variation each logged attribute (lithology, alteration, weathering, intensity, colour, campaign…) explains;
   - grade by unit (log box plots with length-weighted mean and cut-off), median grade for attribute × attribute (e.g. lithology × alteration), Cramér's V;
   - contact analysis (hard or soft boundaries), units with depth, downhole strip log, density and RQD by unit;
   - swath plots, grade × thickness map, grade–length curve;
   - log-probability, inter-element correlation, scatter, collar map, CRM, blank and HARD charts.
5. **Theme** switches between the dark (Obsidian) and light (Ivory) look.
6. **Sample data** loads a synthetic porphyry database with 37 deliberate errors, listed in `manifest.csv`. Its grades depend on host rock, alteration and weathering, so the analyses have something to find.

**Outputs.** Source files are never modified; every run writes a new `GEOVALID_<timestamp>` folder containing:
- HTML reports (fa/en), including the section "Grade versus logged geology";
- `grade_vs_geology.xlsx`: association (η², Kruskal–Wallis), grade statistics per unit, suggested estimation domains, contact analysis and the lithology × alteration median grade;
- an Excel issue log with summary sheets;
- flagged copies of every table (`QC_FLAG`, `QC_COMMENT`);
- desurveyed traces;
- run metadata with SHA-256 hashes of the inputs.

**Command line:** `geovalid-cli.exe run --files ... --out folder --lang fa|en|both`. Exit codes: 0 = clean, 1 = ERROR issues found, 2 = CRITICAL issues found, 3 = the run itself failed.

**Cut-offs** for the analyses come from the profile's `analysis_cutoffs` (e.g. Cu 0.2 %, Au 0.3 g/t); other analytes use the 75th percentile, and the value can be changed in the program.

**v0.2 limits:**
- 76 of the 229 catalogue rules are implemented (new in this version: CRS-004 domain suggestions and CRS-005 contact analysis).
- Proprietary formats and GeoTIFF are not supported; use CSV or `.asc` exports.
- The confidence index, DOCX/PDF reports and map/section viewer come in later phases.
- Collar-method inference (COL-010) is a preview.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
