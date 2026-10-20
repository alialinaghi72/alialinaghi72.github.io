# متن صفحه‌های ابزار (رابط کاربری در tools_ui.py و منطق در assets/tools.js)
TOOLS = [
{
 'slug': 'cut-off-grade', 'icon': 'calc',
 'fa': {
  'short': 'ماشین‌حساب عیار حد', 'h1': 'ماشین‌حساب عیار حد',
  'title': 'ماشین‌حساب آنلاین عیار حد (Cut-off Grade) برای مس، طلا، روی و سرب | علی علینقی',
  'desc': 'محاسبهٔ آنلاین عیار حد سربه‌سر و حاشیه‌ای برای مس، طلا، نقره، روی، سرب و مولیبدن با قیمت، بازیابی، درصد قابل پرداخت و هزینه‌ها؛ همراه با نمودار حساسیت به قیمت.',
  'lede': 'قیمت فلز، بازیابی و هزینه‌های هر تن کانسنگ را وارد کنید تا عیار حد سربه‌سر و حاشیه‌ای و حساسیت آن به قیمت را ببینید. محاسبه در مرورگر شما انجام می‌شود.',
  'card': 'عیار حد سربه‌سر و حاشیه‌ای با نمودار حساسیت به قیمت فلز.',
  'sections': [
   ('این ماشین‌حساب چه چیزی را محاسبه می‌کند؟', '''<p>ماشین‌حساب دو عدد را محاسبه می‌کند. <b>عیار حد سربه‌سر</b> همهٔ هزینه‌های هر تن کانسنگ، شامل استخراج، فرآوری و هزینه‌های عمومی و اداری، را در بر می‌گیرد. <b>عیار حد حاشیه‌ای</b> هزینهٔ استخراج را کنار می‌گذارد و برای موادی کاربرد دارد که به‌هرحال باید استخراج شوند، مانند مواد درون پیت که برای رسیدن به کانسنگ برداشته می‌شوند.</p>
<p class="eq" dir="ltr">Cut-off = Costs ($/t ore) / [ (Price − Selling cost) × Recovery × Payable ]</p>
<p>برای توضیح کامل فرمول و مثال‌های عددی، مقالهٔ <a href="/articles/cut-off-grade/">عیار حد چیست</a> را بخوانید.</p>'''),
   ('راهنمای ورودی‌ها', '''<ul>
<li><b>قیمت:</b> برای ارزیابی پروژه از قیمت بلندمدت و محتاطانه استفاده کنید، نه قیمت لحظه‌ای. واحد قیمت را می‌توانید دلار بر تن، دلار بر پوند یا دلار بر اونس انتخاب کنید.</li>
<li><b>هزینهٔ فروش:</b> هزینه‌های ذوب و پالایش (TC/RC)، حمل و بیمه، بر حسب همان واحد قیمت.</li>
<li><b>بازیابی:</b> درصدی از فلز خوراک که در فرآوری به محصول می‌رسد؛ بهتر است از نتایج آزمایش‌های متالورژیکی همان کانسار گرفته شود.</li>
<li><b>درصد قابل پرداخت:</b> سهمی از فلز موجود در محصول که خریدار بابت آن پرداخت می‌کند.</li>
<li><b>هزینه‌ها:</b> هزینهٔ استخراج، فرآوری و هزینه‌های عمومی و اداری بر حسب دلار بر تن کانسنگ.</li>
</ul>
<p>مقادیر پیش‌فرض هر فلز صرفاً نمایشی‌اند و جای اعداد پروژهٔ شما را نمی‌گیرند.</p>'''),
   ('محدودیت‌ها', '''<p>این محاسبه ساده‌سازی شده است: رقیق‌شدگی و بازیابی استخراج، محدودیت ظرفیت معدن و کارخانه، هزینه‌های سرمایه‌ای و ارزش زمانی پول را در بر نمی‌گیرد. برای کانسارهای چندفلزی باید از ارزش خالص ذوب (NSR) یا عیار معادل با بازیابی هر فلز استفاده کرد. برای تصمیم‌های سرمایه‌گذاری، عیار حد باید در چارچوب برنامه‌ریزی معدن و تحلیل اقتصادی کامل تعیین شود.</p>'''),
  ],
  'faq': [
   ('چرا عیار حد حاشیه‌ای از عیار حد سربه‌سر کمتر است؟', 'چون هزینهٔ استخراج را در بر نمی‌گیرد. موادی که به‌هرحال باید استخراج شوند، اگر عیارشان بیشتر از عیار حد حاشیه‌ای باشد، فرستادن آن‌ها به کارخانه به‌جای دامپ سودآور است.'),
   ('قیمت را بر حسب چه واحدی وارد کنم؟', 'هر واحدی که در دسترس دارید: دلار بر تن یا دلار بر پوند برای فلزات پایه و دلار بر اونس تروی برای طلا و نقره. ماشین‌حساب تبدیل واحد را خودش انجام می‌دهد؛ فقط هزینهٔ فروش را با همان واحد قیمت وارد کنید.'),
  ],
  'related': {'art': ['cut-off-grade', 'resources-vs-reserves'], 'tools': ['grade-converter'], 'svc': ['resource-estimation']},
 },
 'en': {
  'short': 'Cut-off grade calculator', 'h1': 'Cut-off grade calculator',
  'title': 'Free Cut-off Grade Calculator for Copper, Gold, Zinc and Lead | Ali Alinaghi',
  'desc': 'Calculate break-even and marginal cut-off grades online for copper, gold, silver, zinc, lead and molybdenum from price, recovery, payability and costs, with a price-sensitivity chart.',
  'lede': 'Enter the metal price, recovery and costs per tonne of ore to see the break-even and marginal cut-off grades and how they respond to price. Everything is calculated in your browser.',
  'card': 'Break-even and marginal cut-off grades with a price-sensitivity chart.',
  'sections': [
   ('What this calculator computes', '''<p>The calculator returns two numbers. The <b>break-even cut-off</b> includes every cost per tonne of ore — mining, processing and G&amp;A. The <b>marginal cut-off</b> excludes mining cost and applies to material that has to be mined anyway, such as in-pit material removed to reach ore.</p>
<p class="eq" dir="ltr">Cut-off = Costs ($/t ore) / [ (Price − Selling cost) × Recovery × Payable ]</p>
<p>For the full explanation and worked examples, read <a href="/en/articles/cut-off-grade/">what is cut-off grade</a>.</p>'''),
   ('Input guide', '''<ul>
<li><b>Price:</b> use a conservative long-term price for project evaluation, not the spot price. You can enter it per tonne, per pound or per troy ounce.</li>
<li><b>Selling cost:</b> treatment and refining charges (TC/RC), freight and insurance, in the same unit as the price.</li>
<li><b>Recovery:</b> the share of metal in the feed that reaches the product; ideally from metallurgical test work on the deposit itself.</li>
<li><b>Payable:</b> the share of contained metal in the product that the buyer pays for.</li>
<li><b>Costs:</b> mining, processing and G&amp;A in dollars per tonne of ore.</li>
</ul>
<p>The default values for each metal are illustrative only and are no substitute for your project numbers.</p>'''),
   ('Limitations', '''<p>This is a simplified calculation: it excludes dilution and mining recovery, mine and plant capacity constraints, capital costs and the time value of money. Polymetallic deposits need net smelter return (NSR) or metal equivalents with each metal's recovery. For investment decisions, cut-off grade should be set within full mine planning and economic analysis.</p>'''),
  ],
  'faq': [
   ('Why is the marginal cut-off lower than the break-even cut-off?', 'Because it excludes mining cost. Material that must be mined anyway is worth sending to the mill instead of the dump if its grade is above the marginal cut-off.'),
   ('Which price unit should I use?', 'Whichever you have: dollars per tonne or per pound for base metals, dollars per troy ounce for gold and silver. The calculator converts units itself; just enter the selling cost in the same unit as the price.'),
  ],
  'related': {'art': ['cut-off-grade', 'resources-vs-reserves'], 'tools': ['grade-converter'], 'svc': ['resource-estimation']},
 },
},
{
 'slug': 'grade-converter', 'icon': 'grid',
 'fa': {
  'short': 'تبدیل واحد و فلز محتوا', 'h1': 'تبدیل واحد عیار و محاسبهٔ فلز محتوا',
  'title': 'تبدیل واحد عیار (درصد، ppm، گرم در تن، اونس) و محاسبهٔ تناژ و فلز محتوا | علی علینقی',
  'desc': 'تبدیل آنلاین واحدهای عیار میان درصد، ppm، ppb، گرم در تن و اونس بر تن، و محاسبهٔ تناژ از حجم و چگالی و فلز محتوا بر حسب تن، کیلوگرم، اونس و پوند.',
  'lede': 'عیار را میان درصد، ppm، ppb، گرم در تن و اونس بر تن تبدیل کنید و از روی حجم، چگالی و عیار، تناژ و مقدار فلز محتوا را به دست آورید.',
  'card': 'تبدیل درصد، ppm، گرم در تن و اونس؛ محاسبهٔ تناژ و فلز محتوا.',
  'sections': [
   ('تبدیل واحدهای عیار', '''<p>عیار فلزات پایه معمولاً بر حسب درصد و عیار فلزات گران‌بها بر حسب گرم در تن یا اونس بر تن بیان می‌شود. روابط اصلی:</p>
<div class="tbl-scroll"><table class="dtable"><thead><tr><th>واحد</th><th>معادل</th></tr></thead><tbody>
<tr><td>۱ درصد</td><td>۱۰٬۰۰۰ ppm = ۱۰٬۰۰۰ گرم در تن</td></tr>
<tr><td>۱ ppm</td><td>۱ گرم در تن = ۱٬۰۰۰ ppb</td></tr>
<tr><td>۱ اونس تروی بر تن کوتاه (oz/st)</td><td>≈ ۳۴٫۲۸۶ گرم در تن</td></tr>
<tr><td>۱ اونس تروی</td><td>۳۱٫۱۰۳۵ گرم</td></tr>
<tr><td>۱ تن متریک</td><td>۲٬۲۰۴٫۶۲ پوند</td></tr>
</tbody></table></div>'''),
   ('محاسبهٔ تناژ و فلز محتوا', '''<p class="eq" dir="ltr">Tonnage (t) = Volume (m³) × Bulk density (t/m³)<br>Contained metal = Tonnage × Grade</p>
<p>برای عیار درصدی، فلز محتوا بر حسب تن برابر تناژ ضرب در عیار تقسیم بر ۱۰۰ است؛ برای عیار گرم در تن، حاصل‌ضرب تناژ و عیار، فلز محتوا را بر حسب گرم می‌دهد. فلز محتوا مقدار برجاست و بازیابی استخراج و فرآوری در آن لحاظ نشده است.</p>'''),
   ('اهمیت چگالی', '''<p>خطا در چگالی مستقیماً به خطا در تناژ و فلز محتوا تبدیل می‌شود. چگالی باید با اندازه‌گیری‌های کافی و نماینده برای هر دامنه و نوع سنگ تعیین شود، به‌ویژه در کانسارهای آهن که چگالی با عیار تغییر می‌کند، و در پهنه‌های اکسیدی که تخلخل بیشتری دارند.</p>'''),
  ],
  'faq': [
   ('یک درصد چند گرم در تن است؟', 'یک درصد برابر ۱۰٬۰۰۰ گرم در تن یا ۱۰٬۰۰۰ ppm است.'),
   ('اونس بر تن را چطور به گرم در تن تبدیل کنم؟', 'یک اونس تروی بر تن کوتاه آمریکایی حدود ۳۴٫۲۸۶ گرم در تن و یک اونس تروی بر تن متریک حدود ۳۱٫۱۰۳ گرم در تن است.'),
  ],
  'related': {'art': ['qaqc', 'cut-off-grade'], 'tools': ['cut-off-grade'], 'svc': ['resource-estimation']},
 },
 'en': {
  'short': 'Unit converter and contained metal', 'h1': 'Grade unit converter and contained-metal calculator',
  'title': 'Grade Unit Converter (%, ppm, g/t, oz/t) and Contained-Metal Calculator | Ali Alinaghi',
  'desc': 'Convert grade units between percent, ppm, ppb, grams per tonne and ounces per ton online, and calculate tonnage from volume and density and contained metal in tonnes, kilograms, ounces and pounds.',
  'lede': 'Convert grades between percent, ppm, ppb, g/t and oz/t, and work out tonnage and contained metal from volume, density and grade.',
  'card': 'Convert %, ppm, g/t and oz/t; calculate tonnage and contained metal.',
  'sections': [
   ('Grade unit conversions', '''<p>Base-metal grades are usually given in percent and precious-metal grades in grams per tonne or ounces per ton. The key relationships:</p>
<div class="tbl-scroll"><table class="dtable"><thead><tr><th>Unit</th><th>Equivalent</th></tr></thead><tbody>
<tr><td>1 %</td><td>10,000 ppm = 10,000 g/t</td></tr>
<tr><td>1 ppm</td><td>1 g/t = 1,000 ppb</td></tr>
<tr><td>1 troy oz per short ton (oz/st)</td><td>≈ 34.286 g/t</td></tr>
<tr><td>1 troy ounce</td><td>31.1035 g</td></tr>
<tr><td>1 metric tonne</td><td>2,204.62 lb</td></tr>
</tbody></table></div>'''),
   ('Tonnage and contained metal', '''<p class="eq" dir="ltr">Tonnage (t) = Volume (m³) × Bulk density (t/m³)<br>Contained metal = Tonnage × Grade</p>
<p>For a percent grade, contained metal in tonnes is tonnage times grade divided by 100; for a g/t grade, tonnage times grade gives contained metal in grams. Contained metal is an in-situ quantity and excludes mining and processing recovery.</p>'''),
   ('Why density matters', '''<p>An error in density becomes an error in tonnage and contained metal directly. Density should be set from enough representative measurements for each domain and rock type — especially in iron deposits, where density changes with grade, and in more porous oxide zones.</p>'''),
  ],
  'faq': [
   ('How many grams per tonne is one percent?', 'One percent equals 10,000 g/t, or 10,000 ppm.'),
   ('How do I convert ounces per ton to grams per tonne?', 'One troy ounce per US short ton is about 34.286 g/t, and one troy ounce per metric tonne is about 31.103 g/t.'),
  ],
  'related': {'art': ['qaqc', 'cut-off-grade'], 'tools': ['cut-off-grade'], 'svc': ['resource-estimation']},
 },
},
{
 'slug': 'variogram-lab', 'icon': 'chart',
 'fa': {
  'short': 'آزمایشگاه واریوگرام', 'h1': 'آزمایشگاه تعاملی واریوگرام',
  'title': 'آزمایشگاه تعاملی واریوگرام: برازش مدل کروی، نمایی و گاوسی | علی علینقی',
  'desc': 'ابزار آنلاین و تعاملی برای یادگیری واریوگرافی: اثر قطعه‌ای، سقف و دامنه را تغییر دهید، مدل کروی، نمایی یا گاوسی را روی واریوگرام تجربی برازش دهید و خطای برازش را ببینید.',
  'lede': 'اثر قطعه‌ای، سقف و دامنه را تغییر دهید و ببینید مدل واریوگرام چطور روی داده‌های تجربی سه نوع کانسار می‌نشیند. یک دکمه هم برای برازش خودکار هست؛ اما اول خودتان امتحان کنید.',
  'card': 'برازش مدل کروی، نمایی یا گاوسی روی واریوگرام تجربی، به‌صورت تعاملی.',
  'sections': [
   ('چطور از آزمایشگاه استفاده کنیم؟', '''<ol class="steps">
<li>یک مجموعه‌داده انتخاب کنید: طلای رگه‌ای با اثر قطعه‌ای بالا، مس پورفیری با پیوستگی خوب یا آهن با پیوستگی بسیار زیاد.</li>
<li>نوع مدل را انتخاب کنید و با لغزنده‌ها اثر قطعه‌ای، سقف جزئی و دامنه را تغییر دهید.</li>
<li>خطای برازش را ببینید؛ این خطا با تعداد جفت هر گام وزن‌دهی شده است، چون گام‌های پرجفت قابل اتکاترند.</li>
<li>نتیجه را با دکمهٔ «برازش خودکار» مقایسه کنید.</li>
</ol>'''),
   ('مجموعه‌داده‌های نمونه', '''<p>داده‌ها مصنوعی‌اند اما رفتار واقعی سه تیپ کانسار را نشان می‌دهند: در طلای رگه‌ای بخش بزرگی از واریانس در اثر قطعه‌ای است و دامنه کوتاه است؛ در مس پورفیری اثر قطعه‌ای کم و دامنه بلند است؛ و در کانسارهای آهن پیوستگی عیار در فاصله‌های بسیار بیشتر حفظ می‌شود.</p>'''),
   ('برازش در عمل', '''<p>در پروژهٔ واقعی، برازش «خودکار» فقط نقطهٔ شروع است. اثر قطعه‌ای را بهتر است از واریوگرام درون‌گمانه‌ای گرفت، جهت‌ها باید با زمین‌شناسی سازگار باشند، و اغلب دو یا سه ساختار تودرتو لازم است. برای جزئیات بیشتر، مقالهٔ <a href="/articles/variogram/">واریوگرام چیست</a> را بخوانید.</p>'''),
  ],
  'faq': [
   ('خطای برازش چطور محاسبه می‌شود؟', 'ریشهٔ میانگین مربع اختلاف واریوگرام تجربی و مدل در هر گام، با وزن تعداد جفت‌های همان گام.'),
   ('کدام مدل بهتر است؟', 'مدلی که هم خطای کمتری دارد و هم با رفتار زمین‌شناسی سازگار است. مدل کروی برای عیار رایج‌ترین انتخاب است و مدل گاوسی برای عیار به‌ندرت مناسب است.'),
  ],
  'related': {'art': ['variogram', 'kriging'], 'tools': ['cut-off-grade'], 'svc': ['resource-estimation']},
 },
 'en': {
  'short': 'Variogram lab', 'h1': 'Interactive variogram lab',
  'title': 'Interactive Variogram Lab: Fit Spherical, Exponential and Gaussian Models | Ali Alinaghi',
  'desc': 'A free interactive tool for learning variography: change the nugget, sill and range, fit a spherical, exponential or Gaussian model to an experimental variogram and see the fit error.',
  'lede': 'Change the nugget, sill and range and watch how a variogram model fits the experimental data of three deposit types. There is an auto-fit button too — but try it yourself first.',
  'card': 'Fit spherical, exponential or Gaussian models to an experimental variogram, interactively.',
  'sections': [
   ('How to use the lab', '''<ol class="steps">
<li>Pick a dataset: high-nugget vein gold, well-structured porphyry copper, or highly continuous iron.</li>
<li>Choose a model type and move the sliders for nugget, partial sill and range.</li>
<li>Watch the fit error; it is weighted by the number of pairs in each lag, because well-populated lags are more reliable.</li>
<li>Compare your result with the auto-fit button.</li>
</ol>'''),
   ('The sample datasets', '''<p>The data are synthetic but mimic three deposit types: in vein gold much of the variance sits in the nugget and the range is short; in porphyry copper the nugget is small and the range long; in iron deposits grade continuity holds over far greater distances.</p>'''),
   ('Fitting in practice', '''<p>On a real project, automatic fitting is only a starting point. Take the nugget from a downhole variogram, keep directions consistent with the geology, and expect to need two or three nested structures. For more detail, read <a href="/en/articles/variogram/">the variogram explained</a>.</p>'''),
  ],
  'faq': [
   ('How is the fit error calculated?', 'As the root of the mean squared difference between the experimental variogram and the model at each lag, weighted by the number of pairs in that lag.'),
   ('Which model is best?', 'The one that fits well and is consistent with the geology. The spherical model is the most common choice for grade; the Gaussian model is rarely appropriate for grade.'),
  ],
  'related': {'art': ['variogram', 'kriging'], 'tools': ['cut-off-grade'], 'svc': ['resource-estimation']},
 },
},
]
