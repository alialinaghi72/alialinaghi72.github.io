# اطلس کانسارهای ایران.
# هر عدد منبع دارد: [[کلید]] در متن به شمارهٔ منبع در فهرست منابع همان صفحه تبدیل می‌شود (کلیدها در SRC).
# اطمینان ارقام: H بالا، MH متوسط تا بالا، M متوسط، ML کم تا متوسط، L کم.
# مختصات تأییدنشده (مهدی‌آباد، موته) عمداً None است و منتشر نمی‌شود.
# ارقام «منتشر نشود» (از جمله ۷٫۷ میلیارد تن خوشهٔ سرچشمه، ۱٫۷۷ میلیارد تن میدوک، عیار گوگرد و فسفر گل‌گهر،
# عیار طلای USGS برای مسجد داغی و خبر واگذاری زرشوران) عمداً در این فایل نیامده‌اند.
from urllib.parse import quote

P = '2026-10-19'

def A(u, t): return f'<a href="{u}" target="_blank" rel="noopener">{t}</a>'
def DOI(d): return A('https://doi.org/' + d, 'doi:' + d)
def USGS(i, name): return f'USGS Mineral Resources Data System, porphyry copper deposits of the Tethys region (SIR 2010-5090), record {i}: {name}. ' + A(f'https://mrdata.usgs.gov/sir20105090z/show-sir20105090z.php?id={i}', 'mrdata.usgs.gov')
def MINDAT(page, name): return f'Mindat.org, {page} ({name}). ' + A(f'https://www.mindat.org/{page}.html', 'mindat.org')
def PG(i, name): return f'PorterGeo Database, {name} ({i}). ' + A(f'https://portergeo.com.au/database/mineinfo.php?mineid={i}', 'portergeo.com.au')
def WP(slug, name): return f'Wikipedia: {name}. ' + A(f'https://en.wikipedia.org/wiki/{slug}', 'en.wikipedia.org')
def MYB(y, path, note=''): return f'USGS ({y}). <i>Minerals Yearbook — The Mineral Industry of Iran</i>{note}. ' + A(f'https://pubs.usgs.gov/myb/vol3/{path}', 'pubs.usgs.gov')
def SD(pii): return A(f'https://www.sciencedirect.com/science/article/abs/pii/{pii}', 'sciencedirect.com')
def ECONG(art, note): return f'<i>Journal of Economic Geology</i> (Iran), article {art} ({note}). ' + A(f'https://econg.um.ac.ir/article_{art}_en.html', 'econg.um.ac.ir')

SRC = {
 # ---------- منطقه‌ای ----------
 'aghazadeh2015': 'Aghazadeh, M., Hou, Z., Badrzadeh, Z. &amp; Zhou, L. (2015). Temporal–spatial distribution and tectonic setting of porphyry copper deposits in Iran: constraints from zircon U–Pb and molybdenite Re–Os geochronology. <i>Ore Geology Reviews</i>, 70, 385–406. ' + DOI('10.1016/j.oregeorev.2015.03.003'),
 'caltech_kerman': 'Geochronology of the Kerman porphyry copper belt, CaltechAUTHORS record 20170726-151335659. ' + A('https://resolver.caltech.edu/CaltechAUTHORS:20170726-151335659', 'resolver.caltech.edu'),
 'nicico': 'National Iranian Copper Industries Co. (NICICO), company profile (in Persian). ' + A('https://www.nicico.com/' + quote('معرفی-شرکت'), 'nicico.com'),
 # ---------- سرچشمه ----------
 'usgs9329': USGS(9329, 'Sar Cheshmeh'),
 'mindat21589': MINDAT('loc-21589', 'Sarcheshmeh'),
 'porter985': PG('mn985', 'Sar Cheshmeh'),
 'waterman1975': 'Waterman, G.C. &amp; Hamilton, R.L. (1975). The Sar Cheshmeh porphyry copper deposit. <i>Economic Geology</i>, 70(3), 568–576. ' + DOI('10.2113/gsecongeo.70.3.568'),
 'magiran2016': 'Persian-language paper on zircon U–Pb ages of the Sarcheshmeh intrusions (2016). ' + A('https://magiran.com/paper/1477403/?lang=en', 'magiran.com'),
 'hassanpour_durham': 'Hassanpour, Sh. et al., output deposited in Durham Research Online (record 1414761), citing a Sarcheshmeh resource figure. ' + A('https://durham-repository.worktribe.com/output/1414761', 'durham-repository.worktribe.com'),
 'econg29220': ECONG(29220, 'Sarcheshmeh intrusions and host rocks'),
 'econg33661': ECONG(33661, 'Sarcheshmeh alteration and mineralisation'),
 'fawp_sar': 'Persian Wikipedia: «معدن مس سرچشمه». ' + A('https://fa.wikipedia.org/wiki/%D9%85%D8%B9%D8%AF%D9%86_%D9%85%D8%B3_%D8%B3%D8%B1%DA%86%D8%B4%D9%85%D9%87', 'fa.wikipedia.org'),
 'akhbar_seridun': 'Akhbar-e Madan (in Persian), news 66542: report on a copper discovery at Seridun. ' + A('https://www.akhbaremadan.ir/news/66542/%da%a9%d8%b4%d9%81-%d8%a8%d8%b2%d8%b1%da%af%d8%aa%d8%b1%db%8c%d9%86-%d9%85%d8%b9%d8%af%d9%86-%d8%b0%d8%ae%db%8c%d8%b1%d9%87-%d9%85%d8%b3-%d8%ba%d8%b1%d8%a8-%d8%a2%d8%b3%db%8c%d8%a7-%d8%a7%db%8c%d8%b1%d8%a7%d9%86', 'akhbaremadan.ir'),
 # ---------- میدوک ----------
 'usgs9319': USGS(9319, 'Miduk'),
 'mindat205749': MINDAT('loc-205749', 'Miduk'),
 'porter986': PG('mn986', 'Miduk'),
 'sid32327': 'SID, paper 32327 (Miduk, abstract). ' + A('https://sid.ir/paper/32327/en', 'sid.ir'),
 'taghipour2008': 'Taghipour, N., Aftabi, A. &amp; Mathur, R. (2008). Geology and Re–Os geochronology of mineralization of the Miduk porphyry copper deposit, Iran. <i>Resource Geology</i>, 143–160. ' + DOI('10.1111/j.1751-3928.2008.00054.x'),
 'boomeri2009': 'Boomeri, M., Nakashima, K. &amp; Lentz, D.R. (2009). The Miduk porphyry Cu deposit, Kerman, Iran: a geochemical analysis of the potassic zone … <i>Journal of Geochemical Exploration</i>, 103(1), 17–29. ' + SD('S0375674209000727'),
 'scirep2022': '<i>Scientific Reports</i> (2022). Hypogene enrichment in the Miduk porphyry copper deposit … ' + A('https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9646824/', 'PMC9646824'),
 'jpgu2009': 'Japan Geoscience Union Meeting 2009, abstract K133-P017 (Miduk alteration). ' + A('https://www2.jpgu.org/meeting/2009/program/session/pdf/K133/K133-P017_e.pdf', 'jpgu.org'),
 'civilica557987': 'Final-pit design study of the Miduk copper mine (in Persian). ' + A('https://civilica.com/doc/557987/', 'civilica.com') + '; ' + A('https://anm.yazd.ac.ir/m/article_1118_791ce2d0e9f00c32084ec58228992b15.pdf', 'anm.yazd.ac.ir'),
 # ---------- کهنگ ----------
 'babazadeh2025': 'Babazadeh, Raeisi, Santosh, Zhao &amp; D’Antonio (2025). Recycled mantle source for porphyry mineralization: U−Pb and Re−Os geochronology, and S–Pb–Cu isotopic constraints from the Urumieh-Dokhtar magmatic arc, central Iran. <i>Journal of Geochemical Exploration</i>, 268, 107630. ' + DOI('10.1016/j.gexplo.2024.107630'),
 'jeg2017_kahang': '<i>Journal of Economic Geology</i> (Iran), 2017: Kahang Cu–Mo porphyry deposit (DOAJ record). ' + A('https://doaj.org/article/09e9bf2c13204b0c9f8b9287f67d097e', 'doaj.org'),
 'iut_kahang': 'Isfahan University of Technology, thesis: 3D modeling and reserve estimation of the mineralized body, eastern Cu–Mo anomaly of Kahang. ' + A('https://thesis.iut.ac.ir/3d-modeling-and-reserve-estimation-mineralized-body-eastern-cu-mo-anomaly-kahang-using', 'thesis.iut.ac.ir'),
 'ogr_kahang': '<i>Ore Geology Reviews</i>: ⁴⁰Ar/³⁹Ar geochronology of the Kahang Cu–(Mo) porphyry deposit. ' + SD('S016913681830297X'),
 'porter1711': PG('mn1711', 'Kahang'),
 'mindat_kahang': MINDAT('feature-12086258', 'Kahang'),
 'wp_kahang': WP('Kahang,_Isfahan', 'Kahang, Isfahan (village)'),
 'usgs9261': USGS(9261, 'Qahan'),
 # ---------- سونگون ----------
 'usgs9247': USGS(9247, 'Sungun'),
 'mindat205026': MINDAT('loc-205026', 'Sungun'),
 'hezarkhani1998': 'Hezarkhani, A. &amp; Williams-Jones, A.E. (1998). Controls of alteration and mineralization in the Sungun porphyry copper deposit, Iran. <i>Economic Geology</i>, 93(5), 651–670. ' + DOI('10.2113/gsecongeo.93.5.651'),
 'hassanpour2015': 'Hassanpour, Sh., Alirezaei, S., Selby, D. &amp; Sergeev, S. (2015). <i>International Journal of Earth Sciences</i>, 104, 45–59. ' + DOI('10.1007/s00531-014-1071-0'),
 'simmonds2017': 'Simmonds, Moazzen &amp; Mathur (2017). <i>International Geology Review</i>, 59(12), 1561–1574. ' + DOI('10.1080/00206814.2017.1285258'),
 'egu2016': 'EGU General Assembly 2016, abstract EGU2016-6335 (Sungun). ' + A('https://meetingorganizer.copernicus.org/EGU2016/EGU2016-6335.pdf', 'meetingorganizer.copernicus.org'),
 'jaes_sungun': '<i>Journal of Asian Earth Sciences</i>: Sungun porphyry stock and skarn. ' + SD('S1367912005002075'),
 'sungun_domaining': 'Geological domaining at Sungun porphyry copper deposit using cluster analysis. ' + A('https://www.researchgate.net/publication/364158127_Geological_domaining_at_Sungun_porphyry_copper_deposit_using_cluster_analysis', 'researchgate.net'),
 'shahrekhabar_sungun': 'Shahrekhabar (news aggregator, in Persian): report of 28 Dec 2024 (8 Dey 1403) on Sungun’s new discovery certificate. ' + A('https://www.shahrekhabar.com/news/173635278094879', 'shahrekhabar.com'),
 'boursepress_sungun': 'Boursepress (in Persian), news 118999 (Sungun discovery certificate). ' + A('https://boursepress.ir/news/118999', 'boursepress.ir'),
 # ---------- مسجد داغی ----------
 'usgs9224': USGS(9224, 'Masjed Daghi'),
 'mindat25154': MINDAT('loc-25154', 'East Azerbaijan; Masjed Daghi entry'),
 'ebrahimi2021': 'Ebrahimi, S., Pan, Y. &amp; Rezaeian, M. (2021). <i>Mineralogy and Petrology</i>, 115, 643–662. ' + DOI('10.1007/s00710-021-00761-z'),
 'afzal2023': 'Afzal, Gholami, Madani, Yasrebi &amp; Sadeghi (2023). <i>Minerals</i>, 13(3), 370. ' + DOI('10.3390/min13030370'),
 'rahnama2025': 'Rahnama et al. (2025). <i>Frontiers in Earth Science</i>. ' + DOI('10.3389/feart.2025.1603296'),
 'geoscience2021': '<i>Geoscience</i> (Beijing), 35(2), 535–551 (2021): zircon U–Pb age of the Masjed Daghi intrusion. ' + DOI('10.19657/j.geoscience.1000-8527.2020.105'),
 'econg48126': ECONG(48126, 'Masjed Daghi, 2022'),
 'civilica1384232': 'Civilica, document 1384232 (Masjed Daghi ore mineralogy, in Persian). ' + A('https://civilica.com/doc/1384232/', 'civilica.com'),
 'saba_md': 'Saba industrial database (in Persian): Masjed Daghi copper mine. ' + A('https://infosaba.com/complexes/1502/%D9%85%D8%B9%D8%AF%D9%86-%D9%85%D8%B3-%D9%85%D8%B3%D8%AC%D8%AF-%D8%AF%D8%A7%D8%BA%DB%8C', 'infosaba.com'),
 'inodu2022': 'Inodu (in Persian), Dec 2022: Masjed Daghi mine awaiting an environmental permit. ' + A('https://inodu.ir/2022/12/%D9%85%D8%B9%D8%AF%D9%86-%D9%85%D8%B3%D8%AC%D8%AF-%D8%AF%D8%A7%D8%BA%D9%84%DB%8C-%D9%85%D9%86%D8%AA%D8%B8%D8%B1-%D9%85%D8%AC%D9%88%D8%B2-%D9%85%D8%AD%DB%8C%D8%B7-%D8%B2%DB%8C%D8%B3%D8%AA-%D8%AF%D9%86/', 'inodu.ir'),
 'metalonline_md': 'Metalonline (in Persian): launch of the Masjed Daghi copper and gold mine. ' + A('https://metalonline.ir/material-selection/launch-copper-and-gold-mine-in-masjeddaghi-jolfa', 'metalonline.ir'),
 'scirp_md': 'Paper on the Ali Javad deposit citing Masjed Daghi resources (SCIRP). ' + A('https://file.scirp.org/Html/15-1210567_69943.htm', 'scirp.org'),
 # ---------- دالی ----------
 'usgs9255': USGS(9255, 'Dalli'),
 'ayati2013': 'Ayati, F., Yavuz, F., Asadi, H.H., Richards, J.P. &amp; Jourdan, F. (2013). Petrology and geochemistry of calc-alkaline volcanic and subvolcanic rocks, Dalli porphyry copper–gold deposit, Markazi Province, Iran. <i>International Geology Review</i>, 55(2), 158–184. ' + DOI('10.1080/00206814.2012.689640'),
 'nrr2023': '<i>Natural Resources Research</i>, 32, 501–522 (2023): Dalli porphyry Cu–Au deposit. ' + DOI('10.1007/s11053-023-10165-9'),
 'petrology_dalli': '<i>Petrology</i> (University of Isfahan), article 21231 (Dalli, in Persian). ' + A('https://journals.ui.ac.ir/article_21231.html', 'journals.ui.ac.ir'),
 'tasnim_dalli': 'Tasnim News (in Persian), 24 Feb 2021 (6 Esfand 1399): Markazi industry deputy on Dalli reserves; Delijan MP on pollution. ' + A('https://www.tasnimnews.com/fa/news/1399/12/06/2459550/%D9%85%D8%B9%D8%A7%D9%88%D9%86-%D8%B5%D9%85%D8%AA-%D8%A7%D8%B3%D8%AA%D8%A7%D9%86-%D9%85%D8%B1%DA%A9%D8%B2%DB%8C-%D9%85%D8%B9%D8%AF%D9%86-%D8%AF%D8%A7%D9%84%DB%8C-%D8%AF%D8%A7%D8%B1%D8%A7%DB%8C-%D8%B0%D8%AE%DB%8C%D8%B1%D9%87-%D8%A7%D8%AD%D8%AA%D9%85%D8%A7%D9%84%DB%8C-12-%D9%85%DB%8C%D9%84%DB%8C%D9%88%D9%86-%D8%AA%D9%86-%D9%85%D8%B3-%D8%A7%D8%B3%D8%AA-%D9%86%D9%85%D8%A7%DB%8C%D9%86%D8%AF%D9%87-%D9%85%D8%B1%D8%AF%D9%85-%D8%AF%D9%84%DB%8C%D8%AC%D8%A7%D9%86-%D9%85%D8%AD%DB%8C%D8%B7-%D8%B2%DB%8C%D8%B3%D8%AA-%D8%A2%D9%84%D9%88%D8%AF%DA%AF%DB%8C-%D9%85%D8%B9%D8%AF%D9%86-%D8%B1%D8%A7-%D8%A7%D8%B9%D9%84%D8%A7%D9%85-%DA%A9%D8%B1%D8%AF%D9%87-%D8%A7%D8%B3%D8%AA', 'tasnimnews.com'),
 'donya_dalli': 'Donya-e-Eqtesad (in Persian): the Dalli copper mine. ' + A('https://donya-e-eqtesad.com/%D8%A8%D8%AE%D8%B4-%D8%B4%D8%B1%DA%A9%D8%AA-%D9%87%D8%A7-104/3749102-%DA%A9%D8%A7%D8%B1%D8%A2%D9%81%D8%B1%DB%8C%D9%86%DB%8C-%D8%A8%D9%88%D9%85%DB%8C-%D8%AF%D8%B1-%D9%85%D8%B9%D8%AF%D9%86-%D9%85%D8%B3-%D8%AF%D8%A7%D9%84%DB%8C', 'donya-e-eqtesad.com'),
 # ---------- آهن ----------
 'torab2007': 'Torab, F.M. &amp; Lehmann, B. (2007). Magnetite-apatite deposits of the Bafq district, Central Iran: apatite geochemistry and monazite geochronology. <i>Mineralogical Magazine</i>, 71(3), 347–363. ' + DOI('10.1180/minmag.2007.071.3.347'),
 'stosch2011': 'Stosch, H.-G., Romer, R.L., Daliran, F. &amp; Rhede, D. (2011). <i>Mineralium Deposita</i>, 46, 9–21. ' + DOI('10.1007/s00126-010-0309-4'),
 'heidarian2017': 'Heidarian, H., Alirezaei, S. &amp; Lentz, D.R. (2017). Chadormalu Kiruna-type magnetite-apatite deposit, Bafq district, Iran … <i>Ore Geology Reviews</i>, 83, 43–62. ' + DOI('10.1016/j.oregeorev.2016.11.031'),
 'heidarian2018': 'Heidarian, H. et al. (2018). <i>Minerals</i>, 8(3), 87. ' + DOI('10.3390/min8030087'),
 'heidarian2016': 'Heidarian, H. et al. (2016). <i>Mineralogy and Petrology</i> (sulphur isotopes, Chadormalu). ' + DOI('10.1007/s00710-016-0440-8'),
 'ogr2021_chador': '<i>Ore Geology Reviews</i> (2021): apatite U–Pb ages, Chadormalu. ' + SD('S0169136821000792'),
 'arabjgeo_chador': '<i>Arabian Journal of Geosciences</i>: the Chadormalu iron ore deposit. ' + DOI('10.1007/s12517-015-1813-8'),
 'mindat223338': MINDAT('loc-223338', 'Chadormalu'),
 'wp_chadormalu': WP('Chadormalu', 'Chadormalu'),
 'mindat205068': MINDAT('loc-205068', 'Choghart'),
 'geolcroat2017': '<i>Geologia Croatica</i> (2017): thorium and rare-earth mineralisation at Choghart. ' + A('https://hrcak.srce.hr/177954', 'hrcak.srce.hr'),
 'taghipour_njgpa': 'Taghipour, S. et al. Mineral chemistry and alteration parageneses of the Chogart iron oxide–apatite occurrence, Bafq district, Central Iran. <i>Neues Jahrbuch für Geologie und Paläontologie, Abhandlungen</i>, 269. ' + A('https://www.schweizerbart.de/papers/njgpa/detail/269/80480/Mineral_chemistry_and_alteration_parageneses_of_the_Chogart_iron_oxide_apatite_occurrence_Bafq_district_Central_Iran', 'schweizerbart.de'),
 'jnst_choghart': '<i>Journal of Nuclear Science and Technology</i> (Iran): thorium anomaly in the Choghart marginal breccia (DOAJ record). ' + A('https://doaj.org/article/2e753d7b79cc418ab066670eb91819a7', 'doaj.org'),
 'alibabaie2020': 'Alibabaie, N., Esmaeily, D., Peters, S.T.M. &amp; Lehmann, B. (2020). <i>Ore Geology Reviews</i>, article 103787. ' + DOI('10.1016/j.oregeorev.2020.103787'),
 'mirzaei2018': 'Mirzaei, R. et al. (2018). <i>Ore Geology Reviews</i>, 102, 639–653. ' + DOI('10.1016/j.oregeorev.2018.09.025'),
 'jafari2019': 'Jafari, A. et al. (2019). <i>Journal of Geochemical Exploration</i>, 205, 106330. ' + DOI('10.1016/j.gexplo.2019.06.012'),
 'atapour': 'Atapour &amp; Aftabi. Comment on the origin of the Gol-e-Gohar iron ore. <i>Ore Geology Reviews</i>, article 102942. ' + SD('S016913681930201X'),
 'gohar2023': 'Paper on the Gohar Zamin (No. 3) orebody as a metamorphosed iron formation (2023). ' + SD('S030192682300164X'),
 'mindat258224': MINDAT('loc-258224', 'Gol-e-Gohar'),
 'wp_golgohar': WP('Gol_Gohar_mine', 'Gol Gohar mine'),
 'mathgeo2022': '<i>Mathematical Geosciences</i> (2022), study using Gol-e-Gohar production data. ' + DOI('10.1007/s11004-022-10030-0'),
 'minerals2026': '<i>Minerals</i> (2026), study using Gol-e-Gohar production data. ' + DOI('10.3390/min16020141'),
 'golmohammadi2015': 'Golmohammadi, A., Karimpour, M.H., Malekzadeh Shafaroudi, A. &amp; Mazaheri, S.A. (2015). Alteration-mineralization and radiometric ages of the source pluton at the Sangan iron skarn deposit, northeastern Iran. <i>Ore Geology Reviews</i>, 65(2), 545–563. ' + DOI('10.1016/j.oregeorev.2014.07.005'),
 'sepidbar2017': 'Sepidbar, F., Mirnejad, H., Li, J.-W. &amp; Ma, C. (2017). <i>Ore Geology Reviews</i>, 91, 660–681. ' + DOI('10.1016/j.oregeorev.2017.08.029'),
 'econg30378': ECONG(30378, 'Ferezneh deposit, Sangan'),
 'ijcm_karat': 'ijcm.du.ac.ir, article 1805 (Karat anomaly, Sangan). ' + A('https://ijcm.du.ac.ir/article_1805.html?lang=en', 'ijcm.du.ac.ir'),
 'ijcm_dardvay': 'ijcm.du.ac.ir, article 1419 (Dardvay skarn, Sangan). ' + A('https://ijcm.du.ac.ir/article_1419.html?lang=en', 'ijcm.du.ac.ir'),
 'myb2022': MYB(2022, '2022/myb3-2022-iran.pdf', ', 2022'),
 'gem_nisco': 'Global Energy Monitor wiki: NISCO Sangan Mine. ' + A('https://www.gem.wiki/NISCO_Sangan_Mine', 'gem.wiki'),
 'quds_sangan': 'Quds Online (in Persian): Sangan proven reserve increased to 788 Mt. ' + A('https://www.qudsonline.ir/news/1146876/%D8%A7%D9%81%D8%B2%D8%A7%DB%8C%D8%B4-%D8%B0%D8%AE%DB%8C%D8%B1%D9%87-%D9%82%D8%B7%D8%B9%DB%8C-%D9%85%D8%B9%D8%AF%D9%86-%D8%B3%D9%86%DA%AF%D8%A7%D9%86-%D8%AE%D9%88%D8%A7%D9%81-%D8%A8%D9%87-%DB%B7%DB%B8%DB%B8-%D9%85%DB%8C%D9%84%DB%8C%D9%88%D9%86-%D8%AA%D9%86', 'qudsonline.ir'),
 '911met_sangan': 'Socially responsible mining in East Iran: the Sangan iron ore mines (911metallurgist). ' + A('https://911metallurgist.com/wp-content/uploads/2016/01/Socially-Responsible-Mining-in-East-Iran-The-Sangan-Iron-Ore-Mines.pdf', '911metallurgist.com'),
 'mindat_f34014': MINDAT('feature-34014', 'Sangan area'),
 # ---------- سرب و روی ----------
 'gilg2006': 'Gilg, H.A., Boni, M., Balassone, G., Allen, C.R., Banks, D. &amp; Moore, F. (2006). <i>Mineralium Deposita</i>, 41, 1–16. ' + DOI('10.1007/s00126-005-0035-5'),
 'boni2007': 'Boni, M. et al. (2007). Hypogene Zn carbonate ores in the Angouran deposit, NW Iran. <i>Mineralium Deposita</i>, 42(8), 799–820. ' + DOI('10.1007/s00126-007-0144-4'),
 'daliran2013': 'Daliran, F., Pride, K., Walther, J., Berner, Z.A. &amp; Bakker, R.J. (2013). <i>Ore Geology Reviews</i>, 53, 373–402. ' + DOI('10.1016/j.oregeorev.2013.02.002'),
 'zhuang_gsa': 'Zhuang, L. et al. Vanished evaporites, halokinetic structure and Zn … (Angouran). <i>GSA Bulletin</i>, 136(3–4), from p. 1569. ' + A('https://pubs.geoscienceworld.org/gsa/gsabulletin/article/136/3-4/1569/627638/Vanished-evaporites-halokinetic-structure-and-Zn', 'pubs.geoscienceworld.org'),
 'zhuang2025': 'Zhuang, L. et al. (2025). <i>Mineralium Deposita</i>, 60, 1769–1788. ' + DOI('10.1007/s00126-025-01372-w'),
 'goldschmidt2003': 'Goldschmidt Conference 2003, abstract 406 (Angouran). ' + A('https://goldschmidtabstracts.info/2003/406.pdf', 'goldschmidtabstracts.info'),
 'mindat25133': MINDAT('loc-25133', 'Angouran'),
 'econg40222': '<i>Journal of Economic Geology</i> (Iran), article 40222 (Takab–Takht-e-Soleyman–Angouran district). ' + A('https://econg.um.ac.ir/article_40222.html?lang=en', 'econg.um.ac.ir'),
 'ogr_angouran': '<i>Ore Geology Reviews</i>: sphalerite stages at Angouran. ' + SD('S0169136818302166'),
 'smsm_angouran': 'smsm.ir (in Persian): introduction to the Angouran mine, Zanjan. ' + A('http://smsm.ir/post/725/%D8%A2%D8%B4%D9%86%D8%A7%DB%8C%DB%8C-%D8%A8%D8%A7-%D9%85%D8%B9%D8%AF%D9%86-%D8%A7%D9%86%DA%AF%D9%88%D8%B1%D8%A7%D9%86-%D8%B2%D9%86%D8%AC%D8%A7%D9%86', 'smsm.ir'),
 'wp_anguran_village': WP('Anguran,_Zanjan', 'Anguran, Zanjan (village)'),
 'impasco_angouran': 'IMPASCO (in Persian): Angouran lead and zinc complex. ' + A('https://angouran.impasco.gov.ir/%D8%AF%D9%81%D8%A7%D8%AA%D8%B1-%D9%88-%D8%B4%D8%B1%DA%A9%D8%AA-%D9%87%D8%A7/%D9%85%D8%AC%D8%AA%D9%85%D8%B9%E2%80%8C%D9%87%D8%A7%DB%8C-%D8%AA%D8%A7%D8%A8%D8%B9%D9%87/%D9%85%D8%AC%D8%AA%D9%85%D8%B9%E2%80%8C%D9%87%D8%A7%DB%8C-%D8%AA%D8%A7%D8%A8%D8%B9%D9%87-%D8%AA%D8%AD%D8%AA-%D9%BE%D9%88%D8%B4%D8%B4/%D9%85%D8%AC%D8%AA%D9%85%D8%B9-%D8%B3%D8%B1%D8%A8-%D9%88-%D8%B1%D9%88%DB%8C-%D8%A7%D9%86%DA%AF%D9%88%D8%B1%D8%A7%D9%86/', 'impasco.gov.ir'),
 'imidro_angouran': 'IMIDRO (in Persian), news 26370: opening of the Angouran underground lead–zinc mine. ' + A('http://imidro.gov.ir/news/' + quote('26370-افتتاح-معدن-زیرزمینی-سرب-روی-انگوران.html'), 'imidro.gov.ir'),
 'ajin_angouran': 'Ajin Group: Angouran project. ' + A('https://www.ajingroup.com/projects/doing/angouran', 'ajingroup.com'),
 'myb2019': MYB(2019, '2019/myb3-2019-iran.pdf', ', 2019'),
 'maghfouri2019': 'Maghfouri, S., Hosseinzadeh, M.R., Choulet, F., Alfonso, P., Azim Zadeh &amp; Rajabi, A. (2019). Vent-proximal sub-seafloor replacement clastic-carbonate hosted SEDEX-type mineralization in the Mehdiabad world-class Zn-Pb-Ba-Cu-Ag deposit, Southern Yazd Basin, Iran. <i>Ore Geology Reviews</i>, 113, 103047. ' + DOI('10.1016/j.oregeorev.2019.103047'),
 'upc2023': 'Conference paper on the Mehdiabad deposit (2023), UPCommons. ' + A('https://upcommons.upc.edu/entities/publication/ea02117d-8321-4d57-bfe0-38bab5abe7e7', 'upcommons.upc.edu'),
 'hal_mehdiabad': 'HAL-INSU, record insu-02538008 (Mehdiabad orebodies). ' + A('https://hal-insu.archives-ouvertes.fr/insu-02538008', 'hal-insu.archives-ouvertes.fr'),
 'jaes_mehdiabad': '<i>Journal of Asian Earth Sciences</i>: host formations of the Mehdiabad deposit. ' + SD('S1367912020304478'),
 'reichert2008': 'Reichert, J. &amp; Borg, G. (2008). <i>Ore Geology Reviews</i>, 33, 134–151. ' + DOI('10.1016/j.oregeorev.2007.02.006'),
 'rajabi_iaeg': 'Rajabi, A. et al. Irish Association for Economic Geology volume, pp. 511–532. ' + A('https://iaeg.ie/resources/Documents/Rajabi%20511%20to%20532.pdf', 'iaeg.ie'),
 'rajabi_irish': 'Rajabi, A. et al. An introduction to Irish-type Zn-Pb deposits in early Cretaceous carbonate rocks of Iran. ' + A('https://www.researchgate.net/publication/373770446_An_introduction_to_Irish-type_Zn-Pb_deposits_in_early_Cretaceous_carbonate_rocks_of_Iran', 'researchgate.net'),
 'mindat223163': MINDAT('loc-223163', 'Mehdiabad'),
 'mindat_f403949': MINDAT('feature-403949', 'Mehdiabad, Mehriz'),
 'mehrnews_mehdiabad': 'Mehr News (in Persian), news 5152874: Mehdiabad lead–zinc development project, Mehriz. ' + A('https://www.mehrnews.com/news/5152874/%D8%B7%D8%B1%D8%AD-%D8%AA%D9%88%D8%B3%D8%B9%D9%87-%D9%85%D8%B9%D8%A7%D8%AF%D9%86-%D8%B3%D8%B1%D8%A8-%D9%88-%D8%B1%D9%88%DB%8C-%D9%85%D9%87%D8%AF%DB%8C-%D8%A2%D8%A8%D8%A7%D8%AF-%D9%85%D9%87%D8%B1%DB%8C%D8%B2-%D8%A7%D9%81%D8%AA%D8%AA%D8%A7%D8%AD-%D8%B4%D8%AF', 'mehrnews.com'),
 'akhbaremadan_mehdiabad': 'Akhbar-e Madan (in Persian), news 56504: transfer of the Mehdiabad lead–zinc mine. ' + A('https://akhbaremadan.ir/news/56504/%D8%B3%D8%B1%D9%86%D9%88%D8%B4%D8%AA-%D8%AA%D9%84%D8%AE-%D9%88%D8%A7%DA%AF%D8%B0%D8%A7%D8%B1%DB%8C-%D9%85%D8%B9%D8%AF%D9%86-%D8%B3%D8%B1%D8%A8-%D9%88%D8%B1%D9%88%DB%8C-%D9%85%D9%87%D8%AF%DB%8C-%D8%A2%D8%A8%D8%A7%D8%AF-%D8%AA%D8%A8%D8%AF%DB%8C%D9%84-%D8%B4%D8%AF%D9%86-%D8%AA%D8%AC%D8%A7%D8%B1%D8%AA%DB%8C-%D8%AE%D8%A7%D9%86%D9%88%D8%A7%D8%AF%DA%AF%DB%8C', 'akhbaremadan.ir'),
 'myb2021': MYB('2020–21', '2020-21/myb3-2020-21-iran.pdf', ', 2020–21'),
 'myb2023': MYB(2026, '2023/myb3-2023-iran.pdf', ', 2023 edition (released February 2026)'),
 'miningnews_union': 'MiningNews: Union Capital forges ahead with Iranian zinc project. ' + A('https://www.miningnews.net/capital-markets/news/1182884/union-capital-forges-ahead-iranian-zinc-project', 'miningnews.net'),
 'gsf_review': 'Review in <i>Geoscience Frontiers</i> (2017) citing the Mehdiabad resource. ' + A('https://www.sciencedirect.com/science/article/pii/S1674987117300543', 'sciencedirect.com'),
 'ghazban1994': 'Ghazban, F., McNutt, R.H. &amp; Schwarcz, H.P. (1994). Genesis of sediment-hosted Zn-Pb-Ba deposits in the Irankuh district, Esfahan area, west-central Iran. <i>Economic Geology</i>, 89(6), 1262–1278. ' + DOI('10.2113/gsecongeo.89.6.1262'),
 'karimpour2017': 'Karimpour, M.H. et al. (2017). <i>Journal of Economic Geology</i> (Iran), 9(2), 267–294 (Irankuh). ' + A('https://econg.um.ac.ir/article_32627.html?lang=en', 'econg.um.ac.ir'),
 'boveiri2018': 'Boveiri Konari, M. &amp; Rastad, E. (2018). <i>Geological Journal</i> (Tappehsorkh). ' + DOI('10.1002/gj.2875'),
 'gushfil_paper': 'A sub-seafloor hydrothermal syn-sedimentary to early diagenetic origin for the Gushfil Zn-Pb-Ag-Ba deposit, south Esfahan, Iran. ' + A('https://www.researchgate.net/publication/312203930_A_sub-seafloor_hydrothermal_syn-sedimentary_to_early_diagenetic_origin_for_the_Gushfil_Zn-Pb-Ag-Ba_deposit_south_Esfahan_Iran', 'researchgate.net'),
 'tappehsorkh': '<i>Chemie der Erde – Geochemistry</i>: the Tappehsorkh Zn–Pb deposit, Irankuh district. ' + SD('S0009281918301569'),
 'mindat422688': MINDAT('loc-422688', 'Gushfil, Irankuh'),
 'mindat_f135294': MINDAT('feature-135294', 'Irankuh district'),
 'bama': 'Bama Company, website. ' + A('https://bamaholding.co/en/home/', 'bamaholding.co'),
 'donya_bama': 'Donya-e-Eqtesad (in Persian), news 382142: fundamental analysis of Bama. ' + A('https://donya-e-eqtesad.com/%D8%A8%D8%AE%D8%B4-%D8%A8%D9%88%D8%B1%D8%B3-6/382142-%D8%AA%D8%AD%D9%84%DB%8C%D9%84-%D8%A8%D9%86%DB%8C%D8%A7%D8%AF%DB%8C-%D8%B4%D8%B1%DA%A9%D8%AA-%D8%A8%D8%A7%D9%85%D8%A7', 'donya-e-eqtesad.com'),
 'iranmetals': 'Iran Metals Market (in Persian): Iran’s lead mines. ' + A('https://iranmetalsmarket.ir/lran-lead-mines/', 'iranmetalsmarket.ir'),
 # ---------- طلا ----------
 'mehrabi1999': 'Mehrabi, B., Yardley, B.W.D. &amp; Cann, J.R. (1999). Sediment-hosted disseminated gold mineralisation at Zarshuran, NW Iran. <i>Mineralium Deposita</i>, 34(7), 673–696. ' + DOI('10.1007/s001260050227'),
 'asadi2000': 'Asadi, H.H. et al. (2000). Petrography, mineralogy and geochemistry of the Zarshuran Carlin-like gold deposit, northwest Iran. <i>Mineralium Deposita</i>, 35, 656–671. ' + A('https://www.researchgate.net/publication/226110087_Petrography_mineralogy_and_geochemistry_of_the_Zarshuran_Carlin-like_gold_deposit_northwest_Iran', 'researchgate.net'),
 'zhang2025': 'Zhang, H., Yang, Z., Liu, P., Yang, S. &amp; Badrzadeh, Z. (2025). Generation of the Zarshuran gold deposit … <i>Economic Geology</i>, 120(6), 1503–1519. ' + DOI('10.5382/econgeo.5192'),
 'yang2026': 'Yang et al. (2026). <i>Ore Geology Reviews</i>: ore fluids at Zarshuran. ' + A('https://www.sciencedirect.com/science/article/pii/S0169136826000259', 'sciencedirect.com'),
 'jme977': '<i>Journal of Mining and Environment</i>, article 977 (Zarshuran). ' + A('https://jme.shahroodut.ac.ir/article_977.html', 'jme.shahroodut.ac.ir'),
 'daliranite': 'Daliranite, PbHgAs₂S₆, a new sulphosalt from the Zarshouran Au–As deposit, Takab region, Iran. <i>Mineralogical Magazine</i>. ' + A('https://resolve.cambridge.org/core/journals/mineralogical-magazine/article/abs/daliranite-pbhgas2s6-a-new-sulphosalt-from-the-zarshouran-auas-deposit-takab-region-iran/E9B95E5E7F9CC5EBF30F91054F39EBB0', 'cambridge.org'),
 'usgs_sedau35': 'USGS, sediment-hosted gold deposits of the world, record 35: Zarshuran. ' + A('https://mrdata.usgs.gov/sedau/show-sedau.php?rec_id=35', 'mrdata.usgs.gov'),
 'mindat25142': MINDAT('loc-25142', 'Zarshuran'),
 'mindat445510': MINDAT('loc-445510', 'second Zarshuran entry, Shahin Dezh County'),
 'tehrantimes_zar': 'Tehran Times, news 506956 (Zarshuran gold). ' + A('https://www.tehrantimes.com/news/506956/', 'tehrantimes.com'),
 'eghtesad2024': 'Eghtesad Online, Dec 2024: Iran’s largest gold mine reports increase in proven reserves. ' + A('https://www.eghtesadonline.com/en/news/2000385/irans-largest-gold-mine-reports-increase-in-proven-reserves', 'eghtesadonline.com'),
 'eghtesad2016': 'Eghtesad Online, Nov 2016: rise in Zarshouran’s gold extraction. ' + A('https://www.eghtesadonline.com/en/news/771272/rise-in-zarshourans-gold-extraction', 'eghtesadonline.com'),
 'donyayemadan_zar': 'Donya-ye Ma’adan (in Persian), news 271360 (Zarshuran gold production). ' + A('https://www.donyayemadan.com/%D8%A8%D8%AE%D8%B4-%D8%B7%D9%84%D8%A7-16/271360-%D8%B2%D8%B1%D8%B4%D9%88%D8%B1%D8%A7%D9%86-%D8%AF%D8%B1-%D9%85%D8%B3%DB%8C%D8%B1-%D8%AC%D9%87%D8%B4-%D8%AA%D9%88%D9%84%DB%8C%D8%AF-%D8%B7%D9%84%D8%A7', 'donyayemadan.com'),
 'bariteco_gold': 'Bariteco (in Persian): Iran’s largest gold mines. ' + A('https://bariteco.ir/irans-largest-gold-mines/', 'bariteco.ir'),
 'anglo2001': 'Anglo American (Anglo Exploration). <i>Final technical report, Zarshuran gold project</i> (2001), via data.gov.ir. ' + A('https://data.gov.ir/dataset/543d9709-501b-45bb-a55a-565cd28511c1/resource/522eba58-9379-421d-b7e3-1dbe00e783bd/download/final_technical_report__zarshuran_gold_project.doc', 'data.gov.ir'),
 'daliran2008': 'Daliran, F. (2008). The carbonate rock-hosted epithermal gold deposit of Agdarreh, Takab geothermal field, NW Iran. <i>Mineralium Deposita</i>, 43(4), 383–404. ' + DOI('10.1007/s00126-007-0167-x'),
 'daliran2018': 'Daliran, F., Hofstra, A., Walther, J. &amp; Topa, D. (2018). In Muntean, J.L. (ed.), <i>Diversity in Carlin-Style Gold Deposits</i>, Reviews in Economic Geology 20, 299–333. ' + DOI('10.5382/rev.20.09'),
 'mindat_ref156983': 'Mindat.org, reference record 156983 (Daliran 2008, Agdarreh). ' + A('https://www.mindat.org/reference.php?id=156983', 'mindat.org'),
 'wp_aghdarreh_village': WP('Aghdarreh', 'Aghdarreh (village in Khoy County)'),
 'fawp_agdarreh': 'Persian Wikipedia: «معدن طلای آق‌دره». ' + A('https://fa.wikipedia.org/wiki/%D9%85%D8%B9%D8%AF%D9%86_%D8%B7%D9%84%D8%A7%DB%8C_%D8%A2%D9%82%E2%80%8C%D8%AF%D8%B1%D9%87', 'fa.wikipedia.org'),
 'ifb_agdarreh': 'Iran Fara Bourse (IFB), news 15334 (Agh-Darreh gold). ' + A('https://www.ifb.ir/News.aspx?id=15334', 'ifb.ir'),
 'bambo_fazar': 'Bambo (in Persian): fundamental analysis of the «فزر» share. ' + A('https://bambo.fund/blog/news/fundamental-analysis-of-fazar/', 'bambo.fund'),
 'richards2006': 'Richards, J.P., Wilkinson, D. &amp; Ullrich, T. (2006). Geology of the Sari Gunay epithermal gold deposit, northwest Iran. <i>Economic Geology</i>, 101(8), 1455–1496. ' + A('https://hero.epa.gov/hero/index.cfm/reference/details/reference_id/4190383', 'hero.epa.gov'),
 'jeg2021_sg': 'Mehrabi, B., Ghasemi Siani, M. et al. (2021). <i>Journal of Economic Geology</i> (Iran), 12(4), 509–530 (Sari Gunay). ' + A('https://econg.um.ac.ir/article_39844_en.html', 'econg.um.ac.ir') + '; ' + A('https://doaj.org/article/4886a48902f3475a92ff4e3449c15d09', 'doaj.org'),
 'jge2014_sg': '<i>Journal of Geochemical Exploration</i> (2014): Sari Gunay, citing Bartram (2005). ' + SD('S0375674214002210'),
 'scirep2026_sg': '<i>Scientific Reports</i> (2026): Sari Gunay. ' + DOI('10.1038/s41598-026-42248-x'),
 'review_sg': 'A review of tectono-magmatic evolution and gold metallogeny in the inner parts of Zagros orogeny: a tectonic model for the major gold deposits, western Iran. ' + A('https://www.researchgate.net/publication/308575132_A_review_of_tectono-magmatic_evolution_and_gold_metallogeny_in_the_inner_parts_of_Zagros_orogeny_a_tectonic_model_for_the_major_gold_deposits_western_Iran', 'researchgate.net'),
 'mineplan_sg': 'Determination of optimal production rate under price uncertainty — Sari Gunay gold mine, Iran. ' + A('https://www.researchgate.net/publication/349502744_Determination_of_optimal_production_rate_under_price_uncertainty-Sari_Gunay_gold_mine_Iran', 'researchgate.net'),
 'gsi_sg': 'Geological Survey of Iran (GSI), English tag page mentioning Sari Gunay. ' + A('https://gsi.ir/en/tag/66/MAZANDARAN', 'gsi.ir'),
 'zarkuh': 'Zarkuh Mining Co., website. ' + A('https://www.zarkuhco.ir/', 'zarkuhco.ir'),
 'akhbaremadan_sg': 'Akhbar-e Madan (in Persian), news 29348 (Sari Gunay heap leaching). ' + A('https://www.akhbaremadan.ir/news/29348', 'akhbaremadan.ir'),
 'asriran_sg': 'Asriran (in Persian), news 535209: gold production at Sari Gunay, Qorveh. ' + A('https://www.asriran.com/fa/news/535209/%D8%AA%D9%88%D9%84%DB%8C%D8%AF-%D8%B7%D9%84%D8%A7-%D8%AF%D8%B1-%D9%85%D8%B9%D8%AF%D9%86-%D8%B3%D8%A7%D8%B1%DB%8C%DA%AF%D9%88%D9%86%DB%8C-%D9%82%D8%B1%D9%88%D9%87-2-%D8%A8%D8%B1%D8%A7%D8%A8%D8%B1-%D9%85%DB%8C%E2%80%8C%D8%B4%D9%88%D8%AF', 'asriran.com'),
 'mehrnews_sg': 'Mehr News (in Persian), news 5350559: Qorveh villages and the gold mines. ' + A('https://www.mehrnews.com/news/5350559/%D9%85%D8%AD%D8%B1%D9%88%D9%85%DB%8C%D8%AA-%D8%B1%D9%88%D8%B3%D8%AA%D8%A7%DB%8C%DB%8C%D8%A7%D9%86-%D9%82%D8%B1%D9%88%D9%87-%D8%AF%D8%B1-%DA%A9%D9%86%D8%A7%D8%B1-%D9%85%D8%B9%D8%A7%D8%AF%D9%86-%D8%B7%D9%84%D8%A7', 'mehrnews.com'),
 'porter1256': PG('mn1256', 'Sari Gunay'),
 'mindat146021': MINDAT('loc-146021', 'Sari Gunay, estimated point'),
 'moritz2006': 'Moritz, R., Ghazban, F. &amp; Singer, B.S. (2006). Eocene gold ore formation at Muteh, Sanandaj-Sirjan tectonic zone, western Iran. <i>Economic Geology</i>, 101(8), 1497–1524. ' + A('https://www.unige.ch/sciences/terre/research/Groups/mineral_resources/archive/pub_archive/moritz_muteh_seg_2006.pdf', 'unige.ch'),
 'unige_muteh': 'Archive ouverte UNIGE, record 21628 (Muteh). ' + A('https://archive-ouverte.unige.ch/unige:21628', 'archive-ouverte.unige.ch'),
 'chahbagh2014': '<i>Journal of Asian Earth Sciences</i> (2014): the Chah Bagh gold deposit, Muteh district. ' + SD('S1367912014002053'),
 'aliyari2012': 'Aliyari, F. et al. (2012). <i>Resource Geology</i> (Muteh district). ' + DOI('10.1111/j.1751-3928.2012.00196.x'),
 'irandaily2019': 'Iran Daily, 16 Feb 2019 (via PressReader). ' + A('https://www.pressreader.com/iran/iran-daily/20190216/281625306569981', 'pressreader.com'),
 'madco_muteh': 'MADCO (in Persian): Muteh gold complex. ' + A('https://www.madco-co.com/portfolio-item/%D9%85%D8%AC%D8%AA%D9%85%D8%B9-%D8%B7%D9%84%D8%A7%DB%8C-%D9%85%D9%88%D8%AA%D9%87/', 'madco-co.com'),
 'imico_muteh': 'IMICO: Muteh gold complex, company record 966. ' + A('https://www.imico.org/detail/company/966', 'imico.org'),
 'beytoote_muteh': 'Beytoote (in Persian): introduction to Iran’s gold mines. ' + A('https://www.beytoote.com/scientific/midanid/introduced2-gold-mine.html', 'beytoote.com'),
 'rimag_muteh': 'Rimag (in Persian), article 9458 (Senjedeh pyrite, Muteh). ' + A('https://www.rimag.ir/fa/Article/9458', 'rimag.ir'),
 'myb1977_muteh': '<i>Minerals Yearbook 1977</i>, Iran chapter. ' + A('https://search.library.wisc.edu/digital/AJQSGMV2MT4PFA8B/text/AS6DJZQK5KVUGG8V', 'search.library.wisc.edu'),
 'mindat28816': MINDAT('loc-28816', 'Muteh mine'),
 'mindat28815': MINDAT('loc-28815', 'Senjedeh pit, Muteh'),
 'wp_muteh': WP('Muteh', 'Muteh (village)'),
}

def R(fa, en, bfa, ben, src, conf, calc=None, direct=None, lab=None, chart=True, dn=('اعلام‌شده', 'as stated')):
    """یک رقم منتشرشده. calc: [(میلیون تن، عیار)] برای محاسبهٔ فلز محتوا؛ direct: فلز محتوای اعلام‌شده (تن) با برچسب dn."""
    return dict(fa=fa, en=en, bfa=bfa, ben=ben, src=src, conf=conf, calc=calc, direct=direct, lab=lab, chart=chart, dn=dn)

LINKS_CU = {'art': ['resources-vs-reserves', 'kriging'], 'svc': ['resource-estimation', 'mineral-exploration'], 'tools': ['grade-converter', 'cut-off-grade']}
LINKS_FE = {'art': ['resources-vs-reserves', 'qaqc'], 'svc': ['resource-estimation', 'exploration-geophysics'], 'tools': ['grade-converter']}
LINKS_ZN = {'art': ['resources-vs-reserves', 'variogram'], 'svc': ['resource-estimation', '3d-geological-modelling'], 'tools': ['grade-converter', 'cut-off-grade']}
LINKS_AU = {'art': ['cut-off-grade', 'qaqc'], 'svc': ['resource-estimation', 'exploration-geochemistry'], 'tools': ['cut-off-grade', 'grade-converter']}

SRC.update({
 'wikidata_sar': 'Wikidata Q2719739 (Sarcheshmeh copper complex). ' + A('https://www.wikidata.org/wiki/Q2719739', 'wikidata.org'),
 'mindat440464': MINDAT('loc-440464', 'Dalli'),
})

# =====================================================================
#  مس پورفیری
# =====================================================================
SARCHESHMEH = dict(
 slug='sarcheshmeh', commodity='cu', ntype='porphyry', metal='cu',
 lat=29.945, lon=55.8619, coord_src='Mindat', coord_cite='mindat21589', coord_conf='H',
 published=P, updated=P, related=['miduk', 'sungun', 'kahang'], links=LINKS_CU,
 res=[
  R('۱٬۵۳۸ میلیون تن با ۰٫۵۸٪ مس، ۰٫۰۳٪ مولیبدن و ۰٫۰۶ گرم در تن طلا', '1,538 Mt @ 0.58% Cu, 0.03% Mo, 0.06 g/t Au',
    'USGS؛ مجموع گروه با نوچون، سرکوه و سریدون؛ سال ذکر نشده', 'USGS; group total including Now Chun, Sar Kuh and Seridune; year not shown',
    ['usgs9329'], 'H', calc=[(1538, .58)], lab=('USGS (مجموع گروه)', 'USGS (group total)')),
  R('۱٬۵۵۷ میلیون تن سولفیدی با ۰٫۵۵۷٪ مس', '1,557 Mt sulphide @ 0.557% Cu', 'Mindat؛ سال و منبع اولیه ذکر نشده', 'Mindat; year and primary source not shown',
    ['mindat21589'], 'M', calc=[(1557, .557)], lab=('Mindat', 'Mindat')),
  R('۱٬۲۰۰ میلیون تن با ۰٫۶۹٪ مس و ۳۰۰ ppm مولیبدن', '1,200 Mt @ 0.69% Cu, 300 ppm Mo', 'نقل ثانویه در Hassanpour و همکاران', 'Secondary citation in Hassanpour et al.',
    ['hassanpour_durham'], 'M', calc=[(1200, .69)], lab=('Hassanpour و همکاران', 'Hassanpour et al.')),
  R('۱٬۲۰۰ میلیون تن با ۱٫۲٪ مس، ۰٫۰۳٪ مولیبدن، ۰٫۲۷ گرم در تن طلا و ۳٫۹ گرم در تن نقره', '1,200 Mt @ 1.2% Cu, 0.03% Mo, 0.27 g/t Au, 3.9 g/t Ag',
    'PorterGeo به نقل از Ellis (۱۹۹۱)؛ عیار مس حدود دو برابر سایر منابع', 'PorterGeo citing Ellis (1991); Cu grade about twice every other source',
    ['porter985'], 'L', calc=[(1200, 1.2)], lab=('PorterGeo', 'PorterGeo')),
 ],
 fa=dict(
  name='سرچشمه', province='کرمان', type_short='مس–مولیبدن پورفیری',
  title='کانسار مس پورفیری سرچشمه: زمین‌شناسی، دگرسانی و ارقام ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار مس پورفیری سرچشمه',
  desc='زمین‌شناسی کانسار مس–مولیبدن پورفیری سرچشمه کرمان: سنگ میزبان، سن‌سنجی، پهنه‌های دگرسانی، ارقام ذخیرهٔ منتشرشده با منبع و سال، و تحلیل مس محتوا.',
  lede='سرچشمه، در کمربند پورفیری کرمان، شناخته‌شده‌ترین کانسار مس پورفیری ایران است. این صفحه زمین‌شناسی، سن و دگرسانی آن را از مقاله‌های منتشرشده خلاصه می‌کند و ارقام ذخیرهٔ متفاوتی را که برایش منتشر شده، با منبع و سال کنار هم می‌گذارد.',
  coord_note='نقطهٔ Wikidata مجتمع مس را، حدود ۴٫۵ کیلومتر شمال پیت، نشان می‌دهد و برای موقعیت کانسار مناسب نیست[[wikidata_sar]]. PorterGeo و یک مقالهٔ ۲۰۱۸ نقاطی در فاصلهٔ ۰٫۴ تا ۱ کیلومتری این نقطه می‌دهند[[porter985]].',
  facts=[
   ('aka', 'Sar Cheshmeh، Sarcheshmeh'),
   ('loc', 'استان کرمان؛ شهرستان قطعی نیست: Mindat آن را ذیل پاریز (شهرستان سیرجان) آورده و انتساب رایج به شهرستان رفسنجان در منابع بررسی‌شده تأیید نشد[[mindat21589]]'),
   ('comm', 'مس و مولیبدن، با طلا و نقره به‌عنوان محصول جانبی؛ عیارهای USGS: ۰٫۵۸٪ مس، ۰٫۰۳٪ مولیبدن و ۰٫۰۶ گرم در تن طلا[[usgs9329]]'),
   ('type', 'مس–مولیبدن پورفیری میوسن'),
   ('belt', 'کمربند پورفیری کرمان (کمان ماگمایی سنوزوئیک کرمان)، بخش جنوب‌شرقی کمان ارومیه–دختر[[caltech_kerman]]'),
   ('host', 'استوک گرانودیوریت پورفیری درون سنگ‌های آتشفشانی–رسوبی ائوسن[[econg29220]]'),
   ('age', 'زیرکن U–Pb حدود ۱۳٫۶ میلیون سال (به نقل USGS)[[usgs9329]] و ۱۲٫۹۷ ± ۰٫۲۳ میلیون سال برای استوک[[magiran2016]]؛ سن Re–Os یافت نشد'),
   ('op', 'شرکت ملی صنایع مس ایران[[nicico]]؛ USGS در رکوردی مربوط به حدود ۲۰۱۰ تا ۲۰۱۵ آن را «تولیدکننده» توصیف کرده است[[usgs9329]]؛ اطلاعات وضعیت ۲۰۲۴ تا ۲۰۲۶ یافت نشد'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی و سن', '''<p>Aghazadeh و همکاران (۲۰۱۵) کانسارهای مس پورفیری ایران را در سه ناحیه گروه‌بندی کرده‌اند: ارسباران در شمال‌غرب، بخش میانی کمان ماگمایی ارومیه–دختر و کرمان. این کانسارها در چند پالس و هم‌زمان با بسته شدن اقیانوس نئوتتیس تشکیل شده‌اند[[aghazadeh2015]]. سرچشمه در کمربند پورفیری کرمان، بخش جنوب‌شرقی این کمان، قرار دارد که مهم‌ترین دورهٔ کانی‌سازی آن میوسن پیشین تا میانی است[[caltech_kerman]].</p>
<p>کانی‌سازی به یک استوک گرانودیوریت پورفیری وابسته است که در سنگ‌های آتشفشانی–رسوبی ائوسن نفوذ کرده است[[econg29220]]؛ مقالهٔ Waterman و Hamilton (۱۹۷۵) از مراجع کلاسیک این کانسار است[[waterman1975]]. دو نتیجهٔ سن‌سنجی زیرکن U–Pb حدود ۰٫۶ میلیون سال با هم فاصله دارند: ۱۳٫۶ میلیون سال، که USGS از McInnes و همکاران (۲۰۰۵) نقل می‌کند[[usgs9329]]، و ۱۲٫۹۷ ± ۰٫۲۳ میلیون سال برای استوک، ۱۲٫۳۷ ± ۰٫۱ میلیون سال برای یک پورفیری تأخیری و حدود ۱۲٫۲ میلیون سال برای دایک‌ها در یک مقالهٔ فارسی سال ۲۰۱۶[[magiran2016]]. سن Re–Os مولیبدنیت برای سرچشمه در منابع بررسی‌شده یافت نشد.</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>چهار پهنهٔ دگرسانی پتاسیک (غالب)، فیلیک، آرژیلیک و پروپیلیتیک در سرچشمه شناخته شده است. کانی‌های اصلی کالکوپیریت، بورنیت، مولیبدنیت و پیریت‌اند و بورنیت و مولیبدنیت بیشتر در عمق دیده می‌شوند[[econg33661]]. به گزارش Mindat، گرانودیوریت مرحلهٔ نخست تا ۱٫۴ درصد مس دارد و پورفیری مرحلهٔ دوم عقیم است[[mindat21589]]. غنی‌شدگی سوپرژن در پهنهٔ فیلیک گزارش شده، اما در منابع بررسی‌شده توصیف روشنی از گسترش و ضخامت پتوی کالکوسیتی نیامده است.</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>ارقام چندمیلیارد تنی که گاه در رسانه‌ها برای «سرچشمه» نقل می‌شود به مجموعهٔ کانسارهای ناحیه، از جمله سریدون، مربوط است و با ارقام خود کانسار در جدول بالا هم‌دامنه نیست[[fawp_sar]][[akhbar_seridun]].</p>'''),
  ],
  expert=[
   ('همگرایی مس محتوا با وجود اختلاف تناژ', '''<p>سه رقم USGS، Mindat و Hassanpour و همکاران تا ۳۰ درصد در تناژ اختلاف دارند (۱٬۲۰۰ تا ۱٬۵۵۷ میلیون تن)، اما هر سه به ۸٫۳ تا ۸٫۹ میلیون تن مس محتوا می‌رسند. این الگو با گزارش یک پیکرهٔ کانسنگ با عیار حد یا محدودهٔ متفاوت سازگار است: عیار حد پایین‌تر تناژ بیشتر و عیار میانگین کمتری می‌دهد، درحالی‌که فلز محتوا تغییر چندانی نمی‌کند. رقم USGS افزون بر این مجموع گروه است و نوچون، سرکوه و سریدون را هم دربرمی‌گیرد.</p>
<p>عیار ۱٫۲ درصد مس در نسخهٔ PorterGeo حدود دو برابر سایر منابع است و ۱۴٫۴ میلیون تن مس محتوا می‌دهد؛ به احتمال زیاد خطای نقل است. پیش از هر مقایسهٔ اقتصادی، عیار حد، تاریخ، نوع کانسنگ (سولفیدی یا اکسیدی) و محدودهٔ هر رقم باید روشن شود؛ تفاوت این عوامل از تفاوت خود ارقام مهم‌تر است.</p>'''),
  ]),
 en=dict(
  name='Sarcheshmeh', province='Kerman', type_short='Porphyry Cu–Mo',
  title='Sarcheshmeh Porphyry Copper Deposit: Geology, Alteration and Resource Figures | Ali Alinaghi',
  h1='Sarcheshmeh porphyry copper deposit: geology and resources',
  desc='Geology of the Sarcheshmeh porphyry Cu–Mo deposit, Kerman, Iran: host rocks, geochronology, alteration zones, published resource figures with source and year, and a contained-copper check.',
  lede='Sarcheshmeh, in the Kerman porphyry belt, is Iran’s best-known porphyry copper deposit. This page summarises its geology, age and alteration from published papers and sets the differing resource figures published for it side by side, each with its source and year.',
  coord_note='The Wikidata point marks the copper complex about 4.5 km north of the pit and should not be used for the deposit[[wikidata_sar]]. PorterGeo and a 2018 paper give points 0.4–1 km from this one[[porter985]].',
  facts=[
   ('aka', 'Sar Cheshmeh; Persian: سرچشمه'),
   ('loc', 'Kerman Province; county unresolved — Mindat files it under Pariz, Sirjan County, and the commonly assumed Rafsanjan County was not confirmed in the sources reviewed[[mindat21589]]'),
   ('comm', 'Copper and molybdenum with gold and silver credits; USGS grades 0.58% Cu, 0.03% Mo, 0.06 g/t Au[[usgs9329]]'),
   ('type', 'Miocene porphyry Cu–Mo'),
   ('belt', 'Kerman porphyry belt (Kerman Cenozoic Magmatic Arc), the southeastern segment of the Urumieh–Dokhtar arc[[caltech_kerman]]'),
   ('host', 'Granodiorite porphyry stock in Eocene volcano-sedimentary rocks[[econg29220]]'),
   ('age', 'Zircon U–Pb about 13.6 Ma (cited by USGS)[[usgs9329]] and 12.97 ± 0.23 Ma for the stock[[magiran2016]]; no Re–Os age found'),
   ('op', 'National Iranian Copper Industries Co. (NICICO)[[nicico]]; described by USGS as a producer in a record from about 2010–15[[usgs9329]]; no 2024–26 status found'),
  ],
  sections=[
   ('Geological setting and age', '''<p>Aghazadeh et al. (2015) group Iran’s porphyry copper deposits into three regions: Arasbaran in the northwest, the middle segment of the Urumieh–Dokhtar magmatic arc, and Kerman. The deposits formed in pulses tied to the closure of the Neo-Tethys ocean[[aghazadeh2015]]. Sarcheshmeh lies in the Kerman porphyry belt, the southeastern segment of the arc, whose most important mineralising period is Early–Middle Miocene[[caltech_kerman]].</p>
<p>Mineralisation is related to a granodiorite porphyry stock emplaced into Eocene volcano-sedimentary rocks[[econg29220]]; Waterman and Hamilton (1975) is one of the classic references on the deposit[[waterman1975]]. Two zircon U–Pb results are about 0.6 million years apart: 13.6 Ma, which USGS cites from McInnes et al. (2005)[[usgs9329]], and 12.97 ± 0.23 Ma for the stock, 12.37 ± 0.1 Ma for a late porphyry and about 12.2 Ma for dykes in a 2016 Persian-language paper[[magiran2016]]. No molybdenite Re–Os age was found in the sources reviewed.</p>'''),
   ('Alteration and mineralisation', '''<p>Four alteration zones are recognised: potassic (dominant), phyllic, argillic and propylitic. The main ore minerals are chalcopyrite, bornite, molybdenite and pyrite, with bornite and molybdenite mostly at depth[[econg33661]]. According to Mindat, the first-stage granodiorite carries up to 1.4% Cu and the second-stage porphyry is barren[[mindat21589]]. Supergene enrichment is reported in the phyllic zone, but the sources reviewed do not describe the extent or thickness of the chalcocite blanket.</p>'''),
   ('Published resource figures', '''{{res}}<p>The multi-billion-tonne figures sometimes quoted for “Sarcheshmeh” in the media refer to the wider cluster of deposits in the district, including Seridun, and do not share the scope of the deposit figures above[[fawp_sar]][[akhbar_seridun]].</p>'''),
  ],
  expert=[
   ('Contained copper converges although tonnage does not', '''<p>The USGS, Mindat and Hassanpour et al. figures differ by up to 30% in tonnage (1,200 to 1,557 Mt), yet all three imply 8.3–8.9 Mt of contained copper. That pattern fits one orebody reported at different cut-off grades or scopes: a lower cut-off gives more tonnes at a lower average grade while contained metal barely moves. The USGS figure is also a group total that includes Now Chun, Sar Kuh and Seridune.</p>
<p>PorterGeo’s 1.2% Cu is about twice every other source’s grade and would imply 14.4 Mt of copper; it is almost certainly a transcription error. Before any economic comparison, the cut-off grade, date, ore type (sulphide or oxide) and scope of each figure need to be established; those differences matter more than the headline numbers.</p>'''),
  ]),
)

MIDUK = dict(
 slug='miduk', commodity='cu', ntype='porphyry', metal='cu',
 lat=30.42056, lon=55.16722, coord_src='Mindat', coord_cite='mindat205749', coord_conf='H',
 published=P, updated=P, related=['sarcheshmeh', 'kahang', 'dalli'], links=LINKS_CU,
 res=[
  R('۱۷۶ میلیون تن با ۰٫۶۱٪ مس، ۰٫۰۰۷٪ مولیبدن و ۱٫۸ گرم در تن نقره', '176 Mt @ 0.61% Cu, 0.007% Mo, 1.8 g/t Ag', 'USGS، حدود ۲۰۱۵', 'USGS, about 2015',
    ['usgs9319'], 'H', calc=[(176, .61)], lab=('USGS (حدود ۲۰۱۵)', 'USGS (about 2015)')),
  R('۲۴۱ میلیون تن کانسنگ با ۰٫۶۱٪ مس؛ ارزش خالص فعلی ۸۶۸ میلیون دلار؛ نسبت باطله‌برداری ۲٫۵۵', '241 Mt ore @ 0.61% Cu; NPV US$868 M; stripping ratio 2.55',
    'مطالعهٔ فارسی طراحی پیت نهایی؛ سال در دسترس نیست', 'Persian final-pit study; year not retrieved',
    ['civilica557987'], 'M', calc=[(241, .61)], lab=('مطالعهٔ پیت نهایی', 'Final-pit study')),
 ],
 fa=dict(
  name='میدوک', province='کرمان', type_short='مس–مولیبدن پورفیری',
  title='کانسار مس پورفیری میدوک شهربابک: زمین‌شناسی، سن و ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار مس پورفیری میدوک',
  desc='کانسار مس پورفیری میدوک در شهرستان شهربابک کرمان: دو فاز نفوذی میوسن، سن Re–Os، پهنه‌های دگرسانی و غنی‌شدگی، و ارقام ذخیرهٔ منتشرشده با منبع.',
  lede='میدوک، حدود ۴۰ کیلومتری شمال‌شرق شهربابک، یکی از کانسارهای اصلی کمربند پورفیری کرمان است و سن کانی‌سازی آن با روش Re–Os روی مولیبدنیت به‌دقت تعیین شده است.',
  coord_note='نقطهٔ USGS حدود ۰٫۹ کیلومتر با این نقطه فاصله دارد[[usgs9319]].',
  facts=[
   ('aka', 'Meiduk، Meydouk'),
   ('loc', 'استان کرمان؛ شهرستان شهربابک، ۴۰ تا ۴۲ کیلومتری شمال‌شرق شهربابک[[mindat205749]]'),
   ('comm', 'مس و مولیبدن، با طلا و نقره؛ عیارهای USGS: ۰٫۶۱٪ مس، ۰٫۰۰۷٪ مولیبدن و ۱٫۸ گرم در تن نقره[[usgs9319]]'),
   ('type', 'مس–مولیبدن پورفیری میوسن'),
   ('belt', 'کمربند پورفیری کرمان؛ سن Re–Os میدوک «مرحلهٔ اصلی ماگماتیسم و تشکیل مس پورفیری» در این کمربند را نشان می‌دهد[[taghipour2008]]'),
   ('host', 'آتشفشانی‌های آندزیتی–بازالتی ائوسن که دو فاز نفوذی کالک‌آلکالن میوسن (P1 و P2) آن‌ها را قطع کرده‌اند[[taghipour2008]]'),
   ('age', 'Re–Os مولیبدنیت ۱۲٫۲۳ ± ۰٫۰۷ میلیون سال، هم‌خوان با سن زیرکن فاز P2[[taghipour2008]]؛ USGS سن U–Pb را ۱۲٫۵ ± ۰٫۱ میلیون سال آورده است[[usgs9319]]'),
   ('op', 'شرکت ملی صنایع مس ایران؛ معدن روباز با طرح توسعه‌ای که USGS برای ۲۰۱۵ ذکر کرده بود[[usgs9319]]؛ راه‌اندازی مجتمع در دسامبر ۲۰۰۴ (اطمینان کم تا متوسط)[[porter986]]'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی و سن', '''<p>میدوک در کمربند پورفیری کرمان قرار دارد. واحدهای میزبان آتشفشانی‌های آندزیتی–بازالتی ائوسن‌اند که دو فاز نفوذی کالک‌آلکالن میوسن، P1 و P2، در آن‌ها نفوذ کرده‌اند. سن Re–Os مولیبدنیت ۱۲٫۲۳ ± ۰٫۰۷ میلیون سال است و با سن زیرکن فاز P2، دومین فاز کانه‌دار، هم‌خوانی دارد[[taghipour2008]]. USGS سن U–Pb را ۱۲٫۵ ± ۰٫۱ میلیون سال آورده است[[usgs9319]]. این سن‌ها همراه با سن‌های سرچشمه بازهٔ حدود ۱۲ تا ۱۳٫۶ میلیون سال را برای کانی‌سازی در این بخش از کمربند کرمان نشان می‌دهند.</p>
<p>فاصلهٔ مستقیم میدوک تا سرچشمه حدود ۸۵ کیلومتر است که با رقم یک چکیدهٔ علمی هم‌خوانی دارد[[sid32327]]؛ رقم ۱۳۰ تا ۱۳۲ کیلومتری برخی مقاله‌های فارسی احتمالاً فاصلهٔ جاده‌ای است.</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>پهنه‌های دگرسانی پتاسیک، فیلیک و پروپیلیتیک به‌صورت هم‌مرکز گسترش یافته‌اند[[jpgu2009]]. کانی‌سازی مرحلهٔ اصلی از کالکوپیریت، مگنتیت و انیدریت تشکیل شده است. در پهنه‌های پتاسیک عمیق، کالکوسیت و کوولیت–دیژنیت درون‌زاد (هیپوژن) گزارش شده و پهنه‌های شسته‌شده، اکسیدی و سولفیدی سوپرژن نیز وجود دارند[[scirep2022]]. Boomeri و همکاران (۲۰۰۹) ژئوشیمی پهنهٔ پتاسیک را بررسی کرده‌اند[[boomeri2009]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>همان مطالعهٔ پیت نهایی عمر ۲۷ ساله و ۳۶۰ متر عمیق‌تر شدن پیت را برآورد کرده است[[civilica557987]]. مقاله‌ها و مرورهای قدیمی‌تر ارقام دیگری هم آورده‌اند که منبع اولیهٔ آن‌ها در منابع بررسی‌شده مشخص نشد.</p>'''),
  ],
  expert=[
   ('دو رقم، دو مبنا', '''<p>رقم USGS (۱۷۶ میلیون تن با ۰٫۶۱٪ مس، حدود ۱٫۱ میلیون تن مس محتوا) و رقم مطالعهٔ پیت نهایی (۲۴۱ میلیون تن کانسنگ با همان عیار، حدود ۱٫۵ میلیون تن مس) عیار یکسان اما تناژ متفاوت دارند. وقتی عیار ثابت می‌ماند و تناژ حدود ۳۷ درصد بیشتر می‌شود، تفاوت احتمالاً از گسترش محدوده یا داده‌های حفاری بیشتر ناشی شده است تا تغییر عیار حد. رقم پیت نهایی «کانسنگ داخل پیت» است و با منبع درجا مقایسهٔ مستقیم ندارد.</p>
<p>گزارش کالکوسیت و کوولیت–دیژنیت هیپوژن در پهنهٔ پتاسیک عمیق یعنی حضور کالکوسیت به‌تنهایی معیار پهنهٔ غنی‌شدهٔ سوپرژن نیست. دامنه‌بندی پهنهٔ غنی‌شده باید بر پایهٔ لاگ اکسایش و موقعیت نسبت به پهنهٔ شسته‌شده انجام شود، نه فقط کانی‌شناسی مس.</p>'''),
  ]),
 en=dict(
  name='Miduk', province='Kerman', type_short='Porphyry Cu–Mo',
  title='Miduk Porphyry Copper Deposit, Shahr-e Babak: Geology, Age and Resources | Ali Alinaghi',
  h1='Miduk porphyry copper deposit: geology and resources',
  desc='The Miduk porphyry copper deposit in Shahr-e Babak County, Kerman: two Miocene intrusive phases, Re–Os age, alteration and enrichment zones, and published resource figures with sources.',
  lede='Miduk, about 40 km northeast of Shahr-e Babak, is one of the main deposits of the Kerman porphyry belt, and its mineralisation has been dated precisely by Re–Os on molybdenite.',
  coord_note='The USGS point is about 0.9 km from this one[[usgs9319]].',
  facts=[
   ('aka', 'Meiduk, Meydouk; Persian: میدوک'),
   ('loc', 'Kerman Province; Shahr-e Babak County, 40–42 km northeast of Shahr-e Babak[[mindat205749]]'),
   ('comm', 'Copper and molybdenum with gold and silver; USGS grades 0.61% Cu, 0.007% Mo, 1.8 g/t Ag[[usgs9319]]'),
   ('type', 'Miocene porphyry Cu–Mo'),
   ('belt', 'Kerman porphyry belt; Miduk’s Re–Os age marks “the main stage of magmatism and porphyry copper formation” in the belt[[taghipour2008]]'),
   ('host', 'Eocene andesitic–basaltic volcanics cut by two Miocene calc-alkaline intrusive phases, P1 and P2[[taghipour2008]]'),
   ('age', 'Molybdenite Re–Os 12.23 ± 0.07 Ma, matching the P2 zircon age[[taghipour2008]]; USGS gives U–Pb 12.5 ± 0.1 Ma[[usgs9319]]'),
   ('op', 'NICICO; open pit with an expansion USGS listed for 2015[[usgs9319]]; complex commissioned in December 2004 (low–medium confidence)[[porter986]]'),
  ],
  sections=[
   ('Geological setting and age', '''<p>Miduk lies in the Kerman porphyry belt. The host rocks are Eocene andesitic–basaltic volcanics intruded by two Miocene calc-alkaline phases, P1 and P2. Molybdenite gives a Re–Os age of 12.23 ± 0.07 Ma, which matches the zircon age of P2, the second mineralising phase[[taghipour2008]]. USGS gives a U–Pb age of 12.5 ± 0.1 Ma[[usgs9319]]. Together with the Sarcheshmeh ages, these results bracket mineralisation in this part of the Kerman belt at about 12–13.6 Ma.</p>
<p>The straight-line distance from Miduk to Sarcheshmeh is about 85 km, matching the figure in a published abstract[[sid32327]]; the 130–132 km quoted in some Persian papers is probably the road distance.</p>'''),
   ('Alteration and mineralisation', '''<p>Potassic, phyllic and propylitic zones form concentric shells[[jpgu2009]]. The main-stage assemblage is chalcopyrite–magnetite–anhydrite. Deep potassic zones carry hypogene chalcocite and covellite–digenite, and leached, oxide and supergene-sulphide zones are also present[[scirep2022]]. Boomeri et al. (2009) studied the geochemistry of the potassic zone[[boomeri2009]].</p>'''),
   ('Published resource figures', '''{{res}}<p>The same final-pit study estimated a 27-year life and a pit deepened by 360 m[[civilica557987]]. Older papers and reviews give other figures whose primary sources could not be traced in the sources reviewed.</p>'''),
  ],
  expert=[
   ('Two figures, two bases', '''<p>The USGS figure (176 Mt at 0.61% Cu, about 1.1 Mt contained copper) and the final-pit figure (241 Mt of ore at the same grade, about 1.5 Mt copper) share a grade but not a tonnage. When grade holds and tonnage rises by about 37%, the difference more likely comes from a larger footprint or more drilling than from a change in cut-off grade. The final-pit number is ore inside a pit design and is not directly comparable with an in-situ resource.</p>
<p>Hypogene chalcocite and covellite–digenite in the deep potassic zone mean that chalcocite alone does not define the supergene enrichment blanket. The enriched domain should be built from oxidation logging and its position relative to the leached cap, not from copper mineralogy alone.</p>'''),
  ]),
)

KAHANG = dict(
 slug='kahang', commodity='cu', ntype='porphyry', metal='cu',
 lat=32.93167, lon=52.48056, coord_src='Mindat', coord_cite='mindat_kahang', coord_conf='M',
 published=P, updated=P, related=['dalli', 'miduk', 'sarcheshmeh'],
 links={'art': ['exploration-stages-iran', 'resources-vs-reserves'], 'svc': ['remote-sensing', 'mineral-exploration'], 'tools': ['grade-converter']},
 res=[
  R('۴۰ میلیون تن قطعی با حدود ۰٫۵۳٪ مس و ۰٫۰۲٪ مولیبدن؛ کل حدود ۱۲۰ میلیون تن (عیار کل ذکر نشده)', '40 Mt proven @ about 0.53% Cu, 0.02% Mo; about 120 Mt in total (grade of the total not given)',
    'گزارش شرکتی ۲۰۰۷، به نقل مقاله‌ای در ۲۰۱۷', '2007 company report, cited in a 2017 paper', ['jeg2017_kahang'], 'ML', calc=[(40, .53)]),
 ],
 fa=dict(
  name='کهنگ', province='اصفهان', type_short='مس–مولیبدن پورفیری',
  title='کانسار مس پورفیری کهنگ اردستان: زمین‌شناسی، دگرسانی و اکتشاف | علی علینقی',
  h1='زمین‌شناسی کانسار مس پورفیری کهنگ',
  desc='کانسار مس–مولیبدن پورفیری کهنگ در شهرستان اردستان اصفهان: کشف با تصاویر لندست، سن‌سنجی U–Pb و Re–Os، پهنه‌های دگرسانی و ذخیرهٔ منتشرشده.',
  lede='کهنگ، حدود ۷۳ کیلومتری شمال‌شرق اصفهان، نمونهٔ روشنی از کشف یک کانسار پورفیری با دورسنجی است: پهنه‌های دگرسانی آن در سال ۱۳۸۲ روی تصاویر ماهواره‌ای لندست شناسایی شد و کانسار هنوز در مرحلهٔ اکتشاف است.',
  coord_note='مختصات از درجه–دقیقه–ثانیهٔ Mindat تبدیل شده است. روستای کهنگ حدود ۱٫۲ کیلومتر با این نقطه فاصله دارد[[wp_kahang]]. پروسپکت «قهان» در استان مرکزی، که در پایگاه USGS آمده، کانسار دیگری است[[usgs9261]].',
  facts=[
   ('aka', 'Kahang؛ «گرگر» (Gor Gor)'),
   ('loc', 'استان اصفهان؛ شهرستان اردستان (Mindat)، حدود ۷۳ کیلومتری شمال‌شرق اصفهان[[jeg2017_kahang]]'),
   ('comm', 'مس و مولیبدن[[jeg2017_kahang]]؛ احتمال طلا (اطمینان متوسط)[[porter1711]]'),
   ('type', 'مس–مولیبدن پورفیری'),
   ('belt', 'بخش مرکزی کمان ماگمایی ارومیه–دختر[[babazadeh2025]]'),
   ('host', 'سنگ‌های آتشفشانی داسیتی–ریوداسیتی و استوک‌های گرانیتی–گرانودیوریتی[[jeg2017_kahang]]'),
   ('age', 'زیرکن U–Pb حدود ۱۵ میلیون سال و Re–Os مولیبدنیت ۱۴٫۵ میلیون سال؛ عدم قطعیت در چکیده ذکر نشده[[babazadeh2025]]'),
   ('op', 'مرحلهٔ اکتشاف؛ پروانه، بهره‌بردار یا تولیدی در منابع بررسی‌شده یافت نشد'),
  ],
  sections=[
   ('کشف با دورسنجی', '''<p>کهنگ در سال ۱۳۸۲ با نقشه‌برداری پهنه‌های دگرسانی روی تصاویر ماهواره‌ای لندست شناسایی شد[[iut_kahang]]. دگرسانی‌های فیلیک و آرژیلیک کانی‌های رسی و سرسیت دارند که در باندهای فروسرخ موج‌کوتاه جذب طیفی ویژه‌ای نشان می‌دهند و به همین دلیل در تصاویر ماهواره‌ای قابل تشخیص‌اند. کهنگ نمونهٔ خوبی از نقش دورسنجی در مرحلهٔ پی‌جویی کانسارهای پورفیری است؛ روش کار در صفحهٔ <a href="/services/remote-sensing/">دورسنجی و نقشه‌برداری دگرسانی</a> توضیح داده شده است.</p>'''),
   ('جایگاه زمین‌شناسی و سن', '''<p>کهنگ در بخش مرکزی کمان ماگمایی ارومیه–دختر قرار دارد. Babazadeh و همکاران (۲۰۲۵) سن زیرکن U–Pb حدود ۱۵ میلیون سال و سن Re–Os مولیبدنیت ۱۴٫۵ میلیون سال را گزارش کرده‌اند[[babazadeh2025]] که با پالس میوسن میانی (۱۷ تا ۱۵ میلیون سال) در کمان میانی هم‌خوان است[[aghazadeh2015]]. آن‌ها کانی‌سازی را به گسیختگی ورقهٔ فرورونده در گذار از مرحلهٔ هم‌برخوردی به پس‌برخوردی، و منشأ فلزات را به گوشتهٔ دوباره غنی‌شدهٔ زیر قاره نسبت می‌دهند[[babazadeh2025]]. یک مطالعهٔ سن‌سنجی ⁴⁰Ar/³⁹Ar نیز در Ore Geology Reviews منتشر شده است[[ogr_kahang]].</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>پهنه‌های دگرسانی فیلیک، آرژیلیک حدواسط و پروپیلیتیک گزارش شده و پهنهٔ پتاسیک گزارش نشده است. کانی‌سازی به‌صورت پراکنده و استوک‌ورک است. پهنهٔ اکسیدی مالاکیت، آزوریت و اکسیدهای آهن دارد، پهنهٔ سوپرژن کالکوسیت و کوولیت، و پهنهٔ هیپوژن کالکوپیریت، پیریت، مگنتیت و بورنیت. مقدار δ³⁴S سولفیدها از −۱٫۶ تا +۲٫۱ در هزار است[[jeg2017_kahang]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
  ],
  expert=[
   ('یادداشت اکتشافی و رده‌بندی', '''<p><b>پهنهٔ پتاسیک:</b> در سامانه‌های پورفیری، دگرسانی فیلیک و آرژیلیک معمولاً بخش‌های بالایی و حاشیه‌ای را می‌پوشاند و دگرسانی پتاسیک در هسته و عمق قرار دارد. گزارش نشدن پهنهٔ پتاسیک در کهنگ ممکن است نشان دهد که حفاری‌ها هنوز به هستهٔ سامانه نرسیده‌اند؛ آزمودن این فرض با حفاری عمیق‌تر و داده‌های ژئوفیزیکی (قطبش القایی و مغناطیس‌سنجی) ارزش اکتشافی دارد.</p>
<p><b>«ذخیرهٔ قطعی» در مرحلهٔ اکتشاف:</b> رقم ۴۰ میلیون تن قطعی بر پایهٔ رده‌بندی ایرانی است. در کد JORC، ذخیرهٔ قطعی (Proved Ore Reserve) فقط پس از اعمال عوامل تعدیل‌کننده در یک مطالعهٔ پیش‌امکان‌سنجی یا امکان‌سنجی معنا دارد؛ برای کانساری که هنوز در مرحلهٔ اکتشاف است، معادل نزدیک‌تر «منبع» است، نه «ذخیره». مقالهٔ <a href="/articles/resources-vs-reserves/">تفاوت منابع و ذخایر</a> این موضوع را با جزئیات توضیح می‌دهد.</p>'''),
  ]),
 en=dict(
  name='Kahang', province='Isfahan', type_short='Porphyry Cu–Mo',
  title='Kahang Porphyry Copper Deposit, Ardestan: Geology, Alteration and Exploration | Ali Alinaghi',
  h1='Kahang porphyry copper deposit: geology and exploration',
  desc='The Kahang porphyry Cu–Mo deposit in Ardestan County, Isfahan: discovery from Landsat imagery, U–Pb and Re–Os ages, alteration zones and the published resource figure.',
  lede='Kahang, about 73 km northeast of Isfahan, is a clear example of a porphyry deposit found by remote sensing: its alteration zones were mapped on Landsat satellite images in 1382 SH (2003/04), and the deposit is still at the exploration stage.',
  coord_note='Converted from Mindat’s degree–minute–second values. Kahang village is about 1.2 km from this point[[wp_kahang]]. The “Qahan” prospect in Markazi Province, listed by USGS, is a different deposit[[usgs9261]].',
  facts=[
   ('aka', 'Gor Gor; Persian: کهنگ'),
   ('loc', 'Isfahan Province; Ardestan County (Mindat), about 73 km northeast of Isfahan[[jeg2017_kahang]]'),
   ('comm', 'Copper and molybdenum[[jeg2017_kahang]]; possible gold (medium confidence)[[porter1711]]'),
   ('type', 'Porphyry Cu–Mo'),
   ('belt', 'Central Urumieh–Dokhtar magmatic arc[[babazadeh2025]]'),
   ('host', 'Dacitic–rhyodacitic volcanics and granitic–granodioritic stocks[[jeg2017_kahang]]'),
   ('age', 'Zircon U–Pb about 15 Ma and molybdenite Re–Os 14.5 Ma; uncertainties not given in the abstract[[babazadeh2025]]'),
   ('op', 'Exploration stage; no licence, operator or production found in the sources reviewed'),
  ],
  sections=[
   ('Discovery by remote sensing', '''<p>Kahang was identified in 1382 SH (2003/04) by mapping alteration zones on Landsat satellite images[[iut_kahang]]. Phyllic and argillic alteration contain clays and sericite with diagnostic absorption features in the shortwave infrared, which is why they can be picked out from orbit. Kahang is a good example of the role of remote sensing at the prospecting stage of porphyry exploration; the workflow is described on the <a href="/en/services/remote-sensing/">remote sensing and alteration mapping</a> page.</p>'''),
   ('Geological setting and age', '''<p>Kahang lies in the central Urumieh–Dokhtar magmatic arc. Babazadeh et al. (2025) report a zircon U–Pb age of about 15 Ma and a molybdenite Re–Os age of 14.5 Ma[[babazadeh2025]], consistent with the middle-Miocene (17–15 Ma) pulse of the middle arc[[aghazadeh2015]]. They relate mineralisation to slab break-off during the syn- to post-collisional transition and derive the metals from re-enriched mantle beneath the continent[[babazadeh2025]]. A ⁴⁰Ar/³⁹Ar study has also been published in Ore Geology Reviews[[ogr_kahang]].</p>'''),
   ('Alteration and mineralisation', '''<p>Phyllic, intermediate-argillic and propylitic zones are reported; no potassic zone has been described. Ore is disseminated and stockwork. The oxide zone carries malachite, azurite and iron oxides, the supergene zone chalcocite and covellite, and the hypogene zone chalcopyrite, pyrite, magnetite and bornite. Sulphide δ³⁴S ranges from −1.6 to +2.1‰[[jeg2017_kahang]].</p>'''),
   ('Published resource figure', '''{{res}}'''),
  ],
  expert=[
   ('Exploration and classification note', '''<p><b>The missing potassic zone:</b> in porphyry systems, phyllic and argillic alteration usually cover the upper and outer parts while potassic alteration sits in the core and at depth. The absence of a reported potassic zone at Kahang may mean drilling has not yet reached the core of the system; testing that idea with deeper holes and geophysics (induced polarisation and magnetics) has exploration value.</p>
<p><b>“Proven reserve” at the exploration stage:</b> the 40 Mt “proven” figure uses the Iranian classification. Under the JORC Code, a Proved Ore Reserve exists only after modifying factors have been applied in a pre-feasibility or feasibility study; for a deposit still being explored, the closer equivalent is a resource, not a reserve. The <a href="/en/articles/resources-vs-reserves/">resources vs reserves</a> article explains the difference in detail.</p>'''),
  ]),
)

SUNGUN = dict(
 slug='sungun', commodity='cu', ntype='porphyry', metal='cu',
 lat=38.6948, lon=46.7028, coord_src='USGS', coord_cite='usgs9247', coord_conf='MH',
 published=P, updated=P, related=['masjed-daghi', 'sarcheshmeh', 'miduk'], links=LINKS_CU,
 res=[
  R('۸۴۶ میلیون تن با ۰٫۶٪ مس و ۰٫۰۲۴٪ مولیبدن', '846 Mt @ 0.6% Cu, 0.024% Mo', 'USGS، اوایل دههٔ ۲۰۱۰', 'USGS, early 2010s',
    ['usgs9247'], 'M', calc=[(846, .6)], lab=('USGS (دههٔ ۲۰۱۰)', 'USGS (2010s)')),
  R('۸۵۰ میلیون تن با ۰٫۶۲٪ مس و ۰٫۰۱٪ مولیبدن', '850 Mt @ 0.62% Cu, 0.01% Mo', 'Mindat، به نقل از فصلی در نشریهٔ ویژهٔ ۱۹ انجمن زمین‌شناسان اقتصادی (SEG)', 'Mindat, citing a chapter in SEG Special Publication 19',
    ['mindat205026'], 'M', calc=[(850, .62)], lab=('Mindat / SEG', 'Mindat / SEG')),
  R('۷۹۰ میلیون تن قطعی و احتمالی با ۰٫۶۳٪ مس', '790 Mt proven + probable @ 0.63% Cu', 'پروانهٔ قبلی، به گفتهٔ شرکت ملی صنایع مس در دی ۱۴۰۳', 'Previous licence, as stated by NICICO in December 2024',
    ['shahrekhabar_sungun'], 'MH', calc=[(790, .63)], lab=('پروانهٔ قبلی', 'Previous licence')),
  R('۲٬۴۹۰ میلیون تن قطعی و احتمالی با ۰٫۵۳٪ مس', '2,490 Mt proven + probable @ 0.53% Cu', 'گواهی کشف ۸ دی ۱۴۰۳، رده‌بندی ایرانی (غیر CRIRSCO)', 'Discovery certificate of 28 December 2024, Iranian system (not CRIRSCO)',
    ['shahrekhabar_sungun', 'boursepress_sungun'], 'MH', calc=[(2490, .53)], lab=('گواهی کشف ۱۴۰۳', '2024 certificate')),
 ],
 fa=dict(
  name='سونگون', province='آذربایجان شرقی', type_short='مس–مولیبدن پورفیری',
  title='کانسار مس پورفیری سونگون ورزقان: زمین‌شناسی، دگرسانی و ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار مس پورفیری سونگون',
  desc='کانسار مس پورفیری سونگون در شهرستان ورزقان آذربایجان شرقی: سن‌سنجی زیرکن و Re–Os، دگرسانی و اسکارن، و گواهی کشف دی ۱۴۰۳ با تحلیل مس محتوا.',
  lede='سونگون در کمربند ارسباران معدن روباز مس فعالی است که Mindat آن را بزرگ‌ترین معدن روباز مس ایران توصیف کرده است. گواهی کشف تازهٔ آن در دی ۱۴۰۳ رقم ذخیره را حدود سه برابر کرد؛ این صفحه آن رقم را کنار ارقام قبلی می‌گذارد و مس محتوای هرکدام را محاسبه می‌کند.',
  coord_note='نقطهٔ Mindat حدود ۰٫۷ کیلومتر با این نقطه فاصله دارد[[mindat205026]].',
  facts=[
   ('aka', 'Songun'),
   ('loc', 'استان آذربایجان شرقی؛ شهرستان ورزقان[[usgs9247]]'),
   ('comm', 'مس، با مولیبدن به‌عنوان محصول جانبی[[mindat205026]]'),
   ('type', 'مس–مولیبدن پورفیری با اسکارن‌های همبری کوچک[[aghazadeh2015]]'),
   ('belt', 'کمربند ارسباران، مرحلهٔ میوسن پیشین (۲۲ تا ۲۰ میلیون سال)[[aghazadeh2015]]؛ پس‌برخوردی تفسیر شده است[[egu2016]]'),
   ('host', 'استوک پورفیری II (گرانودیوریت، کوارتز مونزونیت، گرانیت) درون آندزیت‌ها؛ اسکارن در همبری با کربنات‌های ناخالص کرتاسهٔ پسین[[jaes_sungun]]'),
   ('age', 'زیرکن U–Pb (SHRIMP): ۲۰٫۶۹ ± ۰٫۳۷ میلیون سال برای پورفیری اصلی و ۲۷٫۶۵ ± ۰٫۵۱ برای آندزیت میزبان[[hassanpour2015]]؛ Re–Os مولیبدنیت: ۲۲٫۹ ± ۰٫۲ تا ۲۱٫۷ ± ۰٫۲ میلیون سال[[simmonds2017]]'),
   ('op', 'شرکت ملی صنایع مس ایران؛ معدن روباز در حال بهره‌برداری[[mindat205026]]؛ گواهی کشف تازه در ۸ دی ۱۴۰۳ (۲۸ دسامبر ۲۰۲۴)[[shahrekhabar_sungun]]'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی و سن', '''<p>سونگون به مرحلهٔ میوسن پیشین (۲۲ تا ۲۰ میلیون سال) کمربند ارسباران تعلق دارد[[aghazadeh2015]] و در یک چکیدهٔ علمی پس‌برخوردی تفسیر شده است[[egu2016]]. کانی‌سازی به استوک پورفیری II، با ترکیب گرانودیوریت، کوارتز مونزونیت و گرانیت، وابسته است که در آندزیت‌ها نفوذ کرده و در همبری با کربنات‌های ناخالص کرتاسهٔ پسین اسکارن ساخته است[[jaes_sungun]]. Hezarkhani و Williams-Jones (۱۹۹۸) عوامل کنترل‌کنندهٔ دگرسانی و کانی‌سازی را در این کانسار بررسی کرده‌اند[[hezarkhani1998]].</p>
<p>سن‌ها یک ناسازگاری آموزنده دارند. سن زیرکن U–Pb پورفیری اصلی ۲۰٫۶۹ ± ۰٫۳۷ میلیون سال و سن آندزیت میزبان ۲۷٫۶۵ ± ۰٫۵۱ میلیون سال است[[hassanpour2015]]، اما سن Re–Os مولیبدنیت ۲۲٫۹ تا ۲۱٫۷ میلیون سال، یعنی قدیمی‌تر از پورفیری اصلی، به دست آمده است[[simmonds2017]]. کانسنگ نمی‌تواند از سنگ میزبان خود قدیمی‌تر باشد؛ پس یا بخشی از کانی‌سازی به فازهای نفوذی قدیمی‌تر وابسته است یا یکی از دو روش سوگیری دارد. یک چکیدهٔ سال ۲۰۱۶ سن زیرکن استوک میزبان را تا حدود ۲۲٫۵ میلیون سال گزارش کرده است[[egu2016]].</p>'''),
   ('دگرسانی، کانی‌سازی و اسکارن', '''<p>پهنه‌های دگرسانی پتاسیک، پتاسیک–فیلیک، فیلیک و پروپیلیتیک (و به‌طور محلی آرژیلیک) و نیز پهنه‌های شسته‌شده، سوپرژن و هیپوژن تفکیک شده‌اند و مس بیشتر با دگرسانی پتاسیک همراه است[[sungun_domaining]]. کانی‌سازی هیپوژن شامل کالکوپیریت پراکنده همراه با پیریت، بورنیت و مولیبدنیت است و کالکوسیت و کوولیت در پهنهٔ سوپرژن دیده می‌شوند[[hezarkhani1998]]. در اسکارن، گارنت، دیوپسید و اپیدوت با کالکوپیریت، اسفالریت، گالن و مگنتیت همراه‌اند[[jaes_sungun]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>گواهی کشف دی ۱۴۰۳ بر پایهٔ رده‌بندی ایرانی «قطعی و احتمالی» صادر شده و با رده‌بندی‌های هم‌راستا با CRIRSCO، مانند JORC، هم‌ارز نیست[[shahrekhabar_sungun]][[boursepress_sungun]].</p>'''),
  ],
  expert=[
   ('سه برابر شدن تناژ و ۲٫۶۵ برابر شدن مس محتوا', '''<p>گواهی کشف دی ۱۴۰۳ تناژ قطعی و احتمالی را از ۷۹۰ به ۲٬۴۹۰ میلیون تن رساند، درحالی‌که عیار از ۰٫۶۳ به ۰٫۵۳ درصد، یعنی ۱۶ درصد، کاهش یافت. مس محتوا از حدود ۵٫۰ به ۱۳٫۲ میلیون تن، یعنی حدود ۲٫۶۵ برابر، افزایش یافته است. اگر رقم قبلی بخشی از رقم تازه باشد، ۱٬۷۰۰ میلیون تن افزوده حدود ۸٫۲ میلیون تن مس دارد؛ یعنی عیار میانگین حدود ۰٫۴۸ درصد، که از میانگین قبلی کمتر است. چنین الگویی با پایین آمدن عیار حد یا بزرگ‌تر شدن پوستهٔ پیت سازگار است، اما مبنای گواهی منتشر نشده است.</p>
<p>ارقام قدیمی‌تر USGS و Mindat (۸۴۶ و ۸۵۰ میلیون تن) به ۵٫۱ تا ۵٫۳ میلیون تن مس می‌رسند و با رقم پروانهٔ قبلی هم‌خوان‌اند. برای داوری دربارهٔ رقم تازه باید عیار حد، روش تخمین، فاصلهٔ حفاری و معیار رده‌بندی آن روشن شود؛ بخش کم‌عیارتر افزوده‌شده به قیمت مس و هزینه‌ها حساس‌تر است.</p>'''),
  ]),
 en=dict(
  name='Sungun', province='East Azerbaijan', type_short='Porphyry Cu–Mo',
  title='Sungun Porphyry Copper Deposit, Varzaqan: Geology, Alteration and Resources | Ali Alinaghi',
  h1='Sungun porphyry copper deposit: geology and resources',
  desc='The Sungun porphyry copper deposit in Varzaqan County, East Azerbaijan: zircon and Re–Os ages, alteration and skarn, and the December 2024 discovery certificate with a contained-copper check.',
  lede='Sungun, in the Arasbaran belt, is an operating open-pit copper mine that Mindat describes as Iran’s largest. A new discovery certificate in December 2024 roughly tripled its reported tonnage; this page sets that figure beside the earlier ones and works out the contained copper in each.',
  coord_note='The Mindat point is about 0.7 km from this one[[mindat205026]].',
  facts=[
   ('aka', 'Songun; Persian: سونگون'),
   ('loc', 'East Azerbaijan Province; Varzaqan County[[usgs9247]]'),
   ('comm', 'Copper, with molybdenum as a by-product[[mindat205026]]'),
   ('type', 'Porphyry Cu–Mo with minor contact skarns[[aghazadeh2015]]'),
   ('belt', 'Arasbaran belt, early-Miocene stage (22–20 Ma)[[aghazadeh2015]]; interpreted as post-collisional[[egu2016]]'),
   ('host', 'Porphyry Stock II (granodiorite, quartz monzonite, granite) in andesites; skarn where it meets Late Cretaceous impure carbonates[[jaes_sungun]]'),
   ('age', 'Zircon U–Pb (SHRIMP) 20.69 ± 0.37 Ma for the main porphyry and 27.65 ± 0.51 Ma for the host andesite[[hassanpour2015]]; molybdenite Re–Os 22.9 ± 0.2 to 21.7 ± 0.2 Ma[[simmonds2017]]'),
   ('op', 'NICICO; operating open pit[[mindat205026]]; new discovery certificate dated 28 December 2024 (8 Dey 1403)[[shahrekhabar_sungun]]'),
  ],
  sections=[
   ('Geological setting and age', '''<p>Sungun belongs to the early-Miocene (22–20 Ma) stage of the Arasbaran belt[[aghazadeh2015]] and has been interpreted as post-collisional[[egu2016]]. Mineralisation is related to Porphyry Stock II — granodiorite, quartz monzonite and granite — which intrudes andesites and formed skarn against Late Cretaceous impure carbonates[[jaes_sungun]]. Hezarkhani and Williams-Jones (1998) studied the controls on alteration and mineralisation[[hezarkhani1998]].</p>
<p>The ages contain an instructive conflict. The main porphyry gives a zircon U–Pb age of 20.69 ± 0.37 Ma and the host andesite 27.65 ± 0.51 Ma[[hassanpour2015]], yet molybdenite gives Re–Os ages of 22.9–21.7 Ma — older than the main porphyry[[simmonds2017]]. Ore cannot be older than its host intrusion, so either earlier intrusive phases host part of it or one of the methods is biased. A 2016 abstract cites host-stock zircon ages back to about 22.5 Ma[[egu2016]].</p>'''),
   ('Alteration, mineralisation and skarn', '''<p>Potassic, potassic–phyllic, phyllic and propylitic (locally argillic) zones, and leached, supergene and hypogene zones, have been distinguished, with copper tied mostly to potassic alteration[[sungun_domaining]]. Hypogene ore is disseminated chalcopyrite with pyrite, bornite and molybdenite, and chalcocite and covellite occur in the supergene zone[[hezarkhani1998]]. The skarn contains garnet, diopside and epidote with chalcopyrite, sphalerite, galena and magnetite[[jaes_sungun]].</p>'''),
   ('Published resource figures', '''{{res}}<p>The December 2024 certificate uses the Iranian “proven and probable” («قطعی و احتمالی») classification, which is not equivalent to CRIRSCO-aligned systems such as JORC[[shahrekhabar_sungun]][[boursepress_sungun]].</p>'''),
  ],
  expert=[
   ('Tonnage tripled, contained copper up 2.65-fold', '''<p>The December 2024 certificate raised proven-plus-probable tonnage from 790 to 2,490 Mt while grade fell from 0.63% to 0.53% Cu, a 16% drop. Contained copper rose from about 5.0 to 13.2 Mt, roughly 2.65-fold. If the earlier figure sits inside the new one, the added 1,700 Mt carries about 8.2 Mt of copper — an average of about 0.48% Cu, below the previous average. That fits a lower cut-off grade or a larger pit shell, but the basis of the certificate has not been published.</p>
<p>The older USGS and Mindat figures (846 and 850 Mt) imply 5.1–5.3 Mt of copper, consistent with the previous licence. Judging the new figure requires its cut-off grade, estimation method, drill spacing and classification criteria; the lower-grade increment is more sensitive to copper price and costs.</p>'''),
  ]),
)

MASJED_DAGHI = dict(
 slug='masjed-daghi', commodity='cu', ntype='porphyry', metal='cu',
 lat=38.8772, lon=45.9386, coord_src='USGS', coord_cite='usgs9224', coord_conf='M',
 published=P, updated=P, related=['sungun', 'dalli', 'sarcheshmeh'], links=LINKS_CU,
 res=[
  R('۲۰۴ میلیون تن با ۰٫۳۴٪ مس (حدود ۶۹۰ هزار تن مس)', '204 Mt @ 0.34% Cu (about 690 kt Cu)', 'USGS، اوایل دههٔ ۲۰۱۰؛ عیار طلای این رکورد نقل نشده (متن را ببینید)', 'USGS, early 2010s; the gold grade in this record is not reproduced (see text)',
    ['usgs9224'], 'M', calc=[(204, .34)], lab=('USGS', 'USGS')),
  R('۲۰۴ میلیون تن با ۰٫۳٪ مس و ۳۲۰ ppb طلا', '204 Mt @ 0.3% Cu, 320 ppb Au', 'نقل‌شده در مقاله‌ای دربارهٔ کانسار علی‌جواد', 'Cited in a paper on the Ali Javad deposit',
    ['scirp_md'], 'ML', calc=[(204, .3)], lab=('مقالهٔ علی‌جواد', 'Ali Javad paper')),
  R('۸۰ میلیون تن قطعی با ۰٫۴۲٪ مس و ۱۲۵ میلیون تن احتمالی با ۰٫۲۳٪ مس', '80 Mt proven @ 0.42% Cu + 125 Mt probable @ 0.23% Cu', 'گزارش خبری فارسی، حدود ۱۳۹۸–۱۳۹۹', 'Persian news report, about 2019–20',
    ['metalonline_md'], 'L', calc=[(80, .42), (125, .23)], lab=('خبر ۱۳۹۸–۹۹', 'News, 2019–20')),
  R('۲۷۲ میلیون تن با ۰٫۳۱٪ مس و ۰٫۶ ppm طلا', '272 Mt @ 0.31 wt% Cu, 0.6 ppm Au', 'بر پایهٔ گمانه‌ها؛ منبعی از ۲۰۱۶ که در مقاله‌های ۲۰۲۲ و ۲۰۲۵ نقل شده', 'Drill-hole based; a 2016 source cited in 2022 and 2025 papers',
    ['econg48126', 'rahnama2025'], 'M', calc=[(272, .31)], lab=('داده‌های حفاری (۲۰۱۶)', 'Drill-hole based (2016)')),
 ],
 fa=dict(
  name='مسجد داغی', province='آذربایجان شرقی', type_short='مس–طلا پورفیری و اپی‌ترمال',
  title='کانسار مس–طلای پورفیری مسجد داغی جلفا: زمین‌شناسی، سن و ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار مس–طلای پورفیری مسجد داغی',
  desc='کانسار مس–طلای پورفیری مسجد داغی در منطقهٔ آزاد ارس، شرق جلفا: سن مورد اختلاف، دگرسانی، رگه‌های طلای اپی‌ترمال سولفید بالا و ارقام ذخیرهٔ منتشرشده.',
  lede='مسجد داغی، حدود ۳۵ کیلومتری شرق جلفا در کنار رود ارس، یک سامانهٔ پورفیری مس–طلا–مولیبدن است که رگه‌های طلای اپی‌ترمال سولفید بالا پس از آن تشکیل شده‌اند. سن کانی‌سازی و وضعیت بهره‌برداری آن هنوز محل اختلاف است.',
  coord_note='نقطهٔ Mindat برای این کانسار دقیقاً یک درجه طول جغرافیایی (حدود ۸۵ کیلومتر) شرق‌تر از نقطهٔ USGS است و با توصیف «۳۵ کیلومتری شرق جلفا» نمی‌خواند؛ Mindat آن را ذیل شهرستان‌های چاراویماق و کلیبر هم آورده است[[mindat25154]].',
  facts=[
   ('aka', 'Masjeddaghi، مسجدداغی'),
   ('loc', 'استان آذربایجان شرقی؛ شهرستان جلفا (فقط از عنوان‌های فارسی استنباط می‌شود)، حدود ۳۵ کیلومتری شرق جلفا کنار رود ارس، در منطقهٔ آزاد ارس[[rahnama2025]]'),
   ('comm', 'مس و طلا به‌عنوان مواد اصلی (USGS)[[usgs9224]]؛ مولیبدن جزئی و رگه‌های طلای اپی‌ترمال[[ebrahimi2021]]'),
   ('type', 'مس–طلا–مولیبدن پورفیری و پس از آن رگه‌های طلای اپی‌ترمال سولفید بالا از سیال ماگمایی مشابه[[ebrahimi2021]]'),
   ('belt', 'پهنهٔ البرز–آذربایجان، جنوب‌غرب کمربند ارسباران[[rahnama2025]]'),
   ('host', 'کوارتز دیوریت پورفیری و کوارتز مونزودیوریت–دیوریت درون آتشفشانی‌های آندزیتی ائوسن[[econg48126]]'),
   ('age', 'مورد اختلاف: زیرکن U–Pb ۵۴٫۱ ± ۱٫۵ میلیون سال (ائوسن)[[geoscience2021]] در برابر میوسن پیشین[[aghazadeh2015]][[ebrahimi2021]]؛ سن Re–Os در دسترس نیست'),
   ('op', 'مالک در پایگاه دادهٔ صبا: شرکت ملی صنایع مس[[saba_md]]؛ در دسامبر ۲۰۲۲ منتظر مجوز سازمان حفاظت محیط زیست بود[[inodu2022]]؛ توصیف «در حال تولید» در رکورد USGS قدیمی است[[usgs9224]]'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی و سن مورد اختلاف', '''<p>مسجد داغی در پهنهٔ البرز–آذربایجان و جنوب‌غرب کمربند ارسباران قرار دارد[[rahnama2025]]. توده‌های میزبان کوارتز دیوریت پورفیری و کوارتز مونزودیوریت–دیوریت‌اند که در آتشفشانی‌های آندزیتی ائوسن نفوذ کرده‌اند[[econg48126]]. Ebrahimi و همکاران (۲۰۲۱) سامانه را پورفیری مس–طلا–مولیبدن می‌دانند که رگه‌های طلای اپی‌ترمال سولفید بالا از سیال ماگمایی مشابه پس از آن تشکیل شده‌اند[[ebrahimi2021]].</p>
<p>سن کانی‌سازی هنوز محل اختلاف است. یک مطالعه سن زیرکن U–Pb را ۵۴٫۱ ± ۱٫۵ میلیون سال (ائوسن) گزارش کرده است[[geoscience2021]]، درحالی‌که Aghazadeh و همکاران و Ebrahimi و همکاران آن را در میوسن پیشین جای می‌دهند[[aghazadeh2015]][[ebrahimi2021]]. هیچ سن Re–Os مولیبدنیتی برای داوری میان این دو وجود ندارد. اگر سن ائوسن درست باشد، مسجد داغی از پالس‌های اصلی پورفیری ارسباران (۲۹ تا ۲۷ و ۲۲ تا ۲۰ میلیون سال) جدا می‌افتد[[aghazadeh2015]].</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>هستهٔ دگرسانی پتاسیک با فلدسپار پتاسیم، بیوتیت و مگنتیت مشخص می‌شود و پهنه‌های فیلیک، آرژیلیک و پروپیلیتیک و سیلیسی‌شدن محلی آن را دربرگرفته‌اند[[econg48126]]. کانی‌های فلزی کالکوپیریت همراه با مقدار کمی بورنیت، کالکوسیت اولیه، تتراهدریت و اندکی مولیبدنیت‌اند[[civilica1384232]]. پهنهٔ سوپرژن در منابع بررسی‌شده توصیف نشده است.</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>یکی از رکوردهای پایگاه داده، عیار طلایی برای مسجد داغی آورده که چند برابر سایر منابع است و با هیچ‌یک از آن‌ها نمی‌خواند؛ این رقم در اینجا نقل نشده است.</p>'''),
   ('وضعیت بهره‌برداری', '''<p>USGS هنوز مسجد داغی را «در حال تولید، با طرح توسعه‌ای که قرار بود در ۲۰۱۵ کامل شود» توصیف می‌کند[[usgs9224]]. اما در دسامبر ۲۰۲۲ مدیرعامل منطقهٔ آزاد ارس گفت استخراج تنها پس از صدور مجوز سازمان حفاظت محیط زیست آغاز می‌شود[[inodu2022]]. در پایگاه دادهٔ صبا، شرکت ملی صنایع مس مالک معرفی شده است[[saba_md]].</p>'''),
  ],
  expert=[
   ('ارقام ذخیره در کنار هم', '''<p>تفکیک خبری ۸۰ میلیون تن قطعی با ۰٫۴۲٪ مس و ۱۲۵ میلیون تن احتمالی با ۰٫۲۳٪ مس، روی هم ۲۰۵ میلیون تن با عیار میانگین وزنی ۰٫۳۰٪ مس می‌شود؛ یعنی تقریباً همان «۲۰۴ میلیون تن با ۰٫۳٪ مس» که در یک مقاله نقل شده است. هر دو حدود ۰٫۶ میلیون تن مس محتوا دارند. رقم ۲۷۲ میلیون تن بر پایهٔ گمانه‌ها با ۰٫۳۱٪ مس حدود ۰٫۸ میلیون تن مس می‌دهد و احتمالاً محدودهٔ بزرگ‌تری را دربرمی‌گیرد.</p>
<p>اختلاف عیار دو ردهٔ قطعی (۰٫۴۲٪) و احتمالی (۰٫۲۳٪) بزرگ است و احتمالاً بخش احتمالی عمدتاً کانسنگ کم‌عیارتر حاشیهٔ سامانه است، نه فقط بخشی با حفاری کمتر. عیار طلا هم در دو منبع دیگر از ۰٫۳۲ تا ۰٫۶ گرم در تن تغییر می‌کند؛ در کانساری که طلا سهم مهمی از ارزش آن دارد، این اختلاف باید پیش از هر ارزیابی اقتصادی با داده‌های حفاری و کنترل کیفیت آنالیز طلا روشن شود.</p>'''),
  ]),
 en=dict(
  name='Masjed Daghi', province='East Azerbaijan', type_short='Porphyry Cu–Au and epithermal',
  title='Masjed Daghi Porphyry Copper–Gold Deposit, Jolfa: Geology, Age and Resources | Ali Alinaghi',
  h1='Masjed Daghi porphyry copper–gold deposit: geology and resources',
  desc='The Masjed Daghi porphyry Cu–Au deposit in the Aras Free Zone east of Jolfa: contested age, alteration, high-sulphidation epithermal gold veins and published resource figures.',
  lede='Masjed Daghi, about 35 km east of Jolfa on the Aras River, is a porphyry Cu–Au–Mo system overprinted by later high-sulphidation epithermal gold veins. Both its age and its operating status are still disputed.',
  coord_note='Mindat’s point for this deposit sits exactly 1° of longitude (about 85 km) east of the USGS point and contradicts the published “35 km east of Jolfa”; Mindat also files it under Charuymaq and Kaleybar counties[[mindat25154]].',
  facts=[
   ('aka', 'Masjeddaghi; Persian: مسجد داغی'),
   ('loc', 'East Azerbaijan Province; Jolfa County (implied only by Persian titles), about 35 km east of Jolfa on the Aras River, inside the Aras Free Zone[[rahnama2025]]'),
   ('comm', 'Copper and gold as major commodities (USGS)[[usgs9224]]; minor molybdenum and epithermal gold veins[[ebrahimi2021]]'),
   ('type', 'Porphyry Cu–Au–Mo followed by high-sulphidation epithermal gold veins from a similar magmatic fluid[[ebrahimi2021]]'),
   ('belt', 'Alborz–Azarbaijan zone, southwestern Arasbaran belt[[rahnama2025]]'),
   ('host', 'Quartz-diorite porphyry and quartz monzodiorite–diorite intruding Eocene andesitic volcanics[[econg48126]]'),
   ('age', 'Contested: zircon U–Pb 54.1 ± 1.5 Ma (Eocene)[[geoscience2021]] vs early Miocene[[aghazadeh2015]][[ebrahimi2021]]; no Re–Os age'),
   ('op', 'Owner in the Saba database: NICICO[[saba_md]]; awaiting an environmental permit in December 2022[[inodu2022]]; the USGS “in production” status is out of date[[usgs9224]]'),
  ],
  sections=[
   ('Setting and a contested age', '''<p>Masjed Daghi lies in the Alborz–Azarbaijan zone on the southwestern side of the Arasbaran belt[[rahnama2025]]. The host intrusions are quartz-diorite porphyry and quartz monzodiorite–diorite emplaced into Eocene andesitic volcanics[[econg48126]]. Ebrahimi et al. (2021) describe a porphyry Cu–Au–Mo system followed by high-sulphidation epithermal gold veins derived from a similar magmatic fluid[[ebrahimi2021]].</p>
<p>The age is still disputed. One study reports a zircon U–Pb age of 54.1 ± 1.5 Ma (Eocene)[[geoscience2021]], whereas Aghazadeh et al. and Ebrahimi et al. place the system in the early Miocene[[aghazadeh2015]][[ebrahimi2021]]. No molybdenite Re–Os age exists to settle it. If the Eocene age holds, Masjed Daghi falls outside the main Arasbaran porphyry pulses at 29–27 and 22–20 Ma[[aghazadeh2015]].</p>'''),
   ('Alteration and mineralisation', '''<p>A potassic core with K-feldspar, biotite and magnetite is surrounded by phyllic, argillic and propylitic zones with local silicification[[econg48126]]. Ore minerals are chalcopyrite with minor bornite, primary chalcocite, tetrahedrite and a little molybdenite[[civilica1384232]]. No supergene zone is described in the sources reviewed.</p>'''),
   ('Published resource figures', '''{{res}}<p>One database record gives a gold grade for Masjed Daghi several times higher than any other source and consistent with none of them; it is not reproduced here.</p>'''),
   ('Operating status', '''<p>USGS still describes Masjed Daghi as “in production; expansion to be completed in 2015”[[usgs9224]]. In December 2022, however, the Aras Free Zone’s chief executive said mining would start only once the Department of Environment issued a permit[[inodu2022]]. The Saba industrial database lists NICICO as owner[[saba_md]].</p>'''),
  ],
  expert=[
   ('The resource figures side by side', '''<p>A news split of 80 Mt proven at 0.42% Cu plus 125 Mt probable at 0.23% Cu adds up to 205 Mt at a weighted 0.30% Cu — essentially the “204 Mt at 0.3% Cu” cited in a paper. Both contain about 0.6 Mt of copper. The drill-hole-based 272 Mt at 0.31% Cu implies about 0.8 Mt of copper and probably covers a larger volume.</p>
<p>The gap between the proven (0.42%) and probable (0.23%) grades is large, suggesting that the probable part is mainly lower-grade material on the margins of the system rather than simply less-drilled ore. Gold grades in the two other sources range from 0.32 to 0.6 g/t; in a deposit where gold is a major part of the value, that spread needs settling with drill data and gold assay QA/QC before any economic assessment.</p>'''),
  ]),
)

DALLI = dict(
 slug='dalli', commodity='cu', ntype='porphyry', metal='cu',
 lat=34.2719, lon=50.3242, coord_src='USGS', coord_cite='usgs9255', coord_conf='MH',
 published=P, updated=P, related=['kahang', 'masjed-daghi', 'miduk'], links=LINKS_CU,
 res=[
  R('۸ میلیون تن با ۰٫۵٪ مس و ۰٫۷۵ گرم در تن طلا', '8 Mt @ 0.5% Cu, 0.75 g/t Au', 'USGS، در ردهٔ «پروسپکت»، اوایل دههٔ ۲۰۱۰', 'USGS “prospect”, early 2010s',
    ['usgs9255'], 'MH', calc=[(8, .5)], lab=('USGS', 'USGS')),
  R('حدود ۵ میلیون تن قطعی و ۱۲ میلیون تن احتمالی با حدود ۰٫۵٪ مس', 'About 5 Mt proven + 12 Mt probable @ about 0.5% Cu', 'معاون صنعت، معدن و تجارت استان مرکزی، ۶ اسفند ۱۳۹۹', 'Markazi deputy for industry, mine and trade, 24 February 2021',
    ['tasnim_dalli'], 'MH', calc=[(5, .5), (12, .5)], lab=('اسفند ۱۳۹۹', 'Feb 2021')),
 ],
 fa=dict(
  name='دالی', province='مرکزی', type_short='مس–طلا پورفیری',
  title='کانسار مس–طلای پورفیری دالی دلیجان: زمین‌شناسی، دگرسانی و ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار مس–طلای پورفیری دالی',
  desc='کانسار مس–طلای پورفیری دالی در شهرستان دلیجان استان مرکزی: دو مرکز تپهٔ شمالی و جنوبی، پوستهٔ پیریتی، سن آرگون–آرگون و ارقام ذخیرهٔ منتشرشده.',
  lede='دالی، حدود ۴۰ کیلومتری شمال‌غرب دلیجان، یک کانسار پورفیری مس–طلای غنی از طلا در بخش مرکزی کمان ارومیه–دختر است و دو مرکز کانی‌سازی دارد: تپهٔ شمالی و تپهٔ جنوبی.',
  coord_note='نقطهٔ Mindat با نقطهٔ USGS یکسان است و احتمالاً از آن رونویسی شده، نه مستقل[[mindat440464]].',
  facts=[
   ('aka', 'Dali'),
   ('loc', 'استان مرکزی؛ شهرستان دلیجان، حدود ۴۰ کیلومتری شمال‌غرب دلیجان و ۹ کیلومتری شمال‌غرب روستای راوه[[petrology_dalli]]'),
   ('comm', 'مس–طلا (پورفیری غنی از طلا)[[nrr2023]]؛ پروانهٔ سالانه فقط مس را ذکر می‌کند[[tasnim_dalli]]'),
   ('type', 'مس–طلا پورفیری میوسن پیشین با دو مرکز (تپهٔ شمالی و تپهٔ جنوبی)[[ayati2013]][[nrr2023]]'),
   ('belt', 'بخش مرکزی کمان ماگمایی ارومیه–دختر[[ayati2013]]'),
   ('host', 'توده‌های نیمه‌عمیق دیوریتی–گرانودیوریتی (کوارتز دیوریت پورفیری) درون آتشفشانی‌های آندزیتی–داسیتی؛ کانسنگ اصلی در سنگ دیوارهٔ آندزیت پورفیری میان توده و پوستهٔ پیریتی[[nrr2023]]'),
   ('age', 'حداقل سن جایگیری حدود ۲۱ میلیون سال (آرگون–آرگون بیوتیت، بدون پلاتوی سنی قابل اتکا)[[ayati2013]]'),
   ('op', 'پروانهٔ بهره‌برداری ۱۳۹۱ برای حدود ۴۸۰ هزار تن در سال[[tasnim_dalli]]؛ بهره‌بردار در منابع بررسی‌شده شناسایی نشد'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی و سن', '''<p>دالی کانسار پورفیری میوسن پیشین در بخش مرکزی کمان ارومیه–دختر است و دو مرکز کانی‌سازی دارد: تپهٔ شمالی و تپهٔ جنوبی[[ayati2013]][[nrr2023]]. توده‌های نیمه‌عمیق دیوریتی تا گرانودیوریتی (کوارتز دیوریت پورفیری) در آتشفشانی‌های آندزیتی–داسیتی نفوذ کرده‌اند و کانسنگ اصلی در سنگ دیوارهٔ آندزیت پورفیری، میان توده و پوستهٔ پیریتی، قرار دارد[[nrr2023]].</p>
<p>سن‌سنجی آرگون–آرگون بیوتیت حداقل سن جایگیری را حدود ۲۱ میلیون سال نشان می‌دهد، هرچند پلاتوی سنی قابل اتکایی به دست نیامده است[[ayati2013]]. این سن از پالس میوسن میانی (۱۷ تا ۱۵ میلیون سال) که برای کانسارهای کمان میانی تعریف شده قدیمی‌تر است[[aghazadeh2015]]؛ پس یا دالی به پالس جداگانه‌ای تعلق دارد یا سن آرگون–آرگون آن نیاز به بازبینی دارد.</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>هستهٔ پتاسیک، پهنهٔ فیلیک و پهنهٔ پروپیلیتیک در دالی گزارش شده و یک پوستهٔ پیریتی U شکل محدودهٔ کانی‌سازی مهم مس–طلا را در بر می‌گیرد[[nrr2023]]. کالکوپیریت حدود ۴۰ درصد کانی‌های فلزی را تشکیل می‌دهد و همراه پیریت دیده می‌شود؛ طلا در کالکوپیریت و رگه‌های کوارتزی جای دارد[[petrology_dalli]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('وضعیت بهره‌برداری', '''<p>دالی در سال ۱۳۹۱ پروانهٔ بهره‌برداری برای حدود ۴۸۰ هزار تن در سال گرفت که فقط مس را شامل می‌شود. در اسفند ۱۳۹۹ نمایندهٔ دلیجان گفت سازمان حفاظت محیط زیست معدن را آلاینده اعلام کرده است[[tasnim_dalli]]؛ سخنگوی معدن در مقابل گفته است همهٔ مجوزها اخذ شده است[[donya_dalli]]. نام بهره‌بردار در منابع بررسی‌شده شناسایی نشد.</p>'''),
  ],
  expert=[
   ('طلا و پوستهٔ پیریتی در تخمین', '''<p>دو رقم منتشرشده، ۸ میلیون تن با ۰٫۵٪ مس و ۰٫۷۵ گرم در تن طلا (USGS، در ردهٔ «پروسپکت») و ۵ میلیون تن قطعی به‌اضافهٔ ۱۲ میلیون تن احتمالی با حدود ۰٫۵٪ مس (۱۳۹۹)، عیار مس یکسان اما تناژ متفاوت دارند؛ رقم دوم بیش از دو برابر رقم اول است و احتمالاً حاصل اکتشاف بیشتر یا محدودهٔ بزرگ‌تر است.</p>
<p>در رقم ۱۳۹۹ عیار طلا ذکر نشده، درحالی‌که دالی پورفیری غنی از طلاست و رقم USGS به‌تنهایی حدود ۶ تن طلای محتوا دارد. در چنین کانساری، تخمین جداگانهٔ طلا و مدل‌سازی پوستهٔ پیریتی U شکل به‌عنوان مرز دامنه برای تخمین درست ضروری است؛ اگر پروانه فقط مس را دربرگیرد، بخشی از ارزش کانسار در برنامه‌ریزی دیده نمی‌شود.</p>'''),
  ]),
 en=dict(
  name='Dalli', province='Markazi', type_short='Porphyry Cu–Au',
  title='Dalli Porphyry Copper–Gold Deposit, Delijan: Geology, Alteration and Resources | Ali Alinaghi',
  h1='Dalli porphyry copper–gold deposit: geology and resources',
  desc='The Dalli porphyry Cu–Au deposit in Delijan County, Markazi Province: Northern and Southern Hills, the pyrite shell, an Ar–Ar age and published resource figures.',
  lede='Dalli, about 40 km northwest of Delijan, is a gold-rich porphyry Cu–Au deposit in the central Urumieh–Dokhtar arc with two mineralised centres, the Northern and Southern Hills.',
  coord_note='The Mindat point is identical to the USGS point and is probably copied from it rather than independent[[mindat440464]].',
  facts=[
   ('aka', 'Dali; Persian: دالی'),
   ('loc', 'Markazi Province; Delijan County, about 40 km northwest of Delijan and 9 km northwest of Raveh village[[petrology_dalli]]'),
   ('comm', 'Copper–gold (gold-rich porphyry)[[nrr2023]]; the annual licence lists copper only[[tasnim_dalli]]'),
   ('type', 'Early-Miocene porphyry Cu–Au with two centres (Northern and Southern Hills)[[ayati2013]][[nrr2023]]'),
   ('belt', 'Central Urumieh–Dokhtar magmatic arc[[ayati2013]]'),
   ('host', 'Diorite–granodiorite subvolcanic plutons (quartz-diorite porphyry) in andesitic–dacitic volcanics; main ore in andesite-porphyry wall rock between the intrusion and the pyrite shell[[nrr2023]]'),
   ('age', 'Minimum emplacement age about 21 Ma (biotite Ar–Ar, no reliable plateaus)[[ayati2013]]'),
   ('op', 'Exploitation licence issued in 1391 SH (2012/13) for about 480,000 t/yr[[tasnim_dalli]]; operator not identified in the sources reviewed'),
  ],
  sections=[
   ('Geological setting and age', '''<p>Dalli is an early-Miocene porphyry in the central Urumieh–Dokhtar arc with two mineralised centres, the Northern and Southern Hills[[ayati2013]][[nrr2023]]. Diorite to granodiorite subvolcanic plutons (quartz-diorite porphyry) intrude andesitic–dacitic volcanics, and the main ore lies in andesite-porphyry wall rock between the intrusion and the pyrite shell[[nrr2023]].</p>
<p>Biotite ⁴⁰Ar/³⁹Ar dating gives a minimum emplacement age of about 21 Ma, although no reliable age plateaus were obtained[[ayati2013]]. That is older than the middle-Miocene (17–15 Ma) pulse defined for the middle arc[[aghazadeh2015]], so either Dalli belongs to a separate pulse or its Ar–Ar age needs revisiting.</p>'''),
   ('Alteration and mineralisation', '''<p>A potassic core with phyllic and propylitic zones is reported, and a U-shaped pyrite shell bounds the significant Cu–Au mineralisation[[nrr2023]]. Chalcopyrite makes up about 40% of the metallic minerals, with pyrite; gold sits in chalcopyrite and quartz veins[[petrology_dalli]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('Operating status', '''<p>Dalli received an exploitation licence in 1391 SH (2012/13) for about 480,000 t/yr, covering copper only. In February 2021 the Delijan MP said the Department of Environment had declared the mine polluting[[tasnim_dalli]]; a mine spokesperson has said all permits were obtained[[donya_dalli]]. The operator was not identified in the sources reviewed.</p>'''),
  ],
  expert=[
   ('Gold and the pyrite shell in estimation', '''<p>The two published figures — 8 Mt at 0.5% Cu and 0.75 g/t Au (USGS, “prospect”) and about 5 Mt proven plus 12 Mt probable at about 0.5% Cu (2021) — share a copper grade but not a tonnage; the second is more than twice the first, probably reflecting more exploration or a larger footprint.</p>
<p>The 2021 figure gives no gold grade, although Dalli is a gold-rich porphyry and the USGS figure alone implies about 6 t of contained gold. In a deposit like this, estimating gold separately and using the U-shaped pyrite shell as a domain boundary are essential; if the licence covers copper only, part of the deposit’s value is invisible to planning.</p>'''),
  ]),
)

# =====================================================================
#  آهن
# =====================================================================
GOL_E_GOHAR = dict(
 slug='gol-e-gohar', commodity='fe', ntype='ioa', metal='fe',
 lat=29.101111, lon=55.323056, coord_src='Mindat', coord_cite='mindat258224', coord_conf='M',
 published=P, updated=P, related=['chadormalu', 'choghart', 'sangan'], links=LINKS_FE,
 res=[
  R('آنومالی ۳: حدود ۶۴۳ میلیون تن با ۵۳٫۱٪ آهن', 'No. 3 orebody: about 643 Mt @ 53.1% Fe', 'Alibabaie و همکاران (۲۰۲۰)', 'Alibabaie et al. (2020)', ['alibabaie2020'], 'M'),
  R('کل منطقه: «حدود ۱٫۱۳۵ میلیارد تن»', 'District: “about 1.135 billion tons”', 'Wikipedia؛ سال و رده روشن نیست', 'Wikipedia; year and category unclear', ['wp_golgohar'], 'L'),
 ],
 fa=dict(
  name='گل‌گهر', province='کرمان', type_short='آهن (منشأ مورد اختلاف)',
  title='کانسار سنگ آهن گل‌گهر سیرجان: زمین‌شناسی و دو نظریهٔ منشأ | علی علینقی',
  h1='زمین‌شناسی کانسار آهن گل‌گهر',
  desc='کانسار سنگ آهن گل‌گهر در شهرستان سیرجان: شش آنومالی در پهنهٔ سنندج–سیرجان، اختلاف بر سر منشأ ماگمایی–گرمابی یا سازند آهن نواری دگرگون‌شده، و ارقام ذخیرهٔ منتشرشده.',
  lede='گل‌گهر، حدود ۵۰ تا ۵۵ کیلومتری جنوب‌غرب سیرجان، مجموعه‌ای از شش پیکرهٔ کانسنگ آهن در پهنهٔ سنندج–سیرجان است. منشأ آن بحث‌برانگیزترین مسئلهٔ ژنتیکی در میان کانسارهای این اطلس است و این صفحه هر دو دیدگاه را با منابعشان آورده است.',
  coord_note='نقطهٔ دیگری با عنوان «Golgohar Fe deposit» در Mindat حدود ۱٫۷ کیلومتر دورتر است. شش پیکرهٔ کانسنگ در بیش از ۴۰ کیلومتر مربع پراکنده‌اند، بنابراین یک نقطه فقط ساده‌سازی است[[mindat258224]].',
  facts=[
   ('aka', 'Gol-Gohar، Golgohar، گل گهر'),
   ('loc', 'استان کرمان؛ شهرستان سیرجان، حدود ۵۲ تا ۵۵ کیلومتری جنوب‌غرب سیرجان[[mindat258224]][[wp_golgohar]]'),
   ('comm', 'مگنتیت همراه با پیریت و کالکوپیریت؛ مگنتیت توده‌ای و نواری[[jafari2019]][[mirzaei2018]]'),
   ('type', 'آهن؛ منشأ مورد اختلاف: ماگمایی–گرمابی از نوع کایرونا (± اسکارن) در برابر سازند آهن نواری دگرگون‌شدهٔ ادیاکاران'),
   ('belt', 'پهنهٔ سنندج–سیرجان[[jafari2019]]'),
   ('host', 'سنگ‌های دگرگونی نئوپروتروزوئیک پسین؛ سن‌های زیرکن U–Pb ۶۰۵ تا ۵۴۴ میلیون سال که طرفداران منشأ ادیاکاران به آن استناد می‌کنند[[atapour]]'),
   ('age', 'سن مستقیمی برای کانی‌سازی در دسترس نیست'),
   ('op', 'معدن روباز با شش پیکرهٔ کانسنگ در بیش از ۴۰ کیلومتر مربع[[mindat258224]]؛ آنومالی ۳ با نام «گهرزمین» استخراج می‌شود[[gohar2023]]؛ نام بهره‌بردار در منابع بررسی‌شده تأیید نشد'),
  ],
  sections=[
   ('دو نظریه دربارهٔ منشأ', '''<p>منشأ گل‌گهر بحث‌برانگیزترین مسئلهٔ ژنتیکی میان کانسارهای این اطلس است. سه مطالعه منشأ ماگمایی را ترجیح می‌دهند:</p>
<ul><li>Alibabaie و همکاران مقادیر δ¹⁸O مگنتیت (۴٫۹ ± ۰٫۷ در هزار) و δ⁵⁶Fe (۰٫۴۹ ± ۰٫۰۵ در هزار) را نشانهٔ سیال ماگمایی–گرمابی نوع کایرونا با منشأ گرانیتی می‌دانند[[alibabaie2020]].</li>
<li>Mirzaei و همکاران کانسنگ را به مگنتیت تودهٔ نوع کایرونا و مگنتیت نواری نوع اسکارن تقسیم می‌کنند و نوع نواری را «سازند آهن نواری» نمی‌دانند[[mirzaei2018]].</li>
<li>Jafari و همکاران کانسنگ چندمرحله‌ای را به سیالات ماگمایی در یک محیط کمانی نسبت می‌دهند[[jafari2019]].</li></ul>
<p>در مقابل، Atapour و Aftabi از یک سازند آهن نواری (BIF) ادیاکاران دگرگون‌شده دفاع می‌کنند. شواهد آن‌ها متاجاسپیلیت، قطعات فروافتاده (dropstone)، سن‌های زیرکن U–Pb ۶۰۵ تا ۵۴۴ میلیون سال، δ³⁴S پیریت در حدود +۲۴ در هزار و نبود هالهٔ اسکارنی یا پهنهٔ تغذیه‌کننده است[[atapour]]. مقاله‌ای در سال ۲۰۲۳ همین دیدگاه را برای آنومالی ۳ (گهرزمین) به کار برده است[[gohar2023]]. توصیف این کانسار صرفاً به‌عنوان «سازند آهن دگرگون‌شده» یا صرفاً «نوع کایرونا» جانب‌داری از یکی از دو دیدگاه است.</p>'''),
   ('کانی‌شناسی', '''<p>چند نسل مگنتیت همراه با پیریت و کالکوپیریت گزارش شده است[[jafari2019]]. هیچ تودهٔ نفوذی مرتبطی با کانی‌سازی تأیید نشده است؛ نکته‌ای که طرفداران منشأ رسوبی–دگرگونی بر آن تأکید می‌کنند[[atapour]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>عیار قابل اتکایی برای فسفر و گوگرد هیچ‌یک از کانسارهای آهن این اطلس، از جمله گل‌گهر، در منابع بررسی‌شده یافت نشد.</p>'''),
   ('بهره‌برداری', '''<p>گل‌گهر معدن روباز است و داده‌های تولید آن در مقاله‌هایی در سال‌های ۲۰۲۲ و ۲۰۲۶ به کار رفته است[[mathgeo2022]][[minerals2026]]. نام شرکت بهره‌بردار در منابع بررسی‌شده تأیید نشد.</p>'''),
  ],
  expert=[
   ('اثر مدل ژنتیکی بر تخمین', '''<p>اختلاف بر سر منشأ فقط بحثی دانشگاهی نیست. اگر بخشی از کانسنگ نواری و بخشی توده‌ای باشد، این دو نوع کانسنگ پیوستگی فضایی، چگالی و احتمالاً عیار گوگرد و فسفر متفاوتی دارند و باید دامنه‌های جداگانه داشته باشند. مدل سازند آهن نواری پیوستگی چینه‌ای و جهت‌یافتگی موازی لایه‌بندی را پیش‌بینی می‌کند و مدل ماگمایی–گرمابی کنترل ساختاری و شکل توده‌ای را؛ این دو، بیضوی جست‌وجو و ناهمسانگردی متفاوتی در واریوگرافی می‌طلبند.</p>
<p>رقم ۶۴۳ میلیون تن آنومالی ۳ و رقم حدود ۱٫۱۳۵ میلیارد تن کل منطقه دامنهٔ متفاوتی دارند و نباید با هم مقایسه یا جمع شوند.</p>'''),
  ]),
 en=dict(
  name='Gol-e-Gohar', province='Kerman', type_short='Iron (origin disputed)',
  title='Gol-e-Gohar Iron Ore Deposit, Sirjan: Geology and Two Theories of Origin | Ali Alinaghi',
  h1='Gol-e-Gohar iron ore deposit: geology and origin',
  desc='The Gol-e-Gohar iron ore deposit in Sirjan County, Kerman: six orebodies in the Sanandaj–Sirjan Zone, the dispute between a magmatic-hydrothermal and a metamorphosed banded-iron-formation origin, and published resource figures.',
  lede='Gol-e-Gohar, about 50–55 km southwest of Sirjan, is a group of six iron orebodies in the Sanandaj–Sirjan Zone. Its origin is the sharpest genetic dispute among the deposits in this atlas, and this page sets out both views with their sources.',
  coord_note='A second Mindat point, “Golgohar Fe deposit”, lies 1.7 km away. The six orebodies are spread over more than 40 km², so a single point is a simplification[[mindat258224]].',
  facts=[
   ('aka', 'Gol-Gohar, Golgohar; Persian: گل‌گهر'),
   ('loc', 'Kerman Province; Sirjan County, about 52–55 km southwest of Sirjan[[mindat258224]][[wp_golgohar]]'),
   ('comm', 'Magnetite with pyrite and chalcopyrite; massive and banded magnetite[[jafari2019]][[mirzaei2018]]'),
   ('type', 'Iron; origin disputed — Kiruna-type magmatic-hydrothermal (± skarn) vs metamorphosed Ediacaran banded iron formation'),
   ('belt', 'Sanandaj–Sirjan Zone[[jafari2019]]'),
   ('host', 'Late Neoproterozoic metamorphic rocks; zircon U–Pb ages of 605–544 Ma cited by proponents of an Ediacaran origin[[atapour]]'),
   ('age', 'No direct age for the mineralisation'),
   ('op', 'Open pit with six orebodies over more than 40 km²[[mindat258224]]; the No. 3 orebody is mined as Gohar Zamin[[gohar2023]]; operator name not confirmed in the sources reviewed'),
  ],
  sections=[
   ('Two theories of origin', '''<p>Gol-e-Gohar’s origin is the sharpest genetic dispute among the deposits in this atlas. Three studies favour a magmatic origin:</p>
<ul><li>Alibabaie et al. read magnetite δ¹⁸O of 4.9 ± 0.7‰ and δ⁵⁶Fe of 0.49 ± 0.05‰ as evidence of a Kiruna-type magmatic-hydrothermal fluid from a granitic source[[alibabaie2020]].</li>
<li>Mirzaei et al. split the ore into Kiruna-type massive magnetite and skarn-type banded magnetite, and do not classify the banded type as a banded iron formation[[mirzaei2018]].</li>
<li>Jafari et al. attribute the multiphase ore to magmatic fluids in an arc setting[[jafari2019]].</li></ul>
<p>Atapour and Aftabi argue instead for a metamorphosed Ediacaran banded iron formation (BIF). They cite metajaspilites, dropstones, zircon U–Pb ages of 605–544 Ma, pyrite δ³⁴S near +24‰ and the absence of any skarn halo or feeder zone[[atapour]]. A 2023 paper applies the same view to the Gohar Zamin (No. 3) orebody[[gohar2023]]. Describing the ore simply as “metamorphosed iron formation”, or simply as “Kiruna-type”, takes one side.</p>'''),
   ('Mineralogy', '''<p>Several generations of magnetite are reported with pyrite and chalcopyrite[[jafari2019]]. No associated intrusion has been confirmed — a point the sedimentary–metamorphic camp emphasises[[atapour]].</p>'''),
   ('Published resource figures', '''{{res}}<p>No reliable phosphorus or sulphur grade was found in the sources reviewed for any iron deposit in this atlas, Gol-e-Gohar included.</p>'''),
   ('Operations', '''<p>Gol-e-Gohar is an open-pit mine, and its production data have been used in papers published in 2022 and 2026[[mathgeo2022]][[minerals2026]]. The operating company’s name was not confirmed in the sources reviewed.</p>'''),
  ],
  expert=[
   ('How the genetic model affects estimation', '''<p>The dispute over origin is not merely academic. If part of the ore is banded and part massive, the two types differ in spatial continuity, density and probably sulphur and phosphorus grade, and need separate domains. A BIF model predicts stratigraphic continuity and orientation parallel to layering; a magmatic-hydrothermal model predicts structural control and massive bodies. The two call for different search ellipses and anisotropy in the variography.</p>
<p>The 643 Mt figure for the No. 3 orebody and the roughly 1.135 Gt figure for the whole district cover different scopes and should not be compared or added.</p>'''),
  ]),
)

CHADORMALU = dict(
 slug='chadormalu', commodity='fe', ntype='ioa', metal='fe',
 lat=32.29667, lon=55.51472, coord_src='Mindat', coord_cite='mindat223338', coord_conf='M',
 published=P, updated=P, related=['choghart', 'gol-e-gohar', 'sangan'], links=LINKS_FE,
 res=[
  R('ذخیرهٔ پیش از استخراج: ۴۰۰ میلیون تن با ۵۵٪ آهن', 'Pre-mining reserve: 400 Mt @ 55% Fe', 'مقاله‌ای در Arabian Journal of Geosciences', 'Paper in the Arabian Journal of Geosciences', ['arabjgeo_chador'], 'M'),
  R('پیکرهٔ اصلی حدود ۸۰٪ ذخیره را در بر دارد', 'The main orebody holds about 80% of the reserve', 'Mindat', 'Mindat', ['mindat223338'], 'ML'),
 ],
 fa=dict(
  name='چادرملو', province='یزد', type_short='آهن–آپاتیت (نوع کایرونا)',
  title='کانسار سنگ آهن چادرملو: زمین‌شناسی کانسار آهن–آپاتیت نوع کایرونا | علی علینقی',
  h1='زمین‌شناسی کانسار آهن–آپاتیت چادرملو',
  desc='کانسار سنگ آهن چادرملو در شهرستان اردکان یزد: کانسار آهن–آپاتیت نوع کایرونای ناحیهٔ بافق، سن‌سنجی U–Pb آپاتیت، دگرسانی و ذخیرهٔ پیش از استخراج.',
  lede='چادرملو، حدود ۱۸۰ کیلومتری شمال‌شرق یزد، کانسار آهن–آپاتیت نوع کایرونا در ناحیهٔ معدنی بافق است و محکم‌ترین سن‌سنجی را در میان کانسارهای آهن این اطلس دارد.',
  coord_note='مختصات از درجه–دقیقه–ثانیهٔ Mindat تبدیل شده است. Mindat این کانسار را ذیل شهرستان بافق هم آورده است.',
  facts=[
   ('aka', 'Chador Malu'),
   ('loc', 'استان یزد؛ شهرستان اردکان، بخش خرانق (Mindat)؛ از نظر زمین‌شناسی بخشی از ناحیهٔ بافق؛ حدود ۱۸۰ کیلومتری شمال‌شرق یزد[[mindat223338]][[wp_chadormalu]]'),
   ('comm', 'مگنتیت–فلوئورآپاتیت نوع کایرونا[[heidarian2018]]'),
   ('type', 'اکسید آهن–آپاتیت (نوع کایرونا)'),
   ('belt', 'ناحیهٔ بافق در کمان آتشفشانی–نفوذی کاشمر–کرمان (کامبرین پیشین)[[torab2007]][[heidarian2017]]'),
   ('host', 'سنگ‌های آتشفشانی–رسوبی پرکامبرین پسین تا کامبرین زیرین[[heidarian2017]]'),
   ('age', 'U–Pb آپاتیت: ۴۹۰ ± ۲۱ میلیون سال (غالب) و سن‌های آشفتگی ۴۳۷ ± ۱۲ و ۲۴۶ ± ۱۷ میلیون سال[[heidarian2018]]؛ ۵۲۹ ± ۲۵ و ۴۳۷ ± ۲۱ میلیون سال در مطالعه‌ای دیگر[[ogr2021_chador]]'),
   ('op', 'کشف در ۱۹۴۰ و تولید از ۱۹۹۹ (اطمینان کم تا متوسط)[[wp_chadormalu]]؛ نام بهره‌بردار و روش استخراج در منابع بررسی‌شده تأیید نشد'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی', '''<p>چادرملو و چغارت کانسارهای اکسید آهن–آپاتیت نوع کایرونا در ناحیهٔ بافق‌اند که درون کمان آتشفشانی–نفوذی کامبرین پیشین کاشمر–کرمان قرار دارد[[torab2007]][[heidarian2017]]. سنگ میزبان توالی آتشفشانی–رسوبی پرکامبرین پسین تا کامبرین زیرین است و دگرسانی‌های سدیک، کلسیک و پتاسیک گزارش شده است[[heidarian2017]].</p>'''),
   ('سن‌سنجی', '''<p>سن‌های چادرملو از همهٔ کانسارهای آهن این اطلس محکم‌ترند. U–Pb آپاتیت سن غالب ۴۹۰ ± ۲۱ میلیون سال و سن‌های آشفتگی ۴۳۷ ± ۱۲ و ۲۴۶ ± ۱۷ میلیون سال را نشان می‌دهد[[heidarian2018]]. مطالعه‌ای در ۲۰۲۱ سن‌های ۵۲۹ ± ۲۵ و ۴۳۷ ± ۲۱ میلیون سال را برای آپاتیت گزارش کرده است[[ogr2021_chador]]. در مقیاس ناحیهٔ بافق، سن مونازیت ۵۱۵ ± ۲۱ میلیون سال[[torab2007]] و سن‌های آپاتیت ۵۳۹ تا ۵۲۷ میلیون سال[[stosch2011]] منتشر شده است.</p>'''),
   ('کانی‌شناسی و دگرسانی', '''<p>کانسنگ از مگنتیت و فلوئورآپاتیت تشکیل شده است[[heidarian2018]]. پیریت تأخیری از ایزوتوپ گوگرد ۳۴ غنی است و پژوهشگران آن را به شورابه‌های حوضه‌ای نسبت می‌دهند[[heidarian2016]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
  ],
  expert=[
   ('آپاتیت: محصول جانبی یا عامل مزاحم؟', '''<p>در کانسارهای آهن–آپاتیت، فسفر دو چهره دارد: برای کنسانترهٔ آهن عامل مزاحم است و هزینهٔ فرآوری را بالا می‌برد، اما اگر آپاتیت بازیابی شود می‌تواند محصول جانبی باشد. در هر دو حالت، فسفر باید کنار آهن در مدل بلوکی تخمین زده شود و رفتار آن در آزمایش‌های فرآوری سنجیده شود.</p>
<p>ذخیرهٔ پیش از استخراج ۴۰۰ میلیون تن با ۵۵ درصد آهن رقمی تاریخی است؛ پس از سال‌ها بهره‌برداری، ذخیرهٔ باقی‌مانده فقط با یک تخمین به‌روز و آشتی دادن تولید واقعی با مدل (reconciliation) قابل بیان است.</p>'''),
  ]),
 en=dict(
  name='Chadormalu', province='Yazd', type_short='Iron oxide–apatite (Kiruna-type)',
  title='Chadormalu Iron Ore Deposit: Geology of a Kiruna-Type Magnetite–Apatite Deposit | Ali Alinaghi',
  h1='Chadormalu magnetite–apatite deposit: geology and age',
  desc='The Chadormalu iron ore deposit in Ardakan County, Yazd: a Kiruna-type magnetite–apatite deposit of the Bafq district, apatite U–Pb ages, alteration and the pre-mining reserve.',
  lede='Chadormalu, about 180 km northeast of Yazd, is a Kiruna-type iron oxide–apatite deposit in the Bafq mining district and has the firmest ages of any iron deposit in this atlas.',
  coord_note='Converted from Mindat’s degree–minute–second values. Mindat also lists the deposit under Bafq County.',
  facts=[
   ('aka', 'Chador Malu; Persian: چادرملو'),
   ('loc', 'Yazd Province; Ardakan County, Kharanaq District (Mindat); geologically part of the Bafq district; about 180 km northeast of Yazd[[mindat223338]][[wp_chadormalu]]'),
   ('comm', 'Kiruna-type magnetite–fluorapatite[[heidarian2018]]'),
   ('type', 'Iron oxide–apatite (Kiruna-type)'),
   ('belt', 'Bafq district in the Early Cambrian Kashmar–Kerman volcano-plutonic arc[[torab2007]][[heidarian2017]]'),
   ('host', 'Late Precambrian to Lower Cambrian volcano-sedimentary rocks[[heidarian2017]]'),
   ('age', 'Apatite U–Pb 490 ± 21 Ma (dominant) with disturbance ages of 437 ± 12 and 246 ± 17 Ma[[heidarian2018]]; 529 ± 25 and 437 ± 21 Ma in another study[[ogr2021_chador]]'),
   ('op', 'Found in 1940; production since 1999 (low–medium confidence)[[wp_chadormalu]]; operator and mining method not confirmed in the sources reviewed'),
  ],
  sections=[
   ('Geological setting', '''<p>Chadormalu and Choghart are Kiruna-type iron oxide–apatite deposits of the Bafq district, which lies within the Early Cambrian Kashmar–Kerman volcano-plutonic arc[[torab2007]][[heidarian2017]]. The host is a late Precambrian to Lower Cambrian volcano-sedimentary sequence, and sodic, calcic and potassic alteration are reported[[heidarian2017]].</p>'''),
   ('Geochronology', '''<p>Chadormalu’s ages are the firmest of any iron deposit in this atlas. Apatite U–Pb gives a dominant age of 490 ± 21 Ma with disturbance ages of 437 ± 12 and 246 ± 17 Ma[[heidarian2018]]. A 2021 study adds apatite ages of 529 ± 25 and 437 ± 21 Ma[[ogr2021_chador]]. At district scale, a monazite age of 515 ± 21 Ma[[torab2007]] and apatite ages of 539–527 Ma[[stosch2011]] have been published.</p>'''),
   ('Mineralogy and alteration', '''<p>The ore consists of magnetite and fluorapatite[[heidarian2018]]. Late pyrite is enriched in sulphur-34, which the authors attribute to basinal brines[[heidarian2016]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
  ],
  expert=[
   ('Apatite: by-product or penalty?', '''<p>In iron oxide–apatite deposits phosphorus has two faces: it is a penalty element in iron concentrate and raises processing cost, but recovered apatite can be a by-product. Either way, phosphorus should be estimated alongside iron in the block model and its behaviour measured in metallurgical testwork.</p>
<p>The pre-mining reserve of 400 Mt at 55% Fe is a historical figure; after years of production, the remaining reserve can only be stated from an up-to-date estimate reconciled against actual production.</p>'''),
  ]),
)

CHOGHART = dict(
 slug='choghart', commodity='fe', ntype='ioa', metal='fe',
 lat=31.70000, lon=55.46722, coord_src='Mindat', coord_cite='mindat205068', coord_conf='M',
 published=P, updated=P, related=['chadormalu', 'gol-e-gohar', 'sangan'], links=LINKS_FE,
 res=[],
 fa=dict(
  name='چغارت', province='یزد', type_short='آهن–آپاتیت (نوع کایرونا)',
  title='کانسار سنگ آهن چغارت بافق: زمین‌شناسی، دگرسانی و توریم | علی علینقی',
  h1='زمین‌شناسی کانسار آهن–آپاتیت چغارت',
  desc='کانسار سنگ آهن چغارت در شهرستان بافق یزد: کانسار اکسید آهن–آپاتیت ناحیهٔ بافق، مراحل دگرسانی، کانی‌سازی توریم و عناصر نادر خاکی و کمبود دادهٔ منتشرشده.',
  lede='چغارت، حدود ۱۲ کیلومتری شمال‌شرق بافق، از دههٔ ۱۹۷۰ میلادی استخراج می‌شود؛ با این حال دادهٔ منتشرشدهٔ آن، از سن تا ذخیره، کمتر از کانسارهای مشابه است.',
  coord_note='عرض جغرافیایی در Mindat گرد شده به نظر می‌رسد (دقت حدود ۰٫۵ کیلومتر). فاصلهٔ این نقطه تا چادرملو حدود ۶۶٫۵ کیلومتر است.',
  facts=[
   ('aka', 'Chogart، Choghart'),
   ('loc', 'استان یزد؛ شهرستان بافق، حدود ۱۲ کیلومتری شمال‌شرق بافق[[mindat205068]]'),
   ('comm', 'آپاتیت–مگنتیت همراه با توریم و عناصر نادر خاکی در توریت و تیتانیت[[geolcroat2017]]'),
   ('type', 'اکسید آهن–آپاتیت، ناحیهٔ بافق'),
   ('belt', 'ناحیهٔ بافق، کمان آتشفشانی–نفوذی کامبرین پیشین ایران مرکزی[[torab2007]]'),
   ('host', 'توالی آتشفشانی–رسوبی کامبرین پیشین ناحیهٔ بافق[[torab2007]]'),
   ('age', 'سن اختصاصی منتشرشده‌ای یافت نشد؛ سن‌های ناحیه‌ای مونازیت ۵۱۵ ± ۲۱[[torab2007]] و آپاتیت ۵۳۹ تا ۵۲۷ میلیون سال[[stosch2011]] لزوماً چغارت را دربرنمی‌گیرند'),
   ('op', 'استخراج از دههٔ ۱۹۷۰ میلادی[[mindat205068]]؛ نام بهره‌بردار و وضعیت کنونی در منابع بررسی‌شده تأیید نشد'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی', '''<p>چغارت یک کانسار اکسید آهن–آپاتیت در ناحیهٔ بافق است؛ همان ناحیه‌ای که چادرملو، حدود ۶۶٫۵ کیلومتر شمال‌تر، در آن قرار دارد. کانسارهای این ناحیه در کمان آتشفشانی–نفوذی کامبرین پیشین ایران مرکزی تشکیل شده‌اند[[torab2007]].</p>'''),
   ('مراحل دگرسانی', '''<p>Taghipour و همکاران توالی دگرسانی را چنین توصیف کرده‌اند: مرحلهٔ سدیک–کلسیک (اکتینولیت، مگنتیت و آپاتیت اولیه)، سپس مرحلهٔ سدیک–آهن‌دار (هماتیت) و در پایان کربناتی‌شدن و سیلیسی‌شدن تأخیری. آلبیتی‌شدن با توریم و عناصر نادر خاکی همراه است[[taghipour_njgpa]].</p>'''),
   ('توریم و عناصر نادر خاکی', '''<p>توریم و عناصر نادر خاکی در کانی‌های توریت و تیتانیت جای دارند[[geolcroat2017]] و یک آنومالی توریم در برش حاشیه‌ای کانسار گزارش شده است[[jnst_choghart]].</p>'''),
   ('ذخیره', '''<p>رقم ذخیرهٔ منتشرشده‌ای برای چغارت در منابع بررسی‌شده یافت نشد.</p>'''),
  ],
  expert=[
   ('پرتوزایی، عناصر نادر خاکی و دادهٔ گم‌شده', '''<p>وجود توریم در کانسنگ یا باطله دو پیامد دارد: پایش پرتوزایی در فرآوری و انباشت باطله، و فرصت ارزیابی عناصر نادر خاکی به‌عنوان محصول جانبی. اگر چنین ارزیابی‌ای مد نظر باشد، تجزیهٔ عناصر نادر خاکی و توریم باید به برنامهٔ نمونه‌برداری و کنترل کیفیت اضافه شود و پهنهٔ برش حاشیه‌ای که آنومالی توریم دارد دامنهٔ جداگانه بگیرد.</p>
<p>نبود سن و ذخیرهٔ منتشرشده برای معدنی با چند دهه سابقه نشان می‌دهد که داده‌های اصلی احتمالاً در گزارش‌های داخلی مانده‌اند؛ هر ارزیابی مستقل باید از داده‌های خام حفاری و تولید شروع شود.</p>'''),
  ]),
 en=dict(
  name='Choghart', province='Yazd', type_short='Iron oxide–apatite (Kiruna-type)',
  title='Choghart Iron Ore Deposit, Bafq: Geology, Alteration and Thorium | Ali Alinaghi',
  h1='Choghart magnetite–apatite deposit: geology and alteration',
  desc='The Choghart iron ore deposit in Bafq County, Yazd: an iron oxide–apatite deposit of the Bafq district, alteration stages, thorium and rare-earth mineralisation, and the gaps in the published record.',
  lede='Choghart, about 12 km northeast of Bafq, has been mined since the 1970s, yet its published record — from age to resource — is thinner than that of comparable deposits.',
  coord_note='Mindat’s latitude looks rounded (about ±0.5 km). This point is about 66.5 km from Chadormalu.',
  facts=[
   ('aka', 'Chogart; Persian: چغارت'),
   ('loc', 'Yazd Province; Bafq County, about 12 km northeast of Bafq[[mindat205068]]'),
   ('comm', 'Apatite–magnetite with thorium and rare earths hosted in thorite and titanite[[geolcroat2017]]'),
   ('type', 'Iron oxide–apatite, Bafq district'),
   ('belt', 'Bafq district, Early Cambrian volcano-plutonic arc of Central Iran[[torab2007]]'),
   ('host', 'Early Cambrian volcano-sedimentary sequence of the Bafq district[[torab2007]]'),
   ('age', 'No deposit-specific age found; the district monazite age of 515 ± 21 Ma[[torab2007]] and apatite ages of 539–527 Ma[[stosch2011]] do not necessarily include Choghart'),
   ('op', 'Mined since the 1970s[[mindat205068]]; operator and current status not confirmed in the sources reviewed'),
  ],
  sections=[
   ('Geological setting', '''<p>Choghart is an iron oxide–apatite deposit of the Bafq district, the same district that hosts Chadormalu about 66.5 km to the north. The district’s deposits formed in the Early Cambrian volcano-plutonic arc of Central Iran[[torab2007]].</p>'''),
   ('Alteration stages', '''<p>Taghipour et al. describe the alteration sequence as a sodic–calcic stage (actinolite, magnetite and early apatite), then a sodic–ferric stage (hematite), and finally late carbonatisation and silicification. Albitisation is associated with the thorium and rare earths[[taghipour_njgpa]].</p>'''),
   ('Thorium and rare earths', '''<p>Thorium and the rare-earth elements are hosted in thorite and titanite[[geolcroat2017]], and a thorium anomaly is reported in the marginal breccia of the deposit[[jnst_choghart]].</p>'''),
   ('Resources', '''<p>No published resource figure for Choghart was found in the sources reviewed.</p>'''),
  ],
  expert=[
   ('Radioactivity, rare earths and missing data', '''<p>Thorium in ore or tailings has two consequences: radiation monitoring in processing and tailings storage, and an opportunity to assess rare earths as a by-product. If such an assessment is considered, REE and thorium assays should be added to the sampling and QA/QC programme, and the marginal breccia with its thorium anomaly should be a separate domain.</p>
<p>The absence of a published age or resource for a mine with decades of production suggests the core data remain in internal reports; any independent evaluation would have to start from raw drilling and production data.</p>'''),
  ]),
)

SANGAN = dict(
 slug='sangan', commodity='fe', ntype='skarn', metal='fe',
 lat=34.48278, lon=60.45222, coord_src='Mindat', coord_cite='mindat_f34014', coord_conf='ML',
 published=P, updated=P, related=['gol-e-gohar', 'chadormalu', 'choghart'], links=LINKS_FE,
 res=[
  R('بیش از ۱٬۰۰۰ میلیون تن قطعی با حدود ۵۳٪ آهن', 'More than 1,000 Mt proven @ about 53% Fe', 'مقاله‌ای دربارهٔ کانسار فرزنه', 'Paper on the Ferezneh deposit', ['econg30378'], 'M'),
  R('۱٫۲ میلیارد تن زمین‌شناسی با ۲۷ تا ۶۱٪ آهن', '1.2 Gt geological @ 27–61% Fe', 'گزارشی دربارهٔ معادن سنگان', 'Report on the Sangan mines', ['911met_sangan'], 'ML'),
  R('ذخیرهٔ قطعی «به ۷۸۸ میلیون تن افزایش یافت»', 'Proven reserve “increased to 788 Mt”', 'خبر فارسی، بدون تاریخ', 'Persian news, undated', ['quds_sangan'], 'ML'),
 ],
 fa=dict(
  name='سنگان', province='خراسان رضوی', type_short='آهن اسکارنی',
  title='کانسار سنگ آهن سنگان خواف: زمین‌شناسی اسکارن آهن و ارقام ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار آهن اسکارنی سنگان',
  desc='ناحیهٔ معدنی سنگ آهن سنگان در شهرستان خواف خراسان رضوی: اسکارن آهن ائوسن، تودهٔ نفوذی سرنوسر، سن‌سنجی، آنومالی‌ها و ارقام ذخیرهٔ ناهم‌خوان.',
  lede='سنگان در شرق ایران یک ناحیهٔ معدنی چندکانساری است، نه یک معدن: اسکارن‌های آهن ائوسن آن در چند آنومالی و با چند بهره‌بردار استخراج می‌شوند و ارقام ذخیرهٔ آن در منابع مختلف هم‌خوان نیستند.',
  coord_note='مختصات از فهرست نقاط مجاور در Mindat تبدیل شده و اطمینان آن کم تا متوسط است[[mindat_f34014]]. سنگان ناحیه‌ای چندکانساری است و یک نقطه فقط موقعیت تقریبی آن را نشان می‌دهد.',
  facts=[
   ('aka', 'Sangan؛ «معدن سنگان خواف»'),
   ('loc', 'استان خراسان رضوی؛ شهرستان خواف[[quds_sangan]]'),
   ('comm', 'مگنتیت اسکارنی؛ در آنومالی کرات مگنتیت، هماتیت، گوتیت و لیمونیت با پیریت و کالکوپیریت جزئی[[ijcm_karat]]'),
   ('type', 'اسکارن آهن ائوسن[[golmohammadi2015]]'),
   ('belt', 'کمربند خواف–کاشمر–بردسکن؛ کانسارها شامل سی‌شمالی، باغک، دردوی، کرات و فرزنه[[econg30378]]'),
   ('host', 'تودهٔ نفوذی مرکب سرنوسر (سینیت تا سینوگرانیت، نوع I تفریق‌یافته)[[golmohammadi2015]]؛ اسکارن مگنتیتی دردوی در همبری گرانیت سرنوسر و کربنات منیزیم‌دار[[ijcm_dardvay]]'),
   ('age', 'زیرکن U–Pb تودهٔ سرنوسر غربی ۳۹٫۱ ± ۰٫۶ تا ۳۸٫۳ ± ۰٫۵ میلیون سال[[golmohammadi2015]]؛ فلوگوپیت کانسنگ (آرگون–آرگون) ۴۱٫۹۷ و ۴۲٫۴۷ ± ۰٫۲ میلیون سال[[sepidbar2017]]'),
   ('op', 'چند بهره‌بردار: ظرفیت ۲۵ میلیون تن در سال، توسعه توسط فولاد خراسان و مشارکت ایمیدرو با Sangan Parsian Epal[[myb2022]]؛ معدن شرکت ملی فولاد ایران ۱٬۵۳۸ هزار تن در ۲۰۲۳[[gem_nisco]]'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی', '''<p>سنگان ناحیه‌ای از اسکارن‌های آهن ائوسن در کمربند خواف–کاشمر–بردسکن در شمال‌شرق ایران است[[golmohammadi2015]] و چند کانسار، از جمله سی‌شمالی، باغک، دردوی، کرات و فرزنه، را دربرمی‌گیرد[[econg30378]]. تودهٔ نفوذی مرکب سرنوسر، با ترکیب سینیت تا سینوگرانیت و از نوع I تفریق‌یافته، منشأ کانی‌سازی دانسته می‌شود[[golmohammadi2015]].</p>'''),
   ('سن‌سنجی و یک ناسازگاری', '''<p>سن آرگون–آرگون فلوگوپیت کانسنگ ۴۱٫۹۷ و ۴۲٫۴۷ ± ۰٫۲ میلیون سال است[[sepidbar2017]]؛ یعنی قدیمی‌تر از سن زیرکن ۳۹٫۱ تا ۳۸٫۳ میلیون سال تودهٔ سرنوسر غربی که منشأ کانی‌سازی فرض می‌شود[[golmohammadi2015]]. کانی‌سازی نمی‌تواند از تودهٔ منشأ خود قدیمی‌تر باشد؛ پس یا فاز نفوذی قدیمی‌تری در کار بوده، یا یکی از دو مجموعه سن سوگیری دارد.</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>اسکارن مگنتیتی دردوی در همبری گرانیت سرنوسر و کربنات منیزیم‌دار در دمای ۳۷۵ تا ۵۸۰ درجهٔ سانتی‌گراد تشکیل شده و δ³⁴S پیریت آن از +۱۰٫۶ تا +۱۷٫۰ در هزار است که به ورود گوگرد از تبخیری‌ها تعبیر شده است[[ijcm_dardvay]]. در آنومالی کرات، مگنتیت، هماتیت، گوتیت و لیمونیت با پیریت و کالکوپیریت جزئی همراه‌اند[[ijcm_karat]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('بهره‌برداری', '''<p>سنگان مجموعه‌ای با چند بهره‌بردار است. USGS ظرفیت ۲۵ میلیون تن در سال، طرح‌های توسعهٔ فولاد خراسان و مشارکت ایمیدرو (سازمان توسعه و نوسازی معادن و صنایع معدنی ایران) با شرکت Sangan Parsian Epal را گزارش کرده است[[myb2022]]. معدنی که شرکت ملی فولاد ایران اداره می‌کند ۱٬۵۳۸ هزار تن استخراج در سال ۲۰۲۳ گزارش کرده است[[gem_nisco]]. بنابراین یک ستون «بهره‌بردار» واحد برای سنگان گمراه‌کننده است.</p>'''),
  ],
  expert=[
   ('یک ناحیه، چند بهره‌بردار، چند رقم', '''<p>ارقام «بیش از یک میلیارد تن قطعی» و «افزایش ذخیرهٔ قطعی به ۷۸۸ میلیون تن» با هم سازگار نیستند، مگر آنکه به محدوده‌ها یا آنومالی‌های متفاوتی مربوط باشند؛ در ناحیه‌ای که چند بهره‌بردار در آنومالی‌های جداگانه کار می‌کنند، این احتمال زیاد است. برای مقایسه، هر رقم باید با محدودهٔ پروانه، آنومالی‌ها، عیار حد و تاریخ آن همراه باشد.</p>
<p>بازهٔ عیار ۲۷ تا ۶۱ درصد آهن در رقم «زمین‌شناسی» نشان می‌دهد که کانسنگ کم‌عیار و پرعیار با هم جمع شده‌اند. در اسکارن‌های آهن، آهن مغناطیسی و نسبت آن به آهن کل برای برآورد محصول قابل فروش از آهن کل مهم‌تر است، و کانسنگ اکسیدی هماتیت–گوتیتی، مانند کانسنگ آنومالی کرات، با جدایش مغناطیسی شدت پایین بازیابی نمی‌شود.</p>'''),
  ]),
 en=dict(
  name='Sangan', province='Razavi Khorasan', type_short='Iron skarn',
  title='Sangan Iron Ore Deposit, Khaf: Geology of an Iron Skarn District and Resource Figures | Ali Alinaghi',
  h1='Sangan iron skarn district: geology and resources',
  desc='The Sangan iron ore district in Khaf County, Razavi Khorasan: Eocene iron skarns, the Sarnowsar intrusion, geochronology, the orebodies and conflicting resource figures.',
  lede='Sangan in eastern Iran is a multi-deposit district rather than a single mine: its Eocene iron skarns are worked in several orebodies by several operators, and its resource figures do not agree from one source to the next.',
  coord_note='Converted from Mindat’s nearby-locality lists; low–medium confidence[[mindat_f34014]]. Sangan is a multi-deposit district, so one point gives only its approximate position.',
  facts=[
   ('aka', '“Sangan Khaf” mine; Persian: سنگان'),
   ('loc', 'Razavi Khorasan Province; Khaf County[[quds_sangan]]'),
   ('comm', 'Skarn magnetite; at the Karat orebody, magnetite, hematite, goethite and limonite with minor pyrite and chalcopyrite[[ijcm_karat]]'),
   ('type', 'Eocene iron skarn[[golmohammadi2015]]'),
   ('belt', 'Khaf–Kashmar–Bardaskan belt; deposits include C-North, Baghak, Dardvay, Karat and Ferezneh[[econg30378]]'),
   ('host', 'Sarnowsar composite intrusion (syenite to syenogranite, fractionated I-type)[[golmohammadi2015]]; Dardvay magnetite skarn at the contact of Sarnowsar granite and Mg-rich carbonate[[ijcm_dardvay]]'),
   ('age', 'Zircon U–Pb of the western Sarnowsar intrusion 39.1 ± 0.6 to 38.3 ± 0.5 Ma[[golmohammadi2015]]; ore phlogopite (Ar–Ar) 41.97 and 42.47 ± 0.2 Ma[[sepidbar2017]]'),
   ('op', 'Several operators: 25 Mt/yr capacity, a Khorasan Steel expansion and an IMIDRO–Sangan Parsian Epal joint venture[[myb2022]]; a National Iranian Steel Co. (NISCO) mine reported 1,538 kt in 2023[[gem_nisco]]'),
  ],
  sections=[
   ('Geological setting', '''<p>Sangan is a district of Eocene iron skarns in the Khaf–Kashmar–Bardaskan belt of northeastern Iran[[golmohammadi2015]] that includes several deposits, among them C-North, Baghak, Dardvay, Karat and Ferezneh[[econg30378]]. The Sarnowsar composite intrusion — syenite to syenogranite, of fractionated I-type — is regarded as the source of the mineralisation[[golmohammadi2015]].</p>'''),
   ('Geochronology and an inconsistency', '''<p>Phlogopite from the ore gives Ar–Ar ages of 41.97 and 42.47 ± 0.2 Ma[[sepidbar2017]] — older than the 39.1–38.3 Ma zircon ages of the western Sarnowsar intrusion that supposedly generated it[[golmohammadi2015]]. Ore cannot be older than its source intrusion, so either an older intrusive phase was involved or one of the two datasets is biased.</p>'''),
   ('Alteration and mineralisation', '''<p>The Dardvay magnetite skarn formed at the contact between Sarnowsar granite and Mg-rich carbonate at 375–580 °C, and its pyrite δ³⁴S of +10.6 to +17.0‰ has been read as an evaporite input[[ijcm_dardvay]]. At Karat, magnetite, hematite, goethite and limonite occur with minor pyrite and chalcopyrite[[ijcm_karat]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('Operations', '''<p>Sangan is a complex with several operators. USGS reports a capacity of 25 Mt/yr, expansions by Khorasan Steel and a joint venture between IMIDRO (Iran’s state mining holding) and Sangan Parsian Epal[[myb2022]]. A mine run by the National Iranian Steel Co. reported 1,538 kt mined in 2023[[gem_nisco]]. A single “operator” field would therefore mislead.</p>'''),
  ],
  expert=[
   ('One district, several operators, several numbers', '''<p>“More than one billion tonnes proven” and “proven reserve increased to 788 Mt” cannot both describe the same thing unless they refer to different licence areas or orebodies — which is likely in a district where several operators work separate deposits. To be comparable, each figure needs its licence area, orebodies, cut-off grade and date.</p>
<p>The 27–61% Fe range in the “geological” figure shows that low- and high-grade ore have been lumped together. In iron skarns, magnetic iron and its ratio to total iron matter more than total iron for estimating saleable product, and oxidised hematite–goethite ore such as that at Karat is not recovered by low-intensity magnetic separation.</p>'''),
  ]),
)

# =====================================================================
#  سرب و روی
# =====================================================================
MEHDIABAD = dict(
 slug='mehdiabad', commodity='znpb', ntype='znpb', metal='zn',
 lat=None, lon=None, coord_src='', coord_cite=None, coord_conf='L',
 published=P, updated=P, related=['irankuh', 'angouran', 'chadormalu'], links=LINKS_ZN,
 res=[
  R('۲۱۸ میلیون تن با ۷٫۲٪ روی، ۲٫۳٪ سرب و ۵۱ گرم در تن نقره', '218 Mt @ 7.2% Zn, 2.3% Pb, 51 g/t Ag', 'دورهٔ Union Resources (دههٔ ۲۰۰۰)، منسوب به مطالعهٔ BRGM در ۱۹۹۴', 'Union Resources era (2000s), attributed to a 1994 BRGM study',
    ['miningnews_union', 'gsf_review'], 'M', calc=[(218, 7.2)], lab=('BRGM ۱۹۹۴', 'BRGM 1994')),
  R('حدود ۷۵ میلیون تن با ۶٪ روی و ۲٫۷٪ سرب', 'About 75 Mt @ 6% Zn, 2.7% Pb', 'سالنامهٔ USGS، ویرایش ۲۰۱۹ (داده‌های ۲۰۱۷)', 'USGS Minerals Yearbook, 2019 edition (2017 data)',
    ['myb2019'], 'M', calc=[(75, 6)], lab=('USGS ۲۰۱۹', 'USGS 2019 ed.')),
  R('۳۹۴ میلیون تن با ۴٫۲٪ روی، ۱٫۶٪ سرب و ۳۶ گرم در تن نقره (کل منبع)', '394 Mt @ 4.2% Zn, 1.6% Pb, 36 g/t Ag (total resource)', 'Maghfouri و همکاران (۲۰۱۹)', 'Maghfouri et al. (2019)',
    ['maghfouri2019'], 'M', calc=[(394, 4.2)], lab=('Maghfouri و همکاران', 'Maghfouri et al.')),
  R('حدود ۱۶۰ میلیون تن با ۶٪ روی و ۲٪ سرب', 'About 160 Mt @ 6% Zn, 2% Pb', 'سالنامهٔ USGS، ویرایش ۲۰۲۰–۲۱', 'USGS Minerals Yearbook, 2020–21 edition',
    ['myb2021'], 'M', calc=[(160, 6)], lab=('USGS ۲۰۲۰–۲۱', 'USGS 2020–21 ed.')),
  R('حدود ۱۷۰ میلیون تن با ۴٫۵٪ روی و ۱٫۶٪ سرب', 'About 170 Mt @ 4.5% Zn, 1.6% Pb', 'سالنامهٔ USGS، ویرایش ۲۰۲۳ (منتشرشده در فوریهٔ ۲۰۲۶)', 'USGS Minerals Yearbook, 2023 edition (released February 2026)',
    ['myb2023'], 'M', calc=[(170, 4.5)], lab=('USGS ۲۰۲۳', 'USGS 2023 ed.')),
 ],
 fa=dict(
  name='مهدی‌آباد', province='یزد', type_short='روی–سرب–باریت',
  title='کانسار سرب و روی مهدی‌آباد یزد: زمین‌شناسی، تیپ و ارقام ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار روی و سرب مهدی‌آباد',
  desc='کانسار روی–سرب–باریت مهدی‌آباد در شهرستان مهریز یزد: میزبان کرتاسهٔ زیرین، اختلاف بر سر تیپ SEDEX یا جانشینی کربناته، کانسنگ سولفیدی و غیرسولفیدی و ارقام ذخیرهٔ متغیر.',
  lede='مهدی‌آباد در جنوب حوضهٔ یزد کانساری است که Maghfouri و همکاران آن را «در مقیاس جهانی» توصیف کرده‌اند. ارقام ذخیرهٔ آن، حتی در سالنامهٔ USGS، بارها تغییر کرده است و این صفحه آن‌ها را به ترتیب زمانی کنار هم می‌گذارد.',
  coord_note='موقعیت این کانسار منتشر نمی‌شود: Mindat آن را در دو نقطه با ۳۰٫۶ کیلومتر فاصله آورده است؛ یکی ذیل شهرستان انار استان کرمان[[mindat223163]] و دیگری ذیل مهریز با طول جغرافیایی گرد[[mindat_f403949]]. مختصات پس از تطبیق با نقشهٔ زمین‌شناسی ۱:۱۰۰٬۰۰۰ یا نقشهٔ موقعیت یک مقالهٔ داوری‌شده افزوده می‌شود.',
  facts=[
   ('aka', 'Mehdi Abad'),
   ('loc', 'استان یزد؛ شهرستان مهریز[[mehrnews_mehdiabad]]؛ USGS نیز آن را در استان یزد می‌داند[[myb2021]]'),
   ('comm', 'روی–سرب–باریت (± مس و نقره)؛ پیکرهٔ دره‌ای (Valley) با کانسنگ سولفیدی و غیرسولفیدی و پیکرهٔ کوهی (Mountain) کاملاً غیرسولفیدی[[hal_mehdiabad]]'),
   ('type', 'مورد اختلاف: SEDEX از نوع جانشینی زیر بستر دریا در نزدیکی دهانه[[maghfouri2019]] در برابر جانشینی باریت و برش دولومیتی در کرتاسهٔ پیشین[[upc2023]] یا تیپ ایرلندی[[rajabi_iaeg]]'),
   ('belt', 'جنوب حوضهٔ یزد، بلوک یزد، ایران مرکزی[[maghfouri2019]]'),
   ('host', 'سازند تفت (شیل غنی از مواد آلی، سیلتستون سیاه، دولومیت، ماسه‌سنگ) و سازند آبکوه، کرتاسهٔ زیرین[[jaes_mehdiabad]]'),
   ('age', 'سن رادیومتری کانی‌سازی در دسترس نیست'),
   ('op', 'پروانه در اختیار ایمیدرو و بهره‌برداری با کنسرسیومی خصوصی از ۱۳۹۵[[akhbaremadan_mehdiabad]]؛ در فهرست شرکت‌های تابعهٔ ایمیدرو در سالنامهٔ USGS منتشرشده در فوریهٔ ۲۰۲۶[[myb2023]]'),
  ],
  sections=[
   ('زمین‌شناسی و کانی‌سازی', '''<p>مهدی‌آباد در سازندهای تفت و آبکوه کرتاسهٔ زیرین در جنوب حوضهٔ یزد قرار دارد[[jaes_mehdiabad]][[maghfouri2019]]. کانسنگ سولفیدی از اسفالریت، گالن و باریت همراه با مقدار کمی پیریت و کالکوپیریت تشکیل شده و در پهنه‌های اکسیدی اسمیت‌زونیت، هیدروزینسیت، همی‌مورفیت و سروزیت دیده می‌شوند. کانی‌سازی در دو افق و در امتداد دست‌کم ۳٫۴ کیلومتر گسترش دارد[[upc2023]][[mindat223163]]. کانسار دو پیکرهٔ اصلی دارد: پیکرهٔ دره‌ای با کانسنگ مختلط سولفیدی و غیرسولفیدی و پیکرهٔ کوهی که کاملاً غیرسولفیدی است[[hal_mehdiabad]].</p>'''),
   ('تیپ کانسار: سه دیدگاه', '''<p>Maghfouri و همکاران (۲۰۱۹) مهدی‌آباد را کانسار SEDEX از نوع «جانشینی زیر بستر دریا در نزدیکی دهانه» طبقه‌بندی کرده‌اند[[maghfouri2019]]. پژوهشی دیگر آن را جانشینی باریت و برش دولومیتی‌شده در کرتاسهٔ پیشین می‌داند[[upc2023]] و Rajabi و همکاران آن را در گروه کانسارهای تیپ ایرلندی جای می‌دهند[[rajabi_iaeg]]. Reichert و Borg (۲۰۰۸) نیز در مطالعه‌ای که ایرانکوه را هم دربرمی‌گیرد به مهدی‌آباد پرداخته‌اند[[reichert2008]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}<p>رقمی حدود ۶۳۰ میلیون تن هم در برخی منابع آمده که با عیار مس نامعقولی همراه است و به احتمال زیاد خطای رونویسی است؛ این رقم در جدول نیامده است[[mindat223163]].</p>'''),
   ('بهره‌برداری و طرح توسعه', '''<p>پروانهٔ مهدی‌آباد در اختیار ایمیدرو است که بهره‌برداری را در ۱۳۹۵ به کنسرسیومی خصوصی واگذار کرد[[akhbaremadan_mehdiabad]]. USGS از توسعهٔ یک میلیارد دلاری توسط پنج شرکت خصوصی برای تولید سالانهٔ ۸۰۰ هزار تن کنسانترهٔ روی و ۸۰ هزار تن کنسانترهٔ سرب–نقره خبر داده است؛ طرحی که از دههٔ ۱۹۹۰ بارها به تأخیر افتاده است[[myb2021]]. آخرین فصل ایران در سالنامهٔ USGS (ویرایش ۲۰۲۳، منتشرشده در فوریهٔ ۲۰۲۶) «مجتمع باریت، سرب و روی مهدی‌آباد» را در فهرست شرکت‌های تابعهٔ ایمیدرو آورده است[[myb2023]]. روش استخراج در منابع بررسی‌شده تأیید نشد.</p>'''),
  ],
  expert=[
   ('نوسان ارقام USGS: تناژ یا عیار؟', '''<p>در سه ویرایش پیاپی سالنامهٔ USGS، رقم مهدی‌آباد از حدود ۷۵ میلیون تن با ۶٪ روی به ۱۶۰ میلیون تن با ۶٪ و سپس به ۱۷۰ میلیون تن با ۴٫۵٪ روی تغییر کرده است. روی محتوا ابتدا از حدود ۴٫۵ به ۹٫۶ میلیون تن افزایش و سپس، با کاهش یک‌چهارمی عیار، به حدود ۷٫۷ میلیون تن کاهش یافته است. افزایش تناژ همراه با افت عیار معمولاً نشانهٔ پایین آمدن عیار حد یا افزوده شدن کانسنگ کم‌عیارتر است.</p>
<p>رقم ادبیات علمی (۳۹۴ میلیون تن با ۴٫۲٪ روی) «کل منبع» است و رقم دههٔ ۲۰۰۰ (۲۱۸ میلیون تن با ۷٫۲٪ روی) به مطالعه‌ای در ۱۹۹۴ برمی‌گردد؛ هیچ‌یک با ارقام USGS هم‌دامنه نیستند. کانسنگ سولفیدی و غیرسولفیدی بازیابی متفاوتی دارند، بنابراین روی محتوا بدون تفکیک نوع کانسنگ معیار کاملی برای مقایسه نیست.</p>'''),
  ]),
 en=dict(
  name='Mehdiabad', province='Yazd', type_short='Zn–Pb–Ba',
  title='Mehdiabad Zinc–Lead Deposit, Yazd: Geology, Deposit Type and Resource Figures | Ali Alinaghi',
  h1='Mehdiabad zinc–lead deposit: geology and resources',
  desc='The Mehdiabad Zn–Pb–Ba deposit in Mehriz County, Yazd: Lower Cretaceous host rocks, the SEDEX vs carbonate-replacement debate, sulphide and non-sulphide ore, and shifting resource figures.',
  lede='Mehdiabad, in the southern Yazd Basin, is a deposit Maghfouri et al. describe as “world-class”. Its resource figures have changed repeatedly, even within the USGS Minerals Yearbook, and this page sets them out in date order.',
  coord_note='No coordinates are published for this deposit: Mindat places it at two points 30.6 km apart, one filed under Anar County in Kerman Province[[mindat223163]] and one under Mehriz with a rounded longitude[[mindat_f403949]]. Coordinates will be added once checked against a 1:100,000 geological sheet or a location map in a peer-reviewed paper.',
  facts=[
   ('aka', 'Mehdi Abad; Persian: مهدی‌آباد'),
   ('loc', 'Yazd Province; Mehriz County[[mehrnews_mehdiabad]]; USGS also places it in Yazd Province[[myb2021]]'),
   ('comm', 'Zn–Pb–Ba (± Cu–Ag); a Valley Orebody of mixed sulphide and non-sulphide ore and a purely non-sulphide Mountain Orebody[[hal_mehdiabad]]'),
   ('type', 'Disputed: vent-proximal sub-seafloor replacement SEDEX[[maghfouri2019]] vs Early Cretaceous replacement of barite and dolomitised breccia[[upc2023]] or Irish-type[[rajabi_iaeg]]'),
   ('belt', 'Southern Yazd Basin, Yazd Block, Central Iran[[maghfouri2019]]'),
   ('host', 'Lower Cretaceous Taft Formation (organic-rich shale, black siltstone, dolomite, sandstone) and Abkuh Formation[[jaes_mehdiabad]]'),
   ('age', 'No radiometric age for the mineralisation'),
   ('op', 'Licence held by IMIDRO and operated by a private consortium since 1395 SH (2016/17)[[akhbaremadan_mehdiabad]]; listed among IMIDRO subsidiaries in the USGS yearbook released in February 2026[[myb2023]]'),
  ],
  sections=[
   ('Geology and mineralisation', '''<p>Mehdiabad lies in the Lower Cretaceous Taft and Abkuh formations of the southern Yazd Basin[[jaes_mehdiabad]][[maghfouri2019]]. The sulphide ore is sphalerite, galena and barite with minor pyrite and chalcopyrite; smithsonite, hydrozincite, hemimorphite and cerussite occur in the oxidised zones. Mineralisation extends over two horizons along at least 3.4 km of strike[[upc2023]][[mindat223163]]. There are two main orebodies: the Valley Orebody of mixed sulphide and non-sulphide ore and the Mountain Orebody, which is entirely non-sulphide[[hal_mehdiabad]].</p>'''),
   ('Deposit type: three views', '''<p>Maghfouri et al. (2019) classify Mehdiabad as a “vent-proximal sub-seafloor replacement” SEDEX deposit[[maghfouri2019]]. Another study reads it as Early Cretaceous replacement of barite and dolomitised breccia[[upc2023]], and Rajabi et al. place it among Irish-type deposits[[rajabi_iaeg]]. Reichert and Borg (2008) also discuss Mehdiabad in a study that covers Irankuh[[reichert2008]].</p>'''),
   ('Published resource figures', '''{{res}}<p>A figure of about 630 Mt also appears in some sources together with an implausible copper grade and is almost certainly a transcription error; it is not included in the table[[mindat223163]].</p>'''),
   ('Operations and expansion', '''<p>Mehdiabad’s licence sits with IMIDRO, which handed operation to a private consortium in 1395 SH (2016/17)[[akhbaremadan_mehdiabad]]. USGS describes five private companies developing a US$1 billion expansion to 800,000 t/yr of zinc concentrate and 80,000 t/yr of lead–silver concentrate, a project delayed repeatedly since the 1990s[[myb2021]]. The latest USGS Iran chapter (2023 edition, released February 2026) lists the “Mehdiabad Barite, Lead, and Zinc Complex” among IMIDRO subsidiaries[[myb2023]]. The mining method was not confirmed in the sources reviewed.</p>'''),
  ],
  expert=[
   ('Shifting USGS figures: tonnage or grade?', '''<p>Across three successive USGS yearbooks, Mehdiabad moved from about 75 Mt at 6% Zn to 160 Mt at 6% and then to 170 Mt at 4.5% Zn. Contained zinc first rose from about 4.5 to 9.6 Mt, then fell back to about 7.7 Mt as the grade was cut by a quarter. Rising tonnage with falling grade usually signals a lower cut-off grade or the addition of lower-grade material.</p>
<p>The literature figure (394 Mt at 4.2% Zn) is a total resource, and the 2000s figure (218 Mt at 7.2% Zn) goes back to a 1994 study; neither shares the scope of the USGS numbers. Sulphide and non-sulphide ores recover differently, so contained zinc without a split by ore type is an incomplete basis for comparison.</p>'''),
  ]),
)

ANGOURAN = dict(
 slug='angouran', commodity='znpb', ntype='znpb', metal='zn',
 lat=36.62283, lon=47.40674, coord_src='Mindat', coord_cite='mindat25133', coord_conf='H',
 published=P, updated=P, related=['zarshuran', 'agh-darreh', 'mehdiabad'], links=LINKS_ZN,
 res=[
  R('۴٫۷ میلیون تن سولفیدی با ۲۷٫۷٪ روی، ۲٫۴٪ سرب و ۱۱۰ گرم در تن نقره + ۱۴٫۶ میلیون تن کربناتی اکسیدی با ۲۲٪ روی و ۴٫۶٪ سرب',
    '4.7 Mt sulphide @ 27.7% Zn, 2.4% Pb, 110 g/t Ag + 14.6 Mt oxidised carbonate @ 22% Zn, 4.6% Pb',
    'Gilg و همکاران (۲۰۰۶)', 'Gilg et al. (2006)', ['gilg2006'], 'H', calc=[(4.7, 27.7), (14.6, 22)], lab=('Gilg و همکاران', 'Gilg et al.')),
  R('حدود ۱۸ میلیون تن با ۲۸٪ روی، عمدتاً اسمیت‌زونیت', 'About 18 Mt @ 28% Zn, mostly smithsonite', 'Boni و همکاران (۲۰۰۷)', 'Boni et al. (2007)',
    ['boni2007'], 'M', calc=[(18, 28)], lab=('Boni و همکاران', 'Boni et al.')),
  R('حدود ۱۶ میلیون تن با ۲۶٪ روی و ۶٪ سرب', 'About 16 Mt @ 26% Zn, 6% Pb', 'سالنامهٔ USGS ۲۰۱۹ (داده‌های ۲۰۱۷)', 'USGS Minerals Yearbook 2019 (2017 data)',
    ['myb2019'], 'M', calc=[(16, 26)], lab=('USGS ۲۰۱۹', 'USGS 2019')),
 ],
 fa=dict(
  name='انگوران', province='زنجان', type_short='روی–سرب کربناتی و سولفیدی',
  title='کانسار سرب و روی انگوران ماه‌نشان: زمین‌شناسی و منشأ | علی علینقی',
  h1='زمین‌شناسی کانسار روی و سرب انگوران',
  desc='کانسار روی–سرب انگوران در شهرستان ماه‌نشان زنجان: میزبان مرمر و شیست، کانسنگ سولفیدی و کربنات روی پرعیار، چهار دیدگاه دربارهٔ منشأ و ارقام ذخیرهٔ هم‌گرا.',
  lede='انگوران پرعیارترین کانسار روی این اطلس است و کانسنگ آن ترکیبی از سولفید و کربنات‌های روی است. با وجود اختلاف بر سر منشأ، ارقام ذخیرهٔ منتشرشده برای آن به‌طور چشمگیری به هم نزدیک‌اند.',
  coord_note='دقت این نقطه در حد دقیقهٔ قوسی تأیید شده است. روستای انگوران حدود ۲۲ کیلومتر با معدن فاصله دارد و نباید به‌جای آن به کار رود[[wp_anguran_village]].',
  facts=[
   ('aka', 'Anguran'),
   ('loc', 'استان زنجان؛ شهرستان ماه‌نشان؛ نزدیک‌ترین شهر: دندی[[smsm_angouran]]'),
   ('comm', 'روی–(سرب–نقره)؛ کانسنگ سولفیدی میزبان مرمر با ۱۱۰ گرم در تن نقره و کانسنگ کربناتی که عمدتاً اسمیت‌زونیت است[[gilg2006]]'),
   ('type', 'مورد اختلاف (بخش «چهار دیدگاه دربارهٔ منشأ» را ببینید)'),
   ('belt', 'مجموعهٔ هسته‌ای دگرگونی در بخش مرکزی پهنهٔ سنندج–سیرجان؛ ناحیهٔ تکاب–تخت سلیمان–انگوران[[econg40222]]'),
   ('host', 'مرمر نئوپروتروزوئیک–کامبرین روی میکاشیست در ستیغ یک تاقدیس باز، با پوشش میوسن شامل سازندهای قم و قرمز بالایی[[gilg2006]][[daliran2013]]'),
   ('age', 'سن رادیومتری کانی‌سازی در دسترس نیست؛ بر پایهٔ مدل‌های زمین‌شناسی میوسن فرض می‌شود'),
   ('op', 'شرکت تهیه و تولید مواد معدنی ایران (ایمپاسکو)[[impasco_angouran]]؛ معدن روباز و معدن زیرزمینی سولفیدی با ظرفیت ۱۲۰ هزار تن کانسنگ در سال با ۲۵٪ روی و ۲٪ سرب[[imidro_angouran]]'),
  ],
  sections=[
   ('جایگاه زمین‌شناسی', '''<p>انگوران در مرمر و شیست یک مجموعهٔ هسته‌ای دگرگونی در بخش مرکزی پهنهٔ سنندج–سیرجان جای دارد و بخشی از ناحیهٔ معدنی تکاب–تخت سلیمان–انگوران است[[econg40222]]. سنگ میزبان مرمر نئوپروتروزوئیک–کامبرین است که روی میکاشیست و در ستیغ یک تاقدیس باز قرار گرفته و سنگ‌های میوسن، از جمله سازندهای قم و قرمز بالایی، آن را پوشانده‌اند[[gilg2006]][[daliran2013]]. زرشوران و آق‌دره، دو کانسار طلای کارلین‌گونهٔ ناحیهٔ تکاب، ۲۶ تا ۳۵ کیلومتر با انگوران فاصله دارند.</p>'''),
   ('چهار دیدگاه دربارهٔ منشأ', '''<ul><li><b>شورابهٔ حوضه‌ای و کربنات روی درون‌زاد:</b> کانسنگ سولفیدی از شورابه‌های حوضه‌ای نهشته شده و کربنات‌های روی درون‌زاد (هیپوژن) بر آن منطبق شده‌اند[[gilg2006]][[boni2007]][[daliran2013]].</li>
<li><b>دودکش برشی ناشی از حرکت نمک:</b> تیپ تازه‌ای با دمای پایین که در یک دودکش برشی، بر اثر حرکت نمک در بالای تبخیری‌های میوسنِ اکنون ناپدیدشده، تشکیل شده است[[zhuang_gsa]].</li>
<li><b>سوپرژن:</b> در تازه‌ترین پژوهش، منطقه‌بندی کانسنگ غیرسولفیدی را سطح ایستابی قدیمی کنترل کرده است؛ یعنی منشأ سوپرژن[[zhuang2025]].</li>
<li><b>دو دیدگاه حاشیه‌ای:</b> برچسب «VMS» در Mindat[[mindat25133]] و چکیده‌ای در ۲۰۰۳ که کانسار را در پهنهٔ ارومیه–دختر جای می‌دهد[[goldschmidt2003]].</li></ul>
<p>میزبان نئوپروتروزوئیک–کامبرین و زمان میوسن انگوران یعنی نباید آن را با مهدی‌آباد و ایرانکوه زیر برچسب «کانسار کربنات‌میزبان کرتاسه» گروه‌بندی کرد.</p>'''),
   ('کانی‌شناسی', '''<p>اسفالریت در دو مرحله و در برش همبری شیست و مرمر تشکیل شده است[[ogr_angouran]]. اسمیت‌زونیت نیز دو نسل دارد و منطقه‌بندی قائمی از کانسنگ سولفیدی، از راه یک پهنهٔ انتقالی، به کانسنگ اکسیدی دیده می‌شود[[boni2007]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('بهره‌برداری', '''<p>انگوران را شرکت تهیه و تولید مواد معدنی ایران (ایمپاسکو) اداره می‌کند[[impasco_angouran]]. USGS در ۲۰۱۹ انتظار داشت معدن روباز به پایان عمر برسد[[myb2019]]. معدن زیرزمینی سولفیدی برای ۱۲۰ هزار تن کانسنگ در سال با ۲۵٪ روی و ۲٪ سرب طراحی شده است[[imidro_angouran]]؛ تاریخ دقیق افتتاح آن در منابع بررسی‌شده مشخص نشد. شرکت آهن آجین از ۱۳۸۸ پیمانکار معدن است[[ajin_angouran]].</p>'''),
  ],
  expert=[
   ('همگرایی روی محتوا', '''<p>سه رقم مستقل، یعنی ۴٫۷ میلیون تن کانسنگ سولفیدی به‌اضافهٔ ۱۴٫۶ میلیون تن کانسنگ کربناتی (Gilg و همکاران)، حدود ۱۸ میلیون تن با ۲۸٪ روی (Boni و همکاران) و حدود ۱۶ میلیون تن با ۲۶٪ روی (USGS)، همه به ۴٫۲ تا ۵٫۰ میلیون تن روی محتوا می‌رسند. این هم‌گرایی نشان می‌دهد که ابعاد کانسار به‌خوبی شناخته شده است.</p>
<p>نکتهٔ کلیدی برای تخمین، نسبت کانسنگ کربناتی به سولفیدی است: کربنات‌های روی با فلوتاسیون معمول سولفیدی به‌خوبی بازیابی نمی‌شوند و روش فرآوری متفاوتی می‌خواهند؛ پس تخمین جداگانهٔ هر نوع کانسنگ و تعیین مرز آن‌ها بر ارزش اقتصادی اثر مستقیم دارد.</p>'''),
  ]),
 en=dict(
  name='Angouran', province='Zanjan', type_short='Zn–Pb (carbonate and sulphide)',
  title='Angouran Zinc–Lead Deposit, Mahneshan: Geology and Origin | Ali Alinaghi',
  h1='Angouran zinc–lead deposit: geology and origin',
  desc='The Angouran Zn–Pb deposit in Mahneshan County, Zanjan: marble and schist host, high-grade sulphide and zinc-carbonate ore, four competing views of its origin and converging resource figures.',
  lede='Angouran is the highest-grade zinc deposit in this atlas, with ore that combines sulphide and zinc carbonates. Its origin is disputed, yet the published resource figures for it agree remarkably well.',
  coord_note='This point is confirmed to the arc-minute. Anguran village lies about 22 km from the mine and should not be used in its place[[wp_anguran_village]].',
  facts=[
   ('aka', 'Anguran; Persian: انگوران'),
   ('loc', 'Zanjan Province; Mahneshan County; nearest town Dandi[[smsm_angouran]]'),
   ('comm', 'Zn–(Pb–Ag); marble-hosted sulphide ore with 110 g/t Ag and carbonate ore dominated by smithsonite[[gilg2006]]'),
   ('type', 'Disputed (see “Four views of its origin”)'),
   ('belt', 'Metamorphic core complex in the central Sanandaj–Sirjan Zone; Takab–Takht-e-Soleyman–Angouran district[[econg40222]]'),
   ('host', 'Neoproterozoic–Cambrian marble over micaschist at the crest of an open anticline, with Miocene cover including the Qom and Upper Red formations[[gilg2006]][[daliran2013]]'),
   ('age', 'No radiometric age for the mineralisation; assumed Miocene from geological models'),
   ('op', 'Iran Minerals Production and Supply Co. (IMPASCO)[[impasco_angouran]]; open pit and an underground sulphide mine rated at 120,000 t/yr of ore grading 25% Zn and 2% Pb[[imidro_angouran]]'),
  ],
  sections=[
   ('Geological setting', '''<p>Angouran is hosted in marble and schist within a metamorphic core complex in the central Sanandaj–Sirjan Zone and belongs to the Takab–Takht-e-Soleyman–Angouran mining district[[econg40222]]. The host is Neoproterozoic–Cambrian marble lying over micaschist at the crest of an open anticline, covered by Miocene rocks including the Qom and Upper Red formations[[gilg2006]][[daliran2013]]. Zarshuran and Agh-Darreh, the two Carlin-style gold deposits of the Takab district, lie 26–35 km from Angouran.</p>'''),
   ('Four views of its origin', '''<ul><li><b>Basinal brines and hypogene zinc carbonate:</b> sulphide ore deposited from basinal brines and overprinted by hypogene zinc carbonates[[gilg2006]][[boni2007]][[daliran2013]].</li>
<li><b>A salt-related breccia pipe:</b> a new low-temperature type formed in a breccia pipe left by salt movement above Miocene evaporites that have since vanished[[zhuang_gsa]].</li>
<li><b>Supergene:</b> in the newest work, the non-sulphide zoning is controlled by the ancient water table, which makes it supergene[[zhuang2025]].</li>
<li><b>Two outliers:</b> Mindat’s “VMS” label[[mindat25133]] and a 2003 abstract that places the deposit in the Urumieh–Dokhtar zone[[goldschmidt2003]].</li></ul>
<p>Angouran’s Neoproterozoic–Cambrian host and Miocene timing mean it should not share a “Cretaceous carbonate-hosted” label with Mehdiabad and Irankuh.</p>'''),
   ('Mineralogy', '''<p>Sphalerite formed in two stages in breccia at the schist–marble contact[[ogr_angouran]]. Smithsonite also has two generations, and the ore shows vertical zoning from sulphide through a transition zone to oxide[[boni2007]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('Operations', '''<p>Angouran is run by the Iran Minerals Production and Supply Co. (IMPASCO)[[impasco_angouran]]. In 2019 USGS expected the open pit to be worked out[[myb2019]]. The underground sulphide mine is rated at 120,000 t/yr of ore grading 25% Zn and 2% Pb[[imidro_angouran]]; its opening date was not pinned down in the sources reviewed. Ahan Ajin has been the mining contractor since 1388 SH (2009/10)[[ajin_angouran]].</p>'''),
  ],
  expert=[
   ('Contained zinc converges', '''<p>Three independent figures — 4.7 Mt of sulphide plus 14.6 Mt of carbonate ore (Gilg et al.), about 18 Mt at 28% Zn (Boni et al.) and about 16 Mt at 26% Zn (USGS) — all imply 4.2–5.0 Mt of contained zinc. That convergence suggests the size of the deposit is well known.</p>
<p>The key estimation issue is the ratio of carbonate to sulphide ore: zinc carbonates do not respond well to conventional sulphide flotation and need a different processing route, so estimating each ore type separately and fixing the boundary between them bears directly on value.</p>'''),
  ]),
)

IRANKUH = dict(
 slug='irankuh', commodity='znpb', ntype='znpb', metal='zn',
 lat=32.51667, lon=51.62861, coord_src='Mindat', coord_cite='mindat422688', coord_conf='M',
 published=P, updated=P, related=['mehdiabad', 'angouran', 'kahang'], links=LINKS_ZN,
 res=[
  R('۷۰۰ هزار تن با ۲٫۵٪ سرب و ۱۱٪ روی', '700,000 t @ 2.5% Pb, 11% Zn', 'وب‌سایت فارسی؛ تاریخ نامعلوم', 'Persian website; date unknown', ['iranmetals'], 'L', chart=False),
  R('کلاه‌دروازه: حدود ۱ میلیون تن با ۱۰٪ روی', 'Kolahdarvazeh: about 1 Mt @ 10% Zn', 'مطبوعات مالی فارسی؛ تاریخ نامعلوم', 'Persian financial press; date unknown', ['donya_bama'], 'L', chart=False),
 ],
 fa=dict(
  name='ایرانکوه', province='اصفهان', type_short='روی–سرب–باریت کربنات‌میزبان',
  title='کانسار سرب و روی ایرانکوه اصفهان: زمین‌شناسی و تیپ کانسار | علی علینقی',
  h1='زمین‌شناسی کانسار روی و سرب ایرانکوه',
  desc='ناحیهٔ معدنی سرب و روی ایرانکوه در جنوب اصفهان: میزبان کربناتی–آواری آپتین، سه دیدگاه دربارهٔ تیپ (MVT، هم‌زاد رسوبی، ایرلندی) و معادن گوشفیل و تپه‌سرخ.',
  lede='ایرانکوه در جنوب اصفهان ناحیه‌ای با چند معدن روباز سرب و روی است. تیپ آن هنوز محل بحث است و برخلاف شهرتش، هیچ رقم ذخیرهٔ داوری‌شده یا رسمی برای آن در دسترس نیست.',
  coord_note='این نقطه پیت گوشفیل است[[mindat422688]]. نقطهٔ ناحیه‌ای Mindat طول جغرافیایی گرد دارد و حدود ۳٫۲ کیلومتر دورتر است[[mindat_f135294]].',
  facts=[
   ('aka', 'Iran-Kuh، Irankouh'),
   ('loc', 'استان اصفهان؛ «جنوب اصفهان»[[karimpour2017]]؛ شهرستان در منابع بررسی‌شده یافت نشد'),
   ('comm', 'روی–سرب–باریت (± نقره)؛ کانسنگ سولفیدی و غیرسولفیدی[[ghazban1994]]'),
   ('type', 'مورد اختلاف: نوع درهٔ میسی‌سی‌پی (MVT)[[karimpour2017]]، هم‌زاد رسوبی تا دیاژنز پیشین[[gushfil_paper]] یا تیپ ایرلندی[[rajabi_irish]]'),
   ('belt', 'جنوب کمربند ملایر–اصفهان، پهنهٔ سنندج–سیرجان[[karimpour2017]]'),
   ('host', 'سنگ‌های کربناتی–آواری کرتاسهٔ زیرین (آپتین) روی شیل و ماسه‌سنگ ژوراسیک[[tappehsorkh]]'),
   ('age', 'مورد اختلاف: ژوراسیک پسین تا کرتاسهٔ پیشین در برابر رویدادی جوان‌تر و مرتبط با زاگرس[[tappehsorkh]]'),
   ('op', 'شرکت باما (اصفهان)؛ معادن روباز گوشفیل، تپه‌سرخ و کلاه‌دروازه[[bama]]؛ تعطیلی کلاه‌دروازه بدون تاریخ گزارش شده است (اطمینان کم)[[donya_bama]]'),
  ],
  sections=[
   ('زمین‌شناسی', '''<p>ایرانکوه در سنگ‌های کربناتی–آواری کرتاسهٔ زیرین (آپتین) جای دارد که روی شیل و ماسه‌سنگ ژوراسیک قرار گرفته‌اند[[tappehsorkh]]؛ در جنوب کمربند ملایر–اصفهان در پهنهٔ سنندج–سیرجان[[karimpour2017]]. Ghazban و همکاران (۱۹۹۴) خاستگاه کانسارهای روی–سرب–باریت رسوب‌میزبان این ناحیه را بررسی کرده‌اند[[ghazban1994]].</p>'''),
   ('سه دیدگاه دربارهٔ تیپ کانسار', '''<ul><li><b>نوع درهٔ میسی‌سی‌پی (MVT):</b> دیدگاه Ghazban و همکاران و Karimpour و همکاران[[ghazban1994]][[karimpour2017]].</li>
<li><b>هم‌زاد رسوبی تا دیاژنز پیشین:</b> دیدگاه Boveiri Konari و همکاران، که کانی‌سازی را هم‌زمان یا اندکی پس از رسوب‌گذاری سنگ میزبان می‌دانند[[gushfil_paper]][[boveiri2018]].</li>
<li><b>تیپ ایرلندی:</b> Rajabi و همکاران ایرانکوه را در گروه کانسارهای تیپ ایرلندی جای می‌دهند[[rajabi_irish]].</li></ul>
<p>سن کانی‌سازی هم محل اختلاف است: ژوراسیک پسین تا کرتاسهٔ پیشین در برابر رویدادی جوان‌تر و مرتبط با کوهزایی زاگرس[[tappehsorkh]].</p>'''),
   ('کانی‌شناسی', '''<p>اسفالریت غنی از آهن، دولومیت و آنکریت از کانی‌های شاخص‌اند[[karimpour2017]] و در تپه‌سرخ دولومیتی‌شدن با کانی‌سازی سولفیدی همراه است[[boveiri2018]].</p>'''),
   ('ارقام ذخیره', '''<p>هیچ رقم ذخیرهٔ داوری‌شده یا رسمی برای ایرانکوه یافت نشد. تنها ارقام موجود از وب‌سایت‌ها و مطبوعات فارسی بدون تاریخ‌اند:</p>{{res}}'''),
  ],
  expert=[
   ('چرا تیپ کانسار برای اکتشاف مهم است', '''<p>سه مدل رقیب پیش‌بینی‌های اکتشافی متفاوتی دارند. در مدل MVT، کانی‌سازی دیرزاد و تحت کنترل ساختارها و تخلخل کربنات است و ادامهٔ آن را باید در امتداد گسل‌ها و سطوح انحلال جست‌وجو کرد. در مدل هم‌زاد رسوبی، کانی‌سازی به افق‌های چینه‌ای خاص محدود است و تعقیب همان افق در گسترهٔ حوضه منطقی است. مدل ایرلندی ترکیبی از کنترل گسل‌های تغذیه‌کننده و جانشینی در کربنات میزبان است.</p>
<p>برای تخمین، این یعنی دامنه‌بندی متفاوت: مرز چینه‌ای در یک مدل و پوستهٔ ساختاری در مدل دیگر. بدون رقم ذخیرهٔ معتبر برای ناحیه‌ای با چند معدن فعال یا سابقاً فعال، هر ارزیابی تازه باید از داده‌های خام حفاری شروع شود.</p>'''),
  ]),
 en=dict(
  name='Irankuh', province='Isfahan', type_short='Carbonate-hosted Zn–Pb–Ba',
  title='Irankuh Zinc–Lead District, Isfahan: Geology and Deposit Type | Ali Alinaghi',
  h1='Irankuh zinc–lead district: geology and deposit type',
  desc='The Irankuh Zn–Pb district south of Isfahan: Aptian carbonate–clastic host rocks, three competing deposit models (MVT, syn-sedimentary, Irish-type), and the Gushfil and Tappehsorkh pits.',
  lede='Irankuh, south of Isfahan, is a lead–zinc district with several open pits. Its deposit type is still debated, and despite its reputation no peer-reviewed or official resource figure for it is available.',
  coord_note='This point is the Gushfil pit[[mindat422688]]. Mindat’s district point has a rounded longitude and lies about 3.2 km away[[mindat_f135294]].',
  facts=[
   ('aka', 'Iran-Kuh, Irankouh; Persian: ایرانکوه'),
   ('loc', 'Isfahan Province; “south of Isfahan”[[karimpour2017]]; county not found in the sources reviewed'),
   ('comm', 'Zn–Pb–Ba (± Ag); sulphide and non-sulphide ore[[ghazban1994]]'),
   ('type', 'Disputed: Mississippi Valley-type (MVT)[[karimpour2017]], syn-sedimentary to early-diagenetic[[gushfil_paper]] or Irish-type[[rajabi_irish]]'),
   ('belt', 'Southern Malayer–Isfahan belt, Sanandaj–Sirjan Zone[[karimpour2017]]'),
   ('host', 'Lower Cretaceous (Aptian) carbonate–clastic rocks over Jurassic shale and sandstone[[tappehsorkh]]'),
   ('age', 'Disputed: Late Jurassic–Early Cretaceous vs a later, Zagros-related event[[tappehsorkh]]'),
   ('op', 'Bama Company (Isfahan); open pits at Gushfil, Tappehsorkh and Kolahdarvazeh[[bama]]; Kolahdarvazeh reported closed, undated (low confidence)[[donya_bama]]'),
  ],
  sections=[
   ('Geology', '''<p>Irankuh is hosted in Lower Cretaceous (Aptian) carbonate–clastic rocks lying over Jurassic shale and sandstone[[tappehsorkh]], in the southern Malayer–Isfahan belt of the Sanandaj–Sirjan Zone[[karimpour2017]]. Ghazban et al. (1994) studied the genesis of the district’s sediment-hosted Zn–Pb–Ba deposits[[ghazban1994]].</p>'''),
   ('Three views of the deposit type', '''<ul><li><b>Mississippi Valley-type (MVT):</b> the view of Ghazban et al. and Karimpour et al.[[ghazban1994]][[karimpour2017]].</li>
<li><b>Syn-sedimentary to early-diagenetic:</b> the view of Boveiri Konari and co-workers, who place mineralisation during or shortly after deposition of the host sediments[[gushfil_paper]][[boveiri2018]].</li>
<li><b>Irish-type:</b> Rajabi and co-workers group Irankuh with Irish-type deposits[[rajabi_irish]].</li></ul>
<p>The age of mineralisation is disputed as well: Late Jurassic–Early Cretaceous versus a later event related to the Zagros orogeny[[tappehsorkh]].</p>'''),
   ('Mineralogy', '''<p>Fe-rich sphalerite, dolomite and ankerite are characteristic[[karimpour2017]], and at Tappehsorkh dolomitisation accompanies the sulphides[[boveiri2018]].</p>'''),
   ('Resource figures', '''<p>No peer-reviewed or official resource figure for Irankuh was found. The only figures available come from undated Persian websites and press:</p>{{res}}'''),
  ],
  expert=[
   ('Why the deposit type matters for exploration', '''<p>The three competing models make different exploration predictions. In an MVT model, mineralisation is epigenetic and controlled by structures and carbonate porosity, so extensions should be sought along faults and dissolution surfaces. In a syn-sedimentary model, mineralisation is confined to particular stratigraphic horizons, and following the same horizon across the basin makes sense. The Irish-type model combines feeder-fault control with replacement of the carbonate host.</p>
<p>For estimation, this means different domaining: a stratigraphic boundary in one model and a structural envelope in another. Without a credible resource figure for a district with several active or former pits, any new evaluation would have to start from raw drilling data.</p>'''),
  ]),
)

# =====================================================================
#  طلا
# =====================================================================
SRC.update({
 'iribnews_sg': 'IRIB News (in Persian), news 2804368: expansion of the Qorveh gold mine. ' + A('https://www.iribnews.ir/fa/news/2804368/%D8%AA%D9%88%D8%B3%D8%B9%D9%87-%D9%85%D8%B9%D8%AF%D9%86-%D8%B7%D9%84%D8%A7%DB%8C-%D9%82%D8%B1%D9%88%D9%87', 'iribnews.ir'),
 'moutehgold': 'Muteh gold complex website (in Persian), post of 6 Bahman 1394. ' + A('http://moutehgold.ir/main/1394/11/06/174', 'moutehgold.ir'),
})

ZARSHURAN = dict(
 slug='zarshuran', commodity='au', ntype='carlin', metal='au',
 lat=36.7206, lon=47.1397, coord_src='USGS', coord_cite='usgs_sedau35', coord_conf='M',
 published=P, updated=P, related=['agh-darreh', 'angouran', 'sari-gunay'], links=LINKS_AU,
 res=[
  R('۱۱٫۳ میلیون تن با ۷٫۹ گرم در تن طلا (حدود ۲٫۹ میلیون اونس)، عیار حد ۱ گرم در تن', '11.3 Mt @ 7.9 g/t Au (about 2.9 Moz), 1.0 g/t cut-off',
    'منبع استنباطی؛ گزارش فنی نهایی Anglo American، ۲۰۰۱ (تنها رقم با عیار حد مشخص)', 'Inferred; Anglo American final technical report, 2001 (the only figure with a stated cut-off)',
    ['anglo2001'], 'M', calc=[(11.3, 7.9)], lab=('Anglo ۲۰۰۱', 'Anglo 2001')),
  R('۱۰۸ تن طلا «ذخیرهٔ قطعی» و ۵۰ تن نقره', '108 t Au “proven reserves” + 50 t Ag', 'آبان ۱۳۹۵؛ کد گزارش‌دهی ذکر نشده', 'November 2016; no reporting code stated',
    ['eghtesad2016'], 'ML', direct=108, lab=('۱۳۹۵ (۲۰۱۶)', '2016')),
  R('۱۵۵ تن طلا با ۲٫۶۳ گرم در تن', '155 t Au @ 2.63 g/t', 'به نقل از «شرکت معدن‌زمین، ۲۰۲۰» در یک مقاله', 'Cited as “Madan-Zamin Company, 2020” in a paper',
    ['jme977'], 'L', direct=155, lab=('«۲۰۲۰»', '“2020”')),
  R('افزایش کانسنگ قطعی از ۲۷ به ۴۳ میلیون تن؛ «۱۱۶ mt» طلای قابل استخراج؛ عمر معدن از ۲۵ به ۶۵ سال', 'Proven ore up from 27 to 43 Mt; “116 mt” extractable gold; mine life from 25 to 65 years',
    'اظهارات مدیریت، دی ۱۴۰۳؛ «۱۱۶» اینجا ۱۱۶ تن طلا خوانده شده است (یادداشت کارشناسی را ببینید)', 'Management statement, December 2024; “116” is read here as 116 t of gold (see the expert note)',
    ['tehrantimes_zar', 'eghtesad2024'], 'M', direct=116, lab=('۱۴۰۳ (۲۰۲۴)', '2024'), dn=('تفسیر نویسنده', 'author’s reading')),
  R('حدود ۴۳ میلیون تن با ۲٫۷ گرم در تن؛ پیش‌تر حدود ۲۷ میلیون تن با ۴ گرم در تن', 'About 43 Mt @ 2.7 g/t; earlier about 27 Mt @ 4 g/t', 'گزارش‌های فارسی بدون تاریخ', 'Undated Persian reports',
    ['donyayemadan_zar', 'bariteco_gold'], 'L', chart=False),
 ],
 fa=dict(
  name='زرشوران', province='آذربایجان غربی', type_short='طلای رسوب‌میزبان (کارلین‌گونه)',
  title='کانسار طلای زرشوران تکاب: زمین‌شناسی کارلین‌گونه و ارقام ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار طلای زرشوران',
  desc='کانسار طلای زرشوران در شهرستان تکاب آذربایجان غربی: طلای نامرئی در پیریت آرسنیک‌دار، سن میوسن، کانی‌های آرسنیک و جیوه و تحلیل ارقام ذخیرهٔ متناقض.',
  lede='زرشوران، حدود ۳۵ کیلومتری شمال تکاب، روشن‌ترین نمونهٔ طلای رسوب‌میزبان کارلین‌گونه در ایران است. ارقام ذخیرهٔ آن تا چند برابر با هم اختلاف دارند و این صفحه با محاسبهٔ طلای محتوا نشان می‌دهد کدام ارقام با هم سازگارند.',
  coord_note='نقطهٔ Mindat و مختصات مقاله‌های ۱۹۹۹ تا ۲۰۰۳ همه در فاصلهٔ ۰٫۷ کیلومتری این نقطه‌اند[[mindat25142]]. نقطهٔ دوم Mindat در شهرستان شاهین‌دژ حدود ۳۲ کیلومتر دورتر است و نباید به کار رود[[mindat445510]].',
  facts=[
   ('aka', 'Zarshouran، Zareh Shuran'),
   ('loc', 'استان آذربایجان غربی؛ شهرستان تکاب، حدود ۳۵ کیلومتری شمال تکاب (۳۰ تا ۴۲ کیلومتر در منابع مختلف)[[usgs_sedau35]]'),
   ('comm', 'طلا؛ در ۱۳۹۵ همراه با طلا ۵۰ تن نقره گزارش شد (اطمینان کم تا متوسط)[[eghtesad2016]]'),
   ('type', 'طلای پراکندهٔ رسوب‌میزبان «کارلین‌گونه»[[mehrabi1999]][[asadi2000]]؛ در پایگاه USGS از نوع کارلین[[usgs_sedau35]]'),
   ('belt', 'ناحیهٔ تکاب؛ نهشت طلا هم‌زمان با بالاآمدگی مجموعهٔ هسته‌ای دگرگونی ایمان‌خان[[zhang2025]]'),
   ('host', 'شیل سیاه سیلتی، آهکی و کربن‌دار با دولومیت و آهک[[mehrabi1999]]؛ سن میزبان از «پرکامبرین پسین» به واحدهای کامبرین بازنگری شده است (اطمینان کم تا متوسط)[[jme977]]'),
   ('age', 'کانی‌سازی ۲۰٫۶ تا ۱۴٫۵ میلیون سال: آرگون–آرگون مسکوویت ۲۰٫۵۹ ± ۰٫۳۲ و U–Pb کلسیت ۱۴٫۵ ± ۲٫۰ میلیون سال[[zhang2025]]'),
   ('op', 'متعلق به ایمیدرو و بهره‌برداری شرکت زرشوران؛ تولید حدود یک تن شمش طلا در سال گزارش شده است[[tehrantimes_zar]]'),
  ],
  sections=[
   ('زمین‌شناسی و سن', '''<p>طلای زرشوران پراکنده و رسوب‌میزبان است و پژوهشگران آن را «کارلین‌گونه» توصیف کرده‌اند[[mehrabi1999]][[asadi2000]]. سنگ میزبان شیل سیاه سیلتی، آهکی و کربن‌دار همراه با دولومیت و آهک است[[mehrabi1999]] که سن آن در پژوهش‌های تازه‌تر از «پرکامبرین پسین» به واحدهای کامبرین بازنگری شده است[[jme977]].</p>
<p>Zhang و همکاران (۲۰۲۵) کانی‌سازی را به ۲۰٫۶ تا ۱۴٫۵ میلیون سال پیش نسبت می‌دهند: سن آرگون–آرگون مسکوویت ۲۰٫۵۹ ± ۰٫۳۲ و سن U–Pb کلسیت ۱۴٫۵ ± ۲٫۰ میلیون سال. آن‌ها نهشت طلا را به بالاآمدگی مجموعهٔ هسته‌ای دگرگونی ایمان‌خان مرتبط می‌دانند[[zhang2025]]. Yang و همکاران (۲۰۲۶) آمیختگی سیالات ماگمایی با شورابه‌های حوضه‌ای را پیشنهاد کرده‌اند[[yang2026]].</p>'''),
   ('کانی‌شناسی', '''<p>اورپیمان، رآلگار، استیبنیت، گچلیت، سینابر، کانی‌های تالیم، باریت و پیریت طلا–آرسنیک‌دار از کانی‌های شناخته‌شدهٔ زرشوران‌اند و طلا به‌صورت «نامرئی» (زیرمیکروسکوپی) در پیریت آرسنیک‌دار، اسفالریت و اورپیمان جای دارد[[mehrabi1999]][[asadi2000]]. زرشوران محل نمونهٔ اصلی (type locality) کانی دالیرانیت (PbHgAs₂S₆) است[[daliranite]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('ناحیهٔ تکاب', '''<p>زرشوران و آق‌دره ۱۲٫۵ کیلومتر از هم فاصله دارند و ۲۶ تا ۳۵ کیلومتر با کانسار روی انگوران؛ این سه با هم ناحیهٔ معدنی تکاب را می‌سازند. صفحه‌های <a href="/atlas/agh-darreh/">آق‌دره</a> و <a href="/atlas/angouran/">انگوران</a> را ببینید.</p>'''),
  ],
  expert=[
   ('طلای محتوا: کدام ارقام با هم سازگارند؟', '''<p>منبع استنباطی Anglo American در ۲۰۰۱ (۱۱٫۳ میلیون تن با ۷٫۹ گرم در تن در عیار حد ۱ گرم در تن) حدود ۸۹ تن طلا دارد و تنها رقمی است که عیار حد آن ذکر شده است. اعلام دی ۱۴۰۳، مبنی بر افزایش کانسنگ قطعی از ۲۷ به ۴۳ میلیون تن و «۱۱۶ mt» طلای قابل استخراج، فقط زمانی منطقی است که «۱۱۶» را ۱۱۶ تن طلا بخوانیم، نه ۱۱۶ میلیون تن کانسنگ: ۴۳ میلیون تن با عیار ۲٫۷ گرم در تن (عیاری که یک گزارش فارسی به مدیرعامل نسبت داده است) دقیقاً ۱۱۶ تن طلا می‌شود.</p>
<p>اگر رقم قبلی ۲۷ میلیون تن با حدود ۴ گرم در تن بوده باشد (حدود ۱۰۸ تن، برابر «ذخیرهٔ قطعی» اعلام‌شده در ۱۳۹۵)، افزایش ۵۹ درصدی کانسنگ فقط حدود ۷ درصد طلای بیشتر آورده است؛ الگویی که بیشتر با پایین آمدن عیار حد سازگار است تا کشف طلای تازه. هر دو ورودی این مقایسه اطمینان کمی دارند، اما همین حساب ساده نشان می‌دهد که تناژ به‌تنهایی معیار مناسبی برای مقایسه نیست.</p>'''),
  ]),
 en=dict(
  name='Zarshuran', province='West Azerbaijan', type_short='Sediment-hosted gold (Carlin-like)',
  title='Zarshuran Gold Deposit, Takab: Carlin-Like Geology and Resource Figures | Ali Alinaghi',
  h1='Zarshuran gold deposit: geology and resources',
  desc='The Zarshuran gold deposit in Takab County, West Azerbaijan: invisible gold in arsenian pyrite, Miocene ages, arsenic and mercury minerals, and a reconciliation of conflicting resource figures.',
  lede='Zarshuran, about 35 km north of Takab, is Iran’s clearest example of sediment-hosted, Carlin-like gold. Its resource figures differ several-fold, and this page works out the contained gold in each to show which of them agree.',
  coord_note='The Mindat point and the coordinates in 1999–2003 papers all lie within 0.7 km of this point[[mindat25142]]. A second Mindat pin in Shahin Dezh County is about 32 km away and should not be used[[mindat445510]].',
  facts=[
   ('aka', 'Zarshouran, Zareh Shuran; Persian: زرشوران'),
   ('loc', 'West Azerbaijan Province; Takab County, about 35 km north of Takab (30–42 km in other sources)[[usgs_sedau35]]'),
   ('comm', 'Gold; 50 t of silver reported alongside the gold in 2016 (low–medium confidence)[[eghtesad2016]]'),
   ('type', 'Sediment-hosted disseminated, “Carlin-like” gold[[mehrabi1999]][[asadi2000]]; Carlin-type in the USGS database[[usgs_sedau35]]'),
   ('belt', 'Takab district; gold deposited during exhumation of the Iman Khan metamorphic core complex[[zhang2025]]'),
   ('host', 'Black silty, calcareous and carbonaceous shale with dolomite and limestone[[mehrabi1999]]; host age revised from “late Precambrian” to Cambrian units (low–medium confidence)[[jme977]]'),
   ('age', 'Mineralisation 20.6–14.5 Ma: muscovite Ar–Ar 20.59 ± 0.32 Ma and calcite U–Pb 14.5 ± 2.0 Ma[[zhang2025]]'),
   ('op', 'IMIDRO-owned and run by the Zarshouran company; reported output about 1 t of gold bars a year[[tehrantimes_zar]]'),
  ],
  sections=[
   ('Geology and age', '''<p>Zarshuran’s gold is disseminated and sediment-hosted, and researchers describe it as “Carlin-like”[[mehrabi1999]][[asadi2000]]. The host is black silty, calcareous and carbonaceous shale with dolomite and limestone[[mehrabi1999]], whose age newer work has revised from “late Precambrian” to Cambrian units[[jme977]].</p>
<p>Zhang et al. (2025) date the mineralisation to 20.6–14.5 Ma, with a muscovite Ar–Ar age of 20.59 ± 0.32 Ma and a calcite U–Pb age of 14.5 ± 2.0 Ma, and tie it to the exhumation of the Iman Khan metamorphic core complex[[zhang2025]]. Yang et al. (2026) invoke magmatic fluids mixing with basinal brines[[yang2026]].</p>'''),
   ('Mineralogy', '''<p>Orpiment, realgar, stibnite, getchellite, cinnabar, thallium minerals, barite and Au–As pyrite are among Zarshuran’s minerals, and the gold is “invisible” (sub-microscopic) in arsenian pyrite, sphalerite and orpiment[[mehrabi1999]][[asadi2000]]. Zarshuran is the type locality of the mineral daliranite (PbHgAs₂S₆)[[daliranite]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('The Takab district', '''<p>Zarshuran and Agh-Darreh lie 12.5 km apart and 26–35 km from the Angouran zinc deposit; together the three form the Takab mining district. See the <a href="/en/atlas/agh-darreh/">Agh-Darreh</a> and <a href="/en/atlas/angouran/">Angouran</a> pages.</p>'''),
  ],
  expert=[
   ('Contained gold: which figures agree?', '''<p>Anglo American’s 2001 inferred resource (11.3 Mt at 7.9 g/t at a 1.0 g/t cut-off) holds about 89 t of gold and is the only figure with a stated cut-off grade. The December 2024 announcement — proven ore up from 27 to 43 Mt and “116 mt” of extractable gold — is internally consistent only if “116” means 116 tonnes of gold, not 116 million tonnes of ore: 43 Mt at 2.7 g/t (the grade a Persian report attributes to the chief executive) is exactly 116 t.</p>
<p>If the earlier 27 Mt carried about 4 g/t (about 108 t, matching the “proven reserve” reported in 2016), the 2024 upgrade added 59% more ore but only about 7% more gold — a pattern that fits a lower cut-off grade better than new ounces. Both inputs are low-confidence, but the arithmetic shows that tonnage alone is a poor basis for comparison.</p>'''),
  ]),
)

AGH_DARREH = dict(
 slug='agh-darreh', commodity='au', ntype='carlin', metal='au',
 lat=36.6667, lon=47.0167, coord_src='Daliran (2008)', coord_cite='mindat_ref156983', coord_conf='MH',
 published=P, updated=P, related=['zarshuran', 'angouran', 'sari-gunay'], links=LINKS_AU,
 res=[
  R('۵٫۱ میلیون تن قطعی + ۹٫۷ میلیون تن احتمالی با ۱٫۲۵ ppm طلا', '5.1 Mt proven + 9.7 Mt probable @ 1.25 ppm Au', 'رده‌بندی قطعی/احتمالی ایرانی؛ بدون تاریخ', 'Iranian proven/probable categories; undated',
    ['fawp_agdarreh'], 'ML', calc=[(5.1, 1.25), (9.7, 1.25)]),
  R('حدود ۷ میلیون تن دیگر با ۰٫۸۵ تا ۱٫۲ ppm قابل افزودن', 'About 7 Mt more @ 0.85–1.2 ppm could be added',
    'برآورد شرکت، حدود ۱۴۰۰؛ «ذخیرهٔ قطعی ۴۲۰ هزار تنی» همان صفحه به تراورتن مربوط است، نه کانسنگ طلا', 'Company estimate, about 2021; the 420,000 t “proven reserve” on the same page refers to travertine, not gold ore',
    ['ifb_agdarreh'], 'ML'),
 ],
 fa=dict(
  name='آق‌دره', province='آذربایجان غربی', type_short='طلای کربنات‌میزبان (کارلین‌گونه)',
  title='کانسار طلای آق‌دره تکاب: زمین‌شناسی و کانی‌سازی | علی علینقی',
  h1='زمین‌شناسی کانسار طلای آق‌دره',
  desc='کانسار طلای آق‌دره در شهرستان تکاب: طلای اپی‌ترمال کربنات‌میزبان با شباهت به تیپ کارلین در میدان زمین‌گرمایی تکاب، توالی دگرسانی، طلای نامرئی و ذخیرهٔ منتشرشده.',
  lede='آق‌دره، حدود ۱۲٫۵ کیلومتری غرب–جنوب‌غرب زرشوران، دومین کانسار طلای کارلین‌گونهٔ ناحیهٔ تکاب است. بهره‌بردار آن، پویا زرکان آق‌دره، با نماد «فزر» در فرابورس ایران معامله می‌شود.',
  coord_note='مختصات از Daliran (۲۰۰۸) گرفته شده و فقط در حد دقیقهٔ قوسی دقیق است (حدود ۱ تا ۱٫۵ کیلومتر)[[mindat_ref156983]]. «Aghdarreh» در ویکی‌پدیای انگلیسی روستایی در شهرستان خوی است و ربطی به این کانسار ندارد[[wp_aghdarreh_village]].',
  facts=[
   ('aka', 'Agdarreh، Aq-Darreh'),
   ('loc', 'استان آذربایجان غربی؛ شهرستان تکاب[[mindat_ref156983]]'),
   ('comm', 'طلا و نقره؛ ظرفیت ۷۰۰ کیلوگرم شمش طلا و ۶۸۴ کیلوگرم نقره (اطمینان کم تا متوسط)[[ifb_agdarreh]]'),
   ('type', '«اپی‌ترمال کربنات‌میزبان» با «شباهت‌های بسیار به تیپ کارلین»[[daliran2008]]؛ «کارلین‌گونه»[[daliran2018]]'),
   ('belt', 'میدان زمین‌گرمایی تکاب در کمان آتشفشانی سنوزوئیک ارومیه–دختر[[mindat_ref156983]]'),
   ('host', 'آهک ریفی میوسن (پیشین) که با سیالات گرمابی شسته شده است[[daliran2008]]'),
   ('age', 'سن مستقیم کانی‌سازی در دسترس نیست؛ چون میزبان آهک میوسن پیشین است، کانی‌سازی جوان‌تر از آن است'),
   ('op', 'شرکت پویا زرکان آق‌دره، با نماد «فزر» در فرابورس ایران از بهمن ۱۳۹۹[[bambo_fazar]]'),
  ],
  sections=[
   ('زمین‌شناسی', '''<p>Daliran (۲۰۰۸) آق‌دره را کانسار «طلای اپی‌ترمال کربنات‌میزبان» در میدان زمین‌گرمایی تکاب با «شباهت‌های بسیار به تیپ کارلین» توصیف می‌کند[[daliran2008]] و فصلی در مجموعهٔ Reviews in Economic Geology انجمن زمین‌شناسان اقتصادی (۲۰۱۸) آن را «کارلین‌گونه» می‌نامد[[daliran2018]]. میزبان، آهک ریفی میوسن پیشین است که سیالات گرمابی آن را شسته‌اند؛ بنابراین کانی‌سازی جوان‌تر از میوسن پیشین است، هرچند سن مستقیمی برای آن در دسترس نیست.</p>'''),
   ('توالی دگرسانی و کانی‌سازی', '''<p>Daliran توالی زیر را توصیف کرده است: کربنات‌زدایی؛ سیلیسی‌شدن همراه با پیریت و اسفالریت؛ سیلیسی‌شدن همراه با گالن، سولفیدهای سرب–آنتیموان–آرسنیک و تلوریدها؛ و در پایان سینابر و باریت تأخیری. طلا در کانسنگ سولفیدی به‌صورت نامرئی در پیریت آرسنیک‌دار و در کانسنگ اکسیدی به‌صورت طلای آزاد دیده می‌شود[[daliran2008]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('ناحیهٔ تکاب', '''<p>آق‌دره ۱۲٫۵ کیلومتر با زرشوران فاصله دارد و این دو همراه با کانسار روی انگوران ناحیهٔ معدنی تکاب را می‌سازند. صفحه‌های <a href="/atlas/zarshuran/">زرشوران</a> و <a href="/atlas/angouran/">انگوران</a> را ببینید.</p>'''),
  ],
  expert=[
   ('کانسنگ اکسیدی و سولفیدی', '''<p>در آق‌دره، طلا در کانسنگ اکسیدی به‌صورت طلای آزاد و در کانسنگ سولفیدی به‌صورت نامرئی در پیریت آرسنیک‌دار دیده می‌شود. این دو نوع کانسنگ بازیابی متفاوتی دارند: طلای آزاد کانسنگ اکسیدی با سیانوراسیون معمول به‌خوبی بازیابی می‌شود، اما طلای نامرئی در سولفیدها ممکن است دیرگداز باشد. بنابراین مرز اکسایش باید به‌عنوان مرز دامنه مدل شود و عیار حد برای هر نوع کانسنگ جداگانه محاسبه شود. ذخیرهٔ منتشرشده (حدود ۱۸٫۵ تن طلای محتوا) بدون این تفکیک ارزش اقتصادی را به‌درستی نشان نمی‌دهد.</p>'''),
  ]),
 en=dict(
  name='Agh-Darreh', province='West Azerbaijan', type_short='Carbonate-hosted gold (Carlin-style)',
  title='Agh-Darreh Gold Deposit, Takab: Geology and Mineralisation | Ali Alinaghi',
  h1='Agh-Darreh gold deposit: geology and mineralisation',
  desc='The Agh-Darreh gold deposit in Takab County: a carbonate-hosted epithermal gold deposit with Carlin-type affinities in the Takab geothermal field, its alteration sequence, invisible gold and the published resource.',
  lede='Agh-Darreh, about 12.5 km west-southwest of Zarshuran, is the second Carlin-style gold deposit of the Takab district. Its operator, Pouya Zarkan Aghdarreh, trades on Iran Fara Bourse under the symbol «فزر».',
  coord_note='Coordinates from Daliran (2008), precise only to the arc-minute (about 1–1.5 km)[[mindat_ref156983]]. The “Aghdarreh” in English Wikipedia is a village in Khoy County and unrelated to this deposit[[wp_aghdarreh_village]].',
  facts=[
   ('aka', 'Agdarreh, Aq-Darreh; Persian: آق‌دره'),
   ('loc', 'West Azerbaijan Province; Takab County[[mindat_ref156983]]'),
   ('comm', 'Gold and silver; capacity of 700 kg gold and 684 kg silver bullion (low–medium confidence)[[ifb_agdarreh]]'),
   ('type', '“Carbonate rock-hosted epithermal” with “many similarities to Carlin-type ore”[[daliran2008]]; “Carlin-style”[[daliran2018]]'),
   ('belt', 'Takab geothermal field in the Cenozoic Urumieh–Dokhtar volcanic arc[[mindat_ref156983]]'),
   ('host', 'Hydrothermally leached (early) Miocene reef limestone[[daliran2008]]'),
   ('age', 'No direct ore age; since the host is early-Miocene limestone, the ore is younger'),
   ('op', 'Pouya Zarkan Aghdarreh, listed on Iran Fara Bourse as «فزر» since Bahman 1399 (January–February 2021)[[bambo_fazar]]'),
  ],
  sections=[
   ('Geology', '''<p>Daliran (2008) describes Agh-Darreh as a “carbonate rock-hosted epithermal” gold deposit in the Takab geothermal field with “many similarities to Carlin-type ore”[[daliran2008]], and a 2018 chapter in the Society of Economic Geologists’ Reviews in Economic Geology calls it “Carlin-style”[[daliran2018]]. The host is hydrothermally leached early-Miocene reef limestone, so the ore must be younger than early Miocene, although it has no direct age.</p>'''),
   ('Alteration and mineralisation sequence', '''<p>Daliran describes the following sequence: decalcification; silicification with pyrite and sphalerite; silicification with galena, Pb–Sb–As sulphides and tellurides; and finally late cinnabar and barite. Gold is invisible in arsenian pyrite in the sulphide ore and occurs as native gold in the oxide ore[[daliran2008]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('The Takab district', '''<p>Agh-Darreh lies 12.5 km from Zarshuran, and the two, with the Angouran zinc deposit, form the Takab mining district. See the <a href="/en/atlas/zarshuran/">Zarshuran</a> and <a href="/en/atlas/angouran/">Angouran</a> pages.</p>'''),
  ],
  expert=[
   ('Oxide and sulphide ore', '''<p>At Agh-Darreh, gold occurs as free gold in oxide ore and as invisible gold in arsenian pyrite in sulphide ore. The two ore types recover differently: free gold in oxide ore responds well to conventional cyanidation, while invisible gold in sulphides may be refractory. The oxidation boundary should therefore be modelled as a domain boundary, and the cut-off grade calculated separately for each ore type. The published reserve (about 18.5 t of contained gold) does not show economic value properly without that split.</p>'''),
  ]),
)

SARI_GUNAY = dict(
 slug='sari-gunay', commodity='au', ntype='epithermal', metal='au',
 lat=35.2000, lon=48.0833, coord_src='PorterGeo', coord_cite='porter1256', coord_conf='M',
 published=P, updated=P, related=['zarshuran', 'agh-darreh', 'muteh'], links=LINKS_AU,
 res=[
  R('۵۲ میلیون تن کانسنگ اکسیدی با ۱٫۷۷ گرم در تن طلا', '52 Mt oxide @ 1.77 g/t Au', '«منبع نشان‌داده‌شده (Indicated) فقط کانسنگ اکسیدی»؛ Bartram (۲۰۰۵) به نقل Richards و همکاران (۲۰۰۶)', '“Indicated resource of just oxide ore”; Bartram (2005), cited by Richards et al. (2006)',
    ['jge2014_sg', 'scirep2026_sg'], 'M', calc=[(52, 1.77)], lab=('Bartram ۲۰۰۵', 'Bartram 2005')),
  R('حدود ۵۵ میلیون تن با ۱٫۶ گرم در تن (عیار حد ۰٫۵ گرم در تن) و در همان مطالعه ۲۱٫۰۷۲ میلیون تن با ۱٫۶ ppm', 'About 55 Mt @ 1.6 g/t (0.5 g/t cut-off) and 21.072 Mt @ 1.6 ppm in the same study',
    'مطالعهٔ برنامه‌ریزی تولید، حدود ۲۰۲۱؛ ناسازگاری درونی', 'Mine-planning study, about 2021; internally inconsistent',
    ['mineplan_sg'], 'L', calc=[(55, 1.6)], lab=('مطالعهٔ ۲۰۲۱', '2021 study')),
  R('«حدود ۱۰۰ تن»', '“About 100 tons”', 'صفحهٔ سازمان زمین‌شناسی کشور', 'Geological Survey of Iran page', ['gsi_sg'], 'L', direct=100, lab=('سازمان زمین‌شناسی', 'GSI')),
  R('«۴۵ تن با ۱٫۷۷ گرم در تن»', '“45 t @ 1.77 g/t”', 'جدول یک مقالهٔ مروری؛ با رقم ۵۲ میلیون تن ناسازگار', 'Review table; conflicts with the 52 Mt figure', ['review_sg'], 'L', direct=45, lab=('مقالهٔ مروری', 'Review')),
 ],
 fa=dict(
  name='ساری‌گونی', province='کردستان', type_short='طلای اپی‌ترمال',
  title='کانسار طلای ساری‌گونی قروه: زمین‌شناسی اپی‌ترمال و ارقام ذخیره | علی علینقی',
  h1='زمین‌شناسی کانسار طلای ساری‌گونی',
  desc='کانسار طلای اپی‌ترمال ساری‌گونی در شهرستان قروه کردستان: مجموعهٔ آتشفشانی میوسن، سن‌سنجی، رگه‌های کوارتز–استیبنیت–رآلگار، لیچینگ توده‌ای و ارقام ذخیره.',
  lede='ساری‌گونی، حدود ۶۰ کیلومتری شمال‌غرب همدان، کانسار طلای اپی‌ترمال در یک مجموعهٔ آتشفشانی میوسن است که Rio Tinto در سال ۱۹۹۹ کشف کرد و کانسنگ اکسیدی آن با لیچینگ توده‌ای فرآوری می‌شود.',
  coord_note='مختصات تقریبی است و از PorterGeo گرفته شده است. نقطهٔ Mindat «برآوردی» است و حدود ۱۳۶ کیلومتر خطا دارد[[mindat146021]]. دو تپهٔ ساری‌گونی و آق‌داغ حدود ۲ کیلومتر از هم فاصله دارند.',
  facts=[
   ('aka', 'Sari Gunay، ساریگونی'),
   ('loc', 'استان کردستان؛ شهرستان قروه[[asriran_sg]]، حدود ۶۰ کیلومتری شمال‌غرب همدان[[porter1256]]'),
   ('comm', 'طلا، با نقره به‌عنوان محصول جانبی[[iribnews_sg]]'),
   ('type', 'اپی‌ترمال در یک مجموعهٔ آتشفشانی لاتیتی تا تراکیتی میوسن با قلیاییت ملایم[[richards2006]]؛ تفکیک سولفید پایین یا حدواسط تأیید نشد'),
   ('host', 'سنگ‌های آتشفشانی و نفوذی لاتیت–تراکیت[[richards2006]]؛ مقاله‌ای در ۲۰۲۱ آن‌ها را داسیت–ریولیت نامیده است[[jeg2021_sg]]'),
   ('age', 'سنگ میزبان ۱۱٫۷ تا ۱۱٫۰ میلیون سال؛ بهترین برآورد سن دگرسانی سرسیتی ۱۰٫۷ میلیون سال (آرگون–آرگون)[[richards2006]]'),
   ('op', 'شرکت معدنی زرکوه، تأسیس‌شده در ژانویهٔ ۲۰۰۴ پس از کشف کانسار توسط Rio Tinto در ۱۹۹۹[[zarkuh]][[scirep2026_sg]]؛ لیچینگ توده‌ای کانسنگ اکسیدی[[akhbaremadan_sg]]'),
  ],
  sections=[
   ('زمین‌شناسی و سن', '''<p>Richards و همکاران (۲۰۰۶) ساری‌گونی را کانسار طلای اپی‌ترمال در یک مجموعهٔ آتشفشانی لاتیتی تا تراکیتی میوسن با قلیاییت ملایم توصیف کرده‌اند. سن سنگ‌های آتشفشانی و نفوذی میزبان ۱۱٫۷ تا ۱۱٫۰ میلیون سال و بهترین برآورد سن دگرسانی سرسیتی ۱۰٫۷ میلیون سال است[[richards2006]]. مقاله‌ای در سال ۲۰۲۱ سنگ‌های میزبان را داسیت–ریولیت نامیده است[[jeg2021_sg]]. کانسار دو تپه دارد، ساری‌گونی و آق‌داغ، که حدود ۲ کیلومتر از هم فاصله دارند[[porter1256]].</p>'''),
   ('کانی‌سازی و دگرسانی', '''<p>رگه‌های کوارتز–پیریت–استیبنیت–رآلگار–اورپیمان میزبان کانی‌سازی‌اند و طلا به‌صورت محلول جامد و ادخال‌های ریز در پیریت آرسنیک‌دار جای دارد[[jeg2021_sg]]. دگرسانی سرسیتی مرحلهٔ اولیهٔ سامانه است[[richards2006]].</p>'''),
   ('ارقام ذخیره و منابع منتشرشده', '''{{res}}'''),
   ('بهره‌برداری', '''<p>شرکت معدنی زرکوه در ژانویهٔ ۲۰۰۴، پس از کشف کانسار توسط Rio Tinto در ۱۹۹۹، تأسیس شد[[zarkuh]][[scirep2026_sg]] و کانسنگ اکسیدی را با لیچینگ توده‌ای فرآوری می‌کند[[akhbaremadan_sg]]. منابع، تاریخچهٔ مالکیت شرکت را به سه شکل ناسازگار روایت کرده‌اند. بر سر سهم یک‌درصدی درآمد برای جوامع محلی نیز اختلاف گزارش شده است[[mehrnews_sg]].</p>'''),
  ],
  expert=[
   ('۹۲ تن یا ۴۵ تن؟', '''<p>منبع اکسیدی ۵۲ میلیون تن با ۱٫۷۷ گرم در تن حدود ۹۲ تن طلا دارد. این رقم با «حدود ۱۰۰ تن» سازمان زمین‌شناسی سازگار است، به شرط آنکه آن را طلای محتوا بخوانیم، اما با «۴۵ تن» یک مقالهٔ مروری سازگار نیست؛ آن رقم احتمالاً کمیت یا بخش دیگری از کانسار را نشان می‌دهد. یک مطالعهٔ برنامه‌ریزی تولید هم در یک متن دو تناژ ناسازگار (حدود ۵۵ و ۲۱ میلیون تن) با عیار ۱٫۶ گرم در تن آورده است.</p>
<p>چون فقط کانسنگ اکسیدی با لیچینگ توده‌ای فرآوری می‌شود، تفکیک منابع اکسیدی و سولفیدی و تعیین بازیابی لیچینگ برای هر بخش پایهٔ هر ارزیابی اقتصادی است.</p>'''),
  ]),
 en=dict(
  name='Sari Gunay', province='Kurdistan', type_short='Epithermal gold',
  title='Sari Gunay Gold Deposit, Qorveh: Epithermal Geology and Resource Figures | Ali Alinaghi',
  h1='Sari Gunay gold deposit: geology and resources',
  desc='The Sari Gunay epithermal gold deposit in Qorveh County, Kurdistan: a Miocene volcanic complex, geochronology, quartz–stibnite–realgar veins, heap leaching and published resource figures.',
  lede='Sari Gunay, about 60 km northwest of Hamedan, is an epithermal gold deposit in a Miocene volcanic complex. Rio Tinto discovered it in 1999, and its oxide ore is processed by heap leaching.',
  coord_note='Approximate coordinates from PorterGeo. Mindat’s point is an “estimate” with an error of about 136 km[[mindat146021]]. The Sari Gunay and Agh Dagh hills are about 2 km apart.',
  facts=[
   ('aka', 'Persian: ساری‌گونی، ساریگونی'),
   ('loc', 'Kurdistan Province; Qorveh County[[asriran_sg]], about 60 km northwest of Hamedan[[porter1256]]'),
   ('comm', 'Gold, with silver as a by-product[[iribnews_sg]]'),
   ('type', 'Epithermal, in a mildly alkaline latitic-to-trachytic Miocene volcanic complex[[richards2006]]; low- vs intermediate-sulphidation not confirmed'),
   ('host', 'Latite–trachyte volcanic and intrusive rocks[[richards2006]]; a 2021 paper calls them dacite–rhyolite[[jeg2021_sg]]'),
   ('age', 'Host rocks 11.7–11.0 Ma; best estimate for sericitic alteration 10.7 Ma (Ar–Ar)[[richards2006]]'),
   ('op', 'Zarkuh Mining Co., founded in January 2004 after Rio Tinto discovered the deposit in 1999[[zarkuh]][[scirep2026_sg]]; heap leaching of oxide ore[[akhbaremadan_sg]]'),
  ],
  sections=[
   ('Geology and age', '''<p>Richards et al. (2006) describe Sari Gunay as an epithermal gold deposit in a mildly alkaline latitic-to-trachytic Miocene volcanic complex. The host volcanic and intrusive rocks are 11.7–11.0 Ma, and the best estimate for sericitic alteration is 10.7 Ma[[richards2006]]. A 2021 paper calls the host rocks dacite–rhyolite instead[[jeg2021_sg]]. The deposit has two hills, Sari Gunay and Agh Dagh, about 2 km apart[[porter1256]].</p>'''),
   ('Mineralisation and alteration', '''<p>Quartz–pyrite–stibnite–realgar–orpiment veins host the mineralisation, and gold sits in arsenian pyrite as solid solution and fine inclusions[[jeg2021_sg]]. Sericitic alteration is an early stage of the system[[richards2006]].</p>'''),
   ('Published resource figures', '''{{res}}'''),
   ('Operations', '''<p>Zarkuh Mining Co. was founded in January 2004, after Rio Tinto discovered the deposit in 1999[[zarkuh]][[scirep2026_sg]], and heap-leaches the oxide ore[[akhbaremadan_sg]]. Sources describe the company’s ownership history in three incompatible ways. A dispute over a 1% revenue share for local communities has also been reported[[mehrnews_sg]].</p>'''),
  ],
  expert=[
   ('92 t or 45 t?', '''<p>The oxide resource of 52 Mt at 1.77 g/t contains about 92 t of gold. That agrees with the Geological Survey’s “about 100 tons” if that is read as contained gold, but not with a review’s “45 t”, which probably refers to a different quantity or part of the deposit. A mine-planning study also gives two incompatible tonnages (about 55 and 21 Mt) at 1.6 g/t in the same text.</p>
<p>Since only oxide ore is heap-leached, splitting oxide from sulphide resources and establishing heap-leach recovery for each is the basis of any economic assessment.</p>'''),
  ]),
)

MUTEH = dict(
 slug='muteh', commodity='au', ntype='orogenic', metal='au',
 lat=None, lon=None, coord_src='', coord_cite=None, coord_conf='L',
 published=P, updated=P, related=['sari-gunay', 'zarshuran', 'irankuh'], links=LINKS_AU,
 res=[
  R('حدود ۲ میلیون تن کانسنگ با حدود ۲ گرم در تن؛ نُه کانسار روی هم بیش از ۱٫۲ میلیون تن', 'About 2 Mt of ore @ about 2 g/t; nine deposits totalling more than 1.2 Mt', 'منابع فارسی بدون تاریخ', 'Undated Persian sources',
    ['beytoote_muteh', 'moutehgold'], 'L', chart=False),
 ],
 fa=dict(
  name='موته', province='اصفهان', type_short='طلای میزبان دگرگونی',
  title='کانسار طلای موته اصفهان: زمین‌شناسی و سن کانی‌سازی | علی علینقی',
  h1='زمین‌شناسی کانسارهای طلای موته',
  desc='ناحیهٔ طلای موته در استان اصفهان: طلای میزبان سنگ‌های دگرگونی پهنهٔ سنندج–سیرجان، سن ائوسن کانی‌سازی، دیدگاه کوهزایی، دگرسانی و تولید گزارش‌شده.',
  lede='موته در استان اصفهان ناحیه‌ای از کانسارهای طلای میزبان سنگ‌های دگرگونی است که سالنامهٔ مواد معدنی ۱۹۷۷ آن را کانسار رگه‌ای طلا–پیریت–کوارتز توصیف کرده است. Moritz و همکاران (۲۰۰۶) کانی‌سازی را به ائوسن نسبت دادند؛ با این حال حتی موقعیت دقیق معادن آن در پایگاه‌های داده هم‌خوان نیست.',
  coord_note='موقعیت این کانسار منتشر نمی‌شود: نقطهٔ معدن در Mindat[[mindat28816]]، نقطهٔ پیت سنجده[[mindat28815]] و روستای موته[[wp_muteh]] تا حدود ۴۲ کیلومتر با هم فاصله دارند. مختصات پس از تطبیق با نقشهٔ زمین‌شناسی یا نقشهٔ موقعیت یک مقالهٔ داوری‌شده افزوده می‌شود.',
  facts=[
   ('aka', 'Mouteh، Mooteh'),
   ('loc', 'استان اصفهان؛ شهرستان در منابع ناهم‌خوان است: گلپایگان (Mindat)، «برخوار و میمه»[[irandaily2019]] و میمه؛ با روستای موته در بخش وزوان اشتباه نشود[[wp_muteh]]'),
   ('comm', 'طلا؛ «کانسار رگه‌ای طلا–پیریت–کوارتز» در سالنامهٔ مواد معدنی ۱۹۷۷[[myb1977_muteh]]'),
   ('type', 'طلای میزبان دگرگونی؛ مورد اختلاف: کشش و بالاآمدگی ائوسن[[moritz2006]] در برابر طلای کوهزایی[[chahbagh2014]][[aliyari2012]]'),
   ('belt', 'پهنهٔ سنندج–سیرجان[[moritz2006]]'),
   ('host', 'شیست و گنیس با آمفیبولیت و کوارتزیت، نفوذیافته با لوکوگرانیت[[unige_muteh]]'),
   ('age', 'آرگون–آرگون مسکوویت ۵۵٫۷ تا ۳۸٫۵ میلیون سال؛ طلا جوان‌ترین رویداد تاریخ‌گذاری‌شده است[[moritz2006]]'),
   ('op', 'مجتمع طلای موته، متعلق به ایمپاسکو[[imico_muteh]]؛ معادن روباز سنجده و چاه‌خاتون، سنجده احتمالاً تعطیل[[madco_muteh]]؛ تولید ۳۴۶ کیلوگرم طلا در ده ماه منتهی به ۳۰ دی ۱۳۹۷[[irandaily2019]]'),
  ],
  sections=[
   ('زمین‌شناسی و سن', '''<p>کانسارهای طلای موته در شیست و گنیس همراه با آمفیبولیت و کوارتزیت جای دارند که لوکوگرانیت در آن‌ها نفوذ کرده است[[unige_muteh]]. Moritz و همکاران (۲۰۰۶) با سن‌سنجی آرگون–آرگون مسکوویت (۵۵٫۷ تا ۳۸٫۵ میلیون سال) کانی‌سازی را به ائوسن نسبت دادند، طلا را جوان‌ترین رویداد تاریخ‌گذاری‌شده دانستند و آن را به کشش و بالاآمدگی پایانی مرتبط کردند. نتایج آن‌ها مدل‌های قدیمی‌تر پرکامبرین–پالئوزوئیک را رد کرد[[moritz2006]]. پژوهشگران دیگر این ناحیه را طلای کوهزایی می‌دانند[[chahbagh2014]][[aliyari2012]].</p>'''),
   ('دگرسانی و کانی‌سازی', '''<p>دگرسانی شامل کوارتز، مسکوویت، پیریت، دولومیت–آنکریت و آلبیت است و پیریت میزبان اصلی طلاست[[moritz2006]]. پیریت اولیهٔ سنجده تا حدود ۸۱۰ ppm طلا دارد (اطمینان کم تا متوسط)[[rimag_muteh]].</p>'''),
   ('ذخیره و تولید', '''<p>رقم ذخیرهٔ قابل اتکایی در منابع بررسی‌شده یافت نشد و تنها ارقام موجود از منابع فارسی بدون تاریخ‌اند:</p>{{res}}<p>مجتمع طلای موته در ده ماه منتهی به ۳۰ دی ۱۳۹۷ (۲۰ ژانویهٔ ۲۰۱۹)، ۳۴۶ کیلوگرم طلا تولید کرد[[irandaily2019]].</p>'''),
  ],
  expert=[
   ('پیامد سن ائوسن برای اکتشاف', '''<p>اگر کانی‌سازی، چنان‌که Moritz و همکاران نشان دادند، به کشش و بالاآمدگی ائوسن وابسته باشد، کنترل‌کنندهٔ اصلی آن پهنه‌های برشی و گسل‌های کششی همان دوره است، نه لایه‌بندی دگرگونی قدیمی‌تر. این دیدگاه هدف اکتشاف را به ساختارهای ائوسن در امتداد پهنهٔ سنندج–سیرجان معطوف می‌کند. برای تخمین، کنترل ساختاری قوی یعنی ناهمسانگردی شدید و پیوستگی کوتاه در جهت عمود بر رگه‌ها؛ با تولید سالانه‌ای در حد چند صد کیلوگرم، دقت مدل رگه و کنترل رقیق‌شدگی در اقتصاد معدن نقش تعیین‌کننده دارد.</p>'''),
  ]),
 en=dict(
  name='Muteh', province='Isfahan', type_short='Metamorphic-hosted gold',
  title='Muteh Gold Deposits, Isfahan: Geology and Age of Mineralisation | Ali Alinaghi',
  h1='Muteh gold deposits: geology and age',
  desc='The Muteh gold district in Isfahan Province: metamorphic-hosted gold in the Sanandaj–Sirjan Zone, the Eocene age of mineralisation, the orogenic interpretation, alteration and reported production.',
  lede='Muteh, in Isfahan Province, is a district of metamorphic-hosted gold deposits that the 1977 Minerals Yearbook described as a gold–pyrite–quartz vein deposit. Moritz et al. (2006) dated the mineralisation to the Eocene, yet even the exact location of its mines is inconsistent between databases.',
  coord_note='No coordinates are published for this deposit: the Mindat mine point[[mindat28816]], the Senjedeh pit point[[mindat28815]] and Muteh village[[wp_muteh]] are up to about 42 km apart. Coordinates will be added once checked against a geological map or a location map in a peer-reviewed paper.',
  facts=[
   ('aka', 'Mouteh, Mooteh; Persian: موته'),
   ('loc', 'Isfahan Province; county inconsistent between sources: Golpayegan (Mindat), “Borkhar-o-Meymeh”[[irandaily2019]] and Meymeh; not to be confused with Muteh village in Vazvan District[[wp_muteh]]'),
   ('comm', 'Gold; a “gold-pyrite-quartz vein deposit” in the 1977 Minerals Yearbook[[myb1977_muteh]]'),
   ('type', 'Metamorphic-hosted gold; disputed: Eocene extension and exhumation[[moritz2006]] vs orogenic gold[[chahbagh2014]][[aliyari2012]]'),
   ('belt', 'Sanandaj–Sirjan Zone[[moritz2006]]'),
   ('host', 'Schist and gneiss with amphibolite and quartzite, intruded by leucogranite[[unige_muteh]]'),
   ('age', 'Muscovite Ar–Ar 55.7–38.5 Ma, with gold the youngest dated event[[moritz2006]]'),
   ('op', 'IMPASCO’s Muteh Gold Complex[[imico_muteh]]; open pits at Senjedeh and Chah-Khatoon, Senjedeh possibly closed[[madco_muteh]]; 346 kg of gold in the ten months to 20 January 2019[[irandaily2019]]'),
  ],
  sections=[
   ('Geology and age', '''<p>The Muteh gold deposits sit in schist and gneiss with amphibolite and quartzite, intruded by leucogranite[[unige_muteh]]. Using muscovite Ar–Ar ages of 55.7–38.5 Ma, Moritz et al. (2006) dated the mineralisation to the Eocene, found gold to be the youngest dated event and tied it to late extension and exhumation; their results refute earlier Precambrian–Paleozoic models[[moritz2006]]. Other authors call the district orogenic[[chahbagh2014]][[aliyari2012]].</p>'''),
   ('Alteration and mineralisation', '''<p>Alteration comprises quartz, muscovite, pyrite, dolomite–ankerite and albite, and pyrite is the main gold host[[moritz2006]]. Early Senjedeh pyrite carries up to about 810 ppm Au (low–medium confidence)[[rimag_muteh]].</p>'''),
   ('Resources and production', '''<p>No reliable resource figure was found in the sources reviewed; the only figures come from undated Persian sources:</p>{{res}}<p>The Muteh Gold Complex produced 346 kg of gold in the ten months to 20 January 2019[[irandaily2019]].</p>'''),
  ],
  expert=[
   ('What an Eocene age means for exploration', '''<p>If mineralisation is tied to Eocene extension and exhumation, as Moritz et al. showed, its main controls are shear zones and extensional faults of that age, not the older metamorphic layering. That view points exploration towards Eocene structures along the Sanandaj–Sirjan Zone. For estimation, strong structural control means strong anisotropy and short continuity across the veins; with annual output of a few hundred kilograms, the accuracy of the vein model and dilution control decide the mine’s economics.</p>'''),
  ]),
)

DEPOSITS = [SARCHESHMEH, MIDUK, KAHANG, SUNGUN, MASJED_DAGHI, DALLI,
            GOL_E_GOHAR, CHADORMALU, CHOGHART, SANGAN,
            MEHDIABAD, ANGOURAN, IRANKUH,
            ZARSHURAN, AGH_DARREH, SARI_GUNAY, MUTEH]

# ---------- متن صفحهٔ اطلس (پیوندهای نسبی به صفحهٔ هر کانسار) ----------
HUB = {
 'fa': [
  ('مس پورفیری: سه ناحیه و چند پالس', '''<p>Aghazadeh و همکاران (۲۰۱۵) کانسارهای مس پورفیری ایران را در سه ناحیه گروه‌بندی کرده‌اند: ارسباران در شمال‌غرب، بخش میانی کمان ماگمایی ارومیه–دختر و کرمان در جنوب‌شرق. این کانسارها در چند پالس و هم‌زمان با بسته شدن اقیانوس نئوتتیس تشکیل شده‌اند: ارسباران یک پالس الیگوسن پسین (۲۹ تا ۲۷ میلیون سال) و یک پالس میوسن پیشین (۲۲ تا ۲۰ میلیون سال) دارد و کمان میانی یک پالس میوسن میانی (۱۷ تا ۱۵ میلیون سال)[[aghazadeh2015]]. مهم‌ترین دورهٔ کانی‌سازی در کمربند کرمان میوسن پیشین تا میانی است[[caltech_kerman]].</p>
<p>سن‌های موجود بیشتر با این چارچوب می‌خوانند: <a href="sungun/">سونگون</a> ۲۲٫۹ تا ۲۱٫۷ میلیون سال (Re–Os)، <a href="kahang/">کهنگ</a> حدود ۱۵ تا ۱۴٫۵ میلیون سال، و <a href="sarcheshmeh/">سرچشمه</a> و <a href="miduk/">میدوک</a> ۱۲ تا ۱۳٫۶ میلیون سال. اما <a href="masjed-daghi/">مسجد داغی</a> سن زیرکن ائوسن (۵۴٫۱ میلیون سال) دارد که با سن میوسن پیشنهادی دیگران در تعارض است، و حداقل سن حدود ۲۱ میلیون سال <a href="dalli/">دالی</a> از پالس کمان میانی قدیمی‌تر است.</p>'''),
  ('آهن: سه خانوادهٔ زمین‌شناسی', '''<p>چهار کانسار آهن این اطلس به سه خانوادهٔ زمین‌شناسی تعلق دارند. <a href="chadormalu/">چادرملو</a> و <a href="choghart/">چغارت</a> کانسارهای اکسید آهن–آپاتیت نوع کایرونا در ناحیهٔ بافق‌اند که در کمان آتشفشانی–نفوذی کامبرین پیشین کاشمر–کرمان تشکیل شده‌اند[[torab2007]][[heidarian2017]]. <a href="sangan/">سنگان</a> ناحیه‌ای از اسکارن‌های آهن ائوسن در کمربند خواف–کاشمر–بردسکن است[[golmohammadi2015]]. <a href="gol-e-gohar/">گل‌گهر</a> در پهنهٔ سنندج–سیرجان قرار دارد و منشأ آن، ماگمایی–گرمابی یا سازند آهن نواری دگرگون‌شده، بحث‌برانگیزترین مسئلهٔ ژنتیکی این اطلس است[[alibabaie2020]][[atapour]].</p>
<p>منابع مختلف هر یک از این کانسارها را «بزرگ‌ترین» خوانده‌اند؛ چنین صفت‌هایی بدون مبنای مقایسهٔ یکسان معنای روشنی ندارند و در این اطلس به کار نرفته‌اند.</p>'''),
  ('سرب و روی: سه کانسار، سه مدل حل‌نشده', '''<p>هیچ‌یک از سه کانسار سرب و روی این اطلس تیپ ژنتیکی قطعی یا سن رادیومتری کانی‌سازی ندارد[[maghfouri2019]][[gilg2006]][[ghazban1994]]. <a href="mehdiabad/">مهدی‌آباد</a> در کرتاسهٔ زیرین حوضهٔ یزد میان مدل SEDEX و جانشینی کربناتی یا تیپ ایرلندی محل بحث است؛ <a href="irankuh/">ایرانکوه</a> در آپتین جنوب اصفهان میان MVT، هم‌زاد رسوبی و ایرلندی؛ و <a href="angouran/">انگوران</a>، با میزبان مرمر نئوپروتروزوئیک–کامبرین و زمان میوسن، میان منشأ درون‌زاد، دودکش برشی نمکی و سوپرژن[[zhuang2025]]. به همین دلیل انگوران نباید با دو کانسار دیگر زیر برچسب «کربنات‌میزبان کرتاسه» گروه‌بندی شود.</p>'''),
  ('طلا: ناحیهٔ تکاب، ساری‌گونی و موته', '''<p><a href="zarshuran/">زرشوران</a> و <a href="agh-darreh/">آق‌دره</a>، با ۱۲٫۵ کیلومتر فاصله در شهرستان تکاب، روشن‌ترین جفت کانسار طلای کارلین‌گونهٔ ایران‌اند و همراه با کانسار روی انگوران ناحیهٔ معدنی تکاب را می‌سازند[[mehrabi1999]][[daliran2008]]. <a href="sari-gunay/">ساری‌گونی</a> کانسار طلای اپی‌ترمال در یک مجموعهٔ آتشفشانی میوسن (۱۱٫۷ تا ۱۰٫۷ میلیون سال) است[[richards2006]] و <a href="muteh/">موته</a> طلای میزبان سنگ‌های دگرگونی پهنهٔ سنندج–سیرجان با سن ائوسن (۵۵٫۷ تا ۳۸٫۵ میلیون سال)[[moritz2006]].</p>'''),
  ('این اطلس را چگونه بخوانیم', '''<ul>
<li><b>ارقام «همان‌گونه که منتشر شده‌اند»:</b> در منابع بررسی‌شده هیچ رقمی مبنای کدهای JORC یا NI 43-101 را ذکر نمی‌کند. بیشتر ارقام ایرانی بر پایهٔ رده‌های ملی «قطعی و احتمالی»‌اند که با رده‌های JORC هم‌ارز نیستند؛ مقالهٔ <a href="/articles/resources-vs-reserves/">تفاوت منابع و ذخایر</a> را ببینید.</li>
<li><b>فلز محتوا:</b> برای مقایسهٔ ارقام ناهم‌خوان، تناژ در عیار ضرب شده است. این محاسبهٔ نویسنده است و نشان می‌دهد کدام ارقام یک پیکرهٔ کانسنگ را با عیار حد یا محدودهٔ متفاوت توصیف می‌کنند.</li>
<li><b>سطح اطمینان:</b> «بالا» یعنی رقم در یک رکورد معتبر (پایگاه دادهٔ USGS، Mindat یا چکیدهٔ ناشر) آمده یا دو منبع مستقل آن را تأیید کرده‌اند؛ «متوسط» یعنی یک منبع معتبر یا نقل ثانویه؛ «کم» یعنی خبر، وب‌سایت شرکتی یا منبعی با انتساب نامشخص یا تعارض شناخته‌شده.</li>
<li><b>مختصات:</b> تقریبی‌اند و منبع هرکدام ذکر شده است. موقعیت مهدی‌آباد و موته، که در منابع هم‌خوان نیست، تا تأیید روی نقشه نمی‌آید.</li>
<li><b>به‌روزرسانی:</b> وضعیت بهره‌برداری بیشتر کانسارها برای ۱۴۰۳ تا ۱۴۰۵ تأیید نشده است. اگر خطایی می‌بینید یا دادهٔ تازه‌تری دارید، از <a href="/#contact">فرم تماس</a> یا دکمهٔ بازخورد هر صفحه خبر دهید.</li></ul>'''),
 ],
 'en': [
  ('Porphyry copper: three regions, several pulses', '''<p>Aghazadeh et al. (2015) group Iran’s porphyry copper deposits into three regions: Arasbaran in the northwest, the middle segment of the Urumieh–Dokhtar magmatic arc, and Kerman in the southeast. The deposits formed in pulses tied to the closure of the Neo-Tethys ocean: Arasbaran had a late-Oligocene pulse (29–27 Ma) and an early-Miocene pulse (22–20 Ma), and the middle arc a middle-Miocene pulse (17–15 Ma)[[aghazadeh2015]]. The Kerman belt’s most important period is Early–Middle Miocene[[caltech_kerman]].</p>
<p>Most of the ages in hand fit that framework: <a href="sungun/">Sungun</a> at 22.9–21.7 Ma (Re–Os), <a href="kahang/">Kahang</a> at about 15–14.5 Ma, and <a href="sarcheshmeh/">Sarcheshmeh</a> and <a href="miduk/">Miduk</a> at 12–13.6 Ma. But <a href="masjed-daghi/">Masjed Daghi</a> has an Eocene zircon age (54.1 Ma) that conflicts with the Miocene age others propose, and the minimum age of about 21 Ma for <a href="dalli/">Dalli</a> is older than the middle-arc pulse.</p>'''),
  ('Iron: three geological families', '''<p>The four iron deposits in this atlas fall into three geological families. <a href="chadormalu/">Chadormalu</a> and <a href="choghart/">Choghart</a> are Kiruna-type iron oxide–apatite deposits of the Bafq district, formed in the Early Cambrian Kashmar–Kerman volcano-plutonic arc[[torab2007]][[heidarian2017]]. <a href="sangan/">Sangan</a> is a district of Eocene iron skarns in the Khaf–Kashmar–Bardaskan belt[[golmohammadi2015]]. <a href="gol-e-gohar/">Gol-e-Gohar</a> lies in the Sanandaj–Sirjan Zone, and its origin — magmatic-hydrothermal or a metamorphosed banded iron formation — is the sharpest genetic dispute in the atlas[[alibabaie2020]][[atapour]].</p>
<p>Different sources call one or another of these deposits “the largest”; without a common basis of comparison such labels mean little, and this atlas does not use them.</p>'''),
  ('Lead–zinc: three deposits, three unresolved models', '''<p>None of the three lead–zinc deposits in this atlas has a settled genetic type or a radiometric ore age[[maghfouri2019]][[gilg2006]][[ghazban1994]]. <a href="mehdiabad/">Mehdiabad</a>, in the Lower Cretaceous of the Yazd Basin, is debated between SEDEX and carbonate-replacement or Irish-type models; <a href="irankuh/">Irankuh</a>, in the Aptian south of Isfahan, between MVT, syn-sedimentary and Irish-type; and <a href="angouran/">Angouran</a>, with a Neoproterozoic–Cambrian marble host and Miocene timing, between hypogene, salt-related breccia-pipe and supergene origins[[zhuang2025]]. Angouran should therefore not share a “Cretaceous carbonate-hosted” label with the other two.</p>'''),
  ('Gold: the Takab district, Sari Gunay and Muteh', '''<p><a href="zarshuran/">Zarshuran</a> and <a href="agh-darreh/">Agh-Darreh</a>, 12.5 km apart in Takab County, are Iran’s clearest pair of Carlin-style gold deposits, and with the Angouran zinc deposit they form the Takab mining district[[mehrabi1999]][[daliran2008]]. <a href="sari-gunay/">Sari Gunay</a> is an epithermal gold deposit in a Miocene volcanic complex (11.7–10.7 Ma)[[richards2006]], and <a href="muteh/">Muteh</a> is metamorphic-hosted gold of Eocene age (55.7–38.5 Ma) in the Sanandaj–Sirjan Zone[[moritz2006]].</p>'''),
  ('How to read this atlas', '''<ul>
<li><b>Figures “as published”:</b> none of the figures in the sources reviewed states a JORC or NI 43-101 basis. Most Iranian figures use the national “proven and probable” («قطعی و احتمالی») categories, which are not equivalent to JORC classes; see <a href="/en/articles/resources-vs-reserves/">resources vs reserves</a>.</li>
<li><b>Contained metal:</b> to compare conflicting figures, tonnage is multiplied by grade. This is the author’s arithmetic, and it shows which figures describe the same orebody at a different cut-off grade or scope.</li>
<li><b>Confidence:</b> “high” means the figure appears in an authoritative record (a USGS database entry, Mindat or a publisher abstract) or two independent sources agree; “medium” means one reliable source or a secondary citation; “low” means news, a company website, an unclear attribution or a known conflict.</li>
<li><b>Coordinates:</b> approximate, each with its source. Mehdiabad and Muteh, whose locations are inconsistent between sources, are not mapped until verified.</li>
<li><b>Updates:</b> 2024–26 operating status could not be confirmed for most deposits. If you spot an error or hold newer data, please say so through the <a href="/en/#contact">contact form</a> or the feedback button on each page.</li></ul>'''),
 ],
}
