# GEOVALID PRO 0.1.0 — راهنمای سریع / Quick start

## فارسی

**اجرا:** فایل `GEOVALID.exe` را دوبار کلیک کنید. نصب لازم نیست و برنامه کاملاً آفلاین کار می‌کند. پوشهٔ `_internal` را کنار فایل exe نگه دارید.

**گام‌ها**
1. **افزودن فایل…**: فایل‌های CSV/TXT/XLSX/XLS پایگاه داده را انتخاب کنید (دهانه، انحراف‌سنجی، آنالیز، سنگ‌شناسی، ژئوتکنیک، چگالی…). نوع هر جدول و نگاشت ستون‌ها، حتی با سرستون فارسی، خودکار تشخیص داده می‌شود. با «نگاشت فیلدها…» می‌توانید آن را اصلاح کنید.
2. **ورودی‌های اختیاری:**
   - مدل رقومی ارتفاع: شبکهٔ ESRI ASCII با پسوند `.asc`، یا فایل نقطه‌ای `.xyz/.csv` با ستون‌های x، y، z.
   - محدودهٔ پروانه: فهرست رئوس x، y.
   - جدول مواد مرجع با ستون‌های `crm_id, analyte, certified, sd`.
   - پروفایل YAML.
3. **اجرای اعتبارسنجی**: نتایج در زبانه‌های «خلاصه» و «مسائل» نمایش داده می‌شود. «باز کردن گزارش» گزارش HTML را باز می‌کند.
4. **دادهٔ نمونه**: یک پایگاه دادهٔ مصنوعی با ۳۷ خطای عمدی بارگذاری می‌کند. فهرست این خطاها در `manifest.csv` آمده است.

**خروجی‌ها** (در پوشهٔ `GEOVALID_<تاریخ>`؛ داده‌های اصلی هرگز تغییر نمی‌کنند)
- `report_fa.html` و `report_en.html`: گزارش فنی با نمودارها.
- `issue_log.xlsx` و `issues.csv`: فهرست کامل مسائل، با خلاصه بر پایهٔ قاعده، جدول و گمانه، ماتریس اجرای قواعد، آمار آنالیزها، روش برداشت دهانه و ΔZ.
- `flagged_tables/*.csv`: نسخه‌ای از هر جدول ورودی با ستون‌های `QC_FLAG` (C/E/W/I) و `QC_COMMENT` (شمارهٔ قواعد).
- `desurveyed_traces.csv`: مسیر محاسبه‌شدهٔ گمانه‌ها به روش کمینهٔ انحنا.
- `run_metadata.json` و `profile_used.yaml`: نسخهٔ نرم‌افزار، هش SHA-256 ورودی‌ها و پارامترها، برای ممیزی.

**خط فرمان:** `geovalid-cli.exe run --files collar.csv survey.csv assay.xlsx --dem dem.asc --out D:\out --lang both`

**محدودیت‌های نسخهٔ ۰٫۱:**
- ۷۴ قاعده از ۲۲۹ قاعدهٔ فهرست مصوب اجرا می‌شود.
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
3. **Run validation.** Review the results in the **Summary** and **Issues** tabs; **Open report** opens the HTML report.
4. **Sample data** loads a synthetic database with 37 deliberate errors, listed in `manifest.csv`.

**Outputs.** Source files are never modified; every run writes a new `GEOVALID_<timestamp>` folder containing:
- HTML reports (fa/en);
- an Excel issue log with summary sheets;
- flagged copies of every table (`QC_FLAG`, `QC_COMMENT`);
- desurveyed traces;
- run metadata with SHA-256 hashes of the inputs.

**Command line:** `geovalid-cli.exe run --files ... --out folder --lang fa|en|both`. Exit codes: 0 = clean, 1 = ERROR issues found, 2 = CRITICAL issues found, 3 = the run itself failed.

**v0.1 limits:**
- 74 of the 229 catalogue rules are implemented.
- Proprietary formats and GeoTIFF are not supported; use CSV or `.asc` exports.
- The confidence index, DOCX/PDF reports and map/section viewer come in later phases.
- Collar-method inference (COL-010) is a preview.

This is a decision-support tool. Final acceptance of data for public reporting rests with the Competent/Qualified Person.
