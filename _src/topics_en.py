# English topic pages. Same slugs and structure as topics_fa.py
TOPICS = [
{
 'slug':'resource-estimation','icon':'cube','short':'Resource estimation',
 'title':'Mineral Resource Estimation Consultant | Ali Alinaghi',
 'desc':'Mineral resource estimation for gold, copper, molybdenum, iron and lead–zinc using geostatistics, kriging and simulation; block modelling, validation and classification aligned with JORC and NI 43-101.',
 'h1':'Mineral resource estimation',
 'lede':'A resource estimate is the bridge between drillhole data and an investment decision. The number at the end of the report has to be traceable, repeatable and defensible in front of an independent auditor.',
 'sections':[
  ('How an estimate is built','''<p>A resource estimation project starts with data validation and ends with a classified, reported resource. The main stages:</p>
<ul>
<li><b>Database validation</b> — collar, survey, lithology and assay checks; review of standards, blanks and duplicates.</li>
<li><b>Domaining</b> — separating mineralised zones by lithology, alteration, oxidation and structural controls.</li>
<li><b>Compositing and top-cutting</b> — equal-length composites and control of extreme values, critical in gold deposits.</li>
<li><b>Variography</b> — directional analysis of grade continuity and variogram model fitting.</li>
<li><b>Block model estimation</b> — ordinary kriging, indicator kriging or sequential Gaussian simulation depending on deposit style and study purpose.</li>
<li><b>Validation</b> — global statistics, swath plots and visual section review.</li>
<li><b>Classification and reporting</b> — Measured, Indicated and Inferred resources with grade–tonnage curves.</li>
</ul>'''),
  ('Choosing the method','''<p>No single method suits every deposit. In porphyry copper–molybdenum systems with good grade continuity, ordinary kriging usually gives stable results. In high-nugget vein gold, indicator kriging or simulation gives a more honest picture of uncertainty. Block size, search neighbourhood and kriging neighbourhood analysis (KNA) are tested before the final run.</p>'''),
  ('Reporting standards','''<p>Reports follow accepted international guidelines such as JORC, NI 43-101 and CIM so they can be understood and audited by clients, lenders and foreign investors. Transparent assumptions, parameters and data limitations are part of every report.</p>'''),
  ('Software','''<p>Isatis.neo for geostatistics and simulation, Leapfrog Geo for implicit modelling, Surpac, Datamine and Vulcan for block modelling, and Python for custom analysis and automated QA/QC.</p>'''),
 ],
 'faq':[
  ('How long does a resource estimate take?','From a few weeks for a simple deposit to several months for a complex, multi-domain, multi-element deposit, depending on data volume and geology.'),
  ('Can a resource be estimated with limited data?','Yes, but at a lower classification. In that case an infill drilling programme is usually recommended to upgrade confidence.'),
 ],
 'related':['3d-geological-modelling','commodities','project-management'],
},
{
 'slug':'3d-geological-modelling','icon':'layers','short':'3D modelling',
 'title':'3D Geological Modelling and Block Models | Ali Alinaghi',
 'desc':'3D geological modelling of mineral deposits in Leapfrog, Surpac and Datamine: lithology, alteration, structure and mineralised domains, block model and density model construction.',
 'h1':'3D geological modelling',
 'lede':'The 3D model is the backbone of a resource estimate. If the mineralised boundary is wrong, even the best geostatistics will not produce the right number.',
 'sections':[
  ('What gets modelled','''<ul>
<li><b>Lithology</b> — host and non-host rock units.</li>
<li><b>Alteration</b> — potassic, phyllic, argillic and propylitic zones in porphyry and epithermal systems.</li>
<li><b>Structure</b> — faults and veins that control or offset mineralisation.</li>
<li><b>Weathering surfaces</b> — oxide, transition and sulphide boundaries that drive processing and recovery.</li>
<li><b>Grade shells</b> — mineralised envelopes based on cut-off grade and geological continuity.</li>
</ul>'''),
  ('Implicit and explicit modelling','''<p>Implicit modelling builds surfaces by interpolation from drillhole data and updates quickly as new holes arrive. Explicit modelling interprets and links sections by hand and gives the geologist tighter control over shape. In practice the best result combines both: implicit models for speed and scenario testing, manual review on key sections.</p>'''),
  ('From geological model to block model','''<p>The geological model becomes a block model in which every block carries a domain code, density, estimated grade and classification. Block size follows drill spacing, mining method and selective mining unit. This model feeds mine design, production scheduling and economic evaluation directly.</p>'''),
 ],
 'faq':[
  ('What data does 3D modelling need?','Drillhole data (collar, survey, lithology, assays), surface geological mapping, topography and, where available, geophysical sections.'),
 ],
 'related':['resource-estimation','mineral-exploration','exploration-geophysics'],
},
{
 'slug':'mineral-exploration','icon':'target','short':'Exploration',
 'title':'Mineral Exploration and Target Generation | Ali Alinaghi',
 'desc':'Mineral exploration programme design from reconnaissance and prospecting to general and detailed exploration; target generation integrating geology, geochemistry, geophysics and remote sensing.',
 'h1':'Mineral exploration and target generation',
 'lede':'The purpose of exploration is to reduce uncertainty at the lowest cost: every stage should answer clearly whether the licence deserves the next stage of investment.',
 'sections':[
  ('Exploration stages','''<ul>
<li><b>Reconnaissance</b> — maps, historical reports, satellite imagery and first field visits.</li>
<li><b>Prospecting</b> — geochemical sampling, geological mapping and anomaly definition.</li>
<li><b>General exploration</b> — trenching, ground geophysics and first drillholes to confirm mineralisation.</li>
<li><b>Detailed exploration</b> — systematic drilling for resource estimation and techno-economic studies.</li>
</ul>'''),
  ('Integrated targeting','''<p>No single dataset finds a deposit. Effective targeting combines <a href="/en/services/exploration-geochemistry/">geochemical anomalies</a>, <a href="/en/services/exploration-geophysics/">geophysical responses</a>, <a href="/en/services/remote-sensing/">remote sensing alteration maps</a> and a deposit model. The output is a ranked list of drill targets, each with a clear technical rationale.</p>'''),
  ('Deposit types and Iranian belts','''<p>Deposit type sets the exploration path. Porphyry copper in the Urumieh–Dokhtar and Kerman belts, iron in the Bafq district and Sanandaj–Sirjan zone, lead–zinc in the Malayer–Isfahan belt, and vein and orogenic gold in shear zones each have their own vectors and strategy.</p>'''),
 ],
 'faq':[
  ('How is an exploration programme budgeted?','In stages with decision points: each stage proceeds only if results from the previous one meet criteria agreed in advance.'),
 ],
 'related':['exploration-geochemistry','exploration-geophysics','remote-sensing'],
},
{
 'slug':'exploration-geophysics','icon':'wave','short':'Geophysics',
 'title':'Exploration Geophysics: Magnetics, IP and Resistivity | Ali Alinaghi',
 'desc':'Interpretation of exploration geophysics including magnetics, induced polarisation (IP), resistivity and gravity, integrated with geology and geochemistry for drillhole design.',
 'h1':'Exploration geophysics',
 'lede':'Geophysics sees below the surface, but without geology its interpretation is ambiguous. Its real value appears when it sits in a single model alongside the other data.',
 'sections':[
  ('Common methods','''<ul>
<li><b>Magnetics</b> — tracing magnetite iron deposits, intrusions and structures; the backbone of iron exploration.</li>
<li><b>Induced polarisation (IP) and resistivity</b> — mapping disseminated sulphides in porphyry copper and polymetallic systems.</li>
<li><b>Gravity</b> — detecting dense bodies and deep structures.</li>
<li><b>Gamma-ray spectrometry</b> — mapping potassic alteration and separating rock units.</li>
</ul>'''),
  ('From anomaly to drillhole','''<p>An IP anomaly can come from barren pyrite, graphite or copper sulphide. That is why anomalies are compared with alteration maps, geochemistry and the geological model, and only targets with several independent lines of evidence reach the drill. Inverted sections are placed in the 3D model next to drillhole data to optimise collar position and depth.</p>'''),
 ],
 'faq':[
  ('Which geophysical method suits porphyry copper?','IP/resistivity for the sulphide zone combined with magnetics to map the intrusion and magnetite destruction in the phyllic zone.'),
 ],
 'related':['mineral-exploration','exploration-geochemistry','3d-geological-modelling'],
},
{
 'slug':'exploration-geochemistry','icon':'flask','short':'Geochemistry',
 'title':'Exploration Geochemistry and Anomaly Separation | Ali Alinaghi',
 'desc':'Exploration geochemistry: stream sediment, soil and rock sampling; anomaly separation with robust statistics and fractal methods, multivariate analysis and pathfinder elements for gold, copper and lead–zinc.',
 'h1':'Exploration geochemistry',
 'lede':'Geochemistry is the cheapest way to shrink a large licence to a few promising targets — provided the sampling design and data processing are done properly.',
 'sections':[
  ('Sampling','''<p>The sampling medium depends on the exploration stage: <b>stream sediments</b> for regional coverage, <b>soils</b> to locate anomalies more precisely, and <b>rock and lithogeochemistry</b> to understand alteration halos and deposit zoning. QA/QC with duplicates, blanks and standards is built into the design from the start.</p>'''),
  ('Processing and anomaly separation','''<ul>
<li>Compositional data transforms (such as the centred log-ratio) before multivariate analysis.</li>
<li>Background and anomaly separation with robust statistics and concentration–area fractal methods.</li>
<li>Principal component and factor analysis to identify element associations.</li>
<li>Anomaly maps and target ranking in GIS.</li>
</ul>'''),
  ('Pathfinder elements','''<p>Arsenic, antimony and mercury for gold; molybdenum, copper and outer zinc–lead halos for porphyry copper; barium and manganese for lead–zinc deposits. Element zoning helps estimate erosion level and locate the core of the system.</p>'''),
 ],
 'faq':[
  ('Why transform geochemical data?','Element concentrations are compositional and create spurious correlations; log-ratio transforms remove that effect and make multivariate results reliable.'),
 ],
 'related':['mineral-exploration','remote-sensing','exploration-geophysics'],
},
{
 'slug':'remote-sensing','icon':'satellite','short':'Remote sensing',
 'title':'Remote Sensing for Mineral Exploration | Ali Alinaghi',
 'desc':'Remote sensing for mineral exploration with ASTER, Sentinel-2 and Landsat imagery: alteration mapping, iron oxides and lineament analysis for target generation.',
 'h1':'Remote sensing for mineral exploration',
 'lede':'Satellite imagery gives a picture of alteration and structure across a wide area before the first field visit, and turns field traverses into targeted work.',
 'sections':[
  ('Data','''<ul>
<li><b>ASTER</b> — short-wave and thermal infrared bands to separate clays, sericite, carbonate and silica.</li>
<li><b>Sentinel-2</b> — good spatial resolution for iron oxides, free and frequently updated.</li>
<li><b>Landsat 8 and 9</b> — long archive, well suited to regional mapping.</li>
<li><b>Digital elevation models</b> — lineament and structural analysis.</li>
</ul>'''),
  ('Methods','''<p>Band ratios, selective principal component analysis, spectral methods such as SAM and supervised classification are used to map argillic, phyllic and propylitic alteration and gossans. Results are always checked in the field and by sampling.</p>'''),
  ('Role in targeting','''<p>Remote sensing output is one layer in the targeting model, not the final answer. Combined with <a href="/en/services/exploration-geochemistry/">geochemistry</a> and <a href="/en/services/exploration-geophysics/">geophysics</a> it produces targets with a much higher chance of drilling success.</p>'''),
 ],
 'faq':[
  ('Does remote sensing replace fieldwork?','No. It makes field visits targeted and cheaper, but alteration and mineralisation can only be confirmed by field observation and assays.'),
 ],
 'related':['mineral-exploration','exploration-geochemistry','exploration-geophysics'],
},
{
 'slug':'project-management','icon':'plan','short':'Project management',
 'title':'Exploration and Mining Project Management | Ali Alinaghi',
 'desc':'Management of mineral exploration projects: staged planning, budgets and schedules, drilling and sampling supervision, data QA/QC and reporting to clients and investors.',
 'h1':'Exploration project management',
 'lede':'Most exploration spend goes into drilling. Good management means every metre answers a specific question and produces data fit for resource estimation.',
 'sections':[
  ('Scope','''<ul>
<li><b>Staged planning</b> — objectives, go/no-go criteria and decision points.</li>
<li><b>Budget and schedule</b> — drilling, assay and staffing costs, with variance tracking.</li>
<li><b>Drilling management</b> — hole design, contractor supervision, core recovery and logging.</li>
<li><b>QA/QC</b> — standards, blanks and duplicates protocol with continuous laboratory monitoring.</li>
<li><b>Data management</b> — a single, auditable database from day one.</li>
<li><b>Reporting</b> — periodic reports for the client and stage reports for investors.</li>
</ul>'''),
  ('International experience','''<p>Work on projects in Armenia, Venezuela and Morocco alongside domestic projects in Iran has built experience coordinating multinational teams and meeting different reporting requirements.</p>'''),
 ],
 'faq':[
  ('What does project management deliver?','An exploration plan and budget, progress reports, a validated database and an end-of-stage report with a recommended next step.'),
 ],
 'related':['mineral-exploration','resource-estimation','commodities'],
},
{
 'slug':'commodities','icon':'gem','short':'Commodities',
 'title':'Gold, Copper, Molybdenum, Iron, Lead–Zinc and Talc Exploration | Ali Alinaghi',
 'desc':'Experience in exploration and resource estimation of gold, copper, molybdenum, iron, lead–zinc, talc and coal: deposit characteristics and the technical challenges of estimating each.',
 'h1':'Commodities',
 'lede':'Every commodity has its own technical challenges. A method that works for an iron deposit can be misleading for vein-hosted gold.',
 'sections':[
  ('Gold','''<p id="gold">Vein, epithermal and orogenic gold deposits usually have a high nugget effect and strongly skewed grades. Top-cutting, indicator kriging or simulation, and careful sampling and preparation are the keys to a reliable gold estimate. Experience: a gold project in Venezuela and vein-hosted gold–copper deposits in Isfahan province, Iran.</p>'''),
  ('Copper and molybdenum','''<p id="copper">Porphyry copper deposits are large-tonnage and low-grade, usually with good grade continuity. Molybdenum is estimated as a by-product and behaves differently in space, so it needs its own variography and domains. Separating oxide, supergene and hypogene zones drives recovery. Experience: a copper–molybdenum project in Armenia and copper projects in Yazd province, Iran.</p>'''),
  ('Iron','''<p id="iron">In magnetite and hematite deposits the density model matters as much as the grade model. Relationships between total iron, density and magnetic iron, and Davis tube results, are used to estimate saleable product. Experience: iron projects in Armenia and South Khorasan, Iran.</p>'''),
  ('Lead and zinc','''<p id="lead-zinc">Carbonate-hosted lead–zinc deposits are irregular, with strong structural and stratigraphic control. Separating sulphide from non-sulphide ore and the Pb:Zn ratio are decisive for process design. Experience: a lead, zinc and gold polymetallic project in Ardabil province, Iran.</p>'''),
  ('Talc','''<p id="talc">Talc value depends more on quality — brightness and impurities — than on grade. Talc exploration focuses on detailed mapping of host units and sampling for quality testing. Experience: a talc and iron project in Morocco.</p>'''),
  ('Coal','''<p id="coal">For coal, seam modelling, thickness and quality (ash, volatile matter and calorific value) are the basis of the resource estimate.</p>'''),
 ],
 'faq':[],
 'related':['resource-estimation','mineral-exploration','3d-geological-modelling'],
},
]
