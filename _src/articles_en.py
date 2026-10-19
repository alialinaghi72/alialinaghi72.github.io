# English articles. Same slugs and structure as articles_fa.py; {{fig:name}} is replaced by charts.py figures.
from articles_fa import REF, P

ARTICLES = [
{
 'slug': 'kriging', 'short': 'Kriging', 'cat': 'Geostatistics', 'icon': 'cube', 'published': P, 'updated': P,
 'title': 'What Is Kriging? A Practical Guide for Mineral Resource Estimation | Ali Alinaghi',
 'desc': 'Ordinary, simple and indicator kriging explained: the kriging system, weights and screening, kriging variance, kriging neighbourhood analysis (KNA), smoothing and common mistakes in resource estimation.',
 'h1': 'What is kriging? A practical guide for resource estimation',
 'lede': 'Kriging is the most widely used method for estimating grades in block models. This guide explains what kriging actually does, where its weights come from, and what makes a kriged estimate defensible — or misleading.',
 'card': 'Principles and equations, types of kriging, neighbourhood analysis and common mistakes.',
 'keywords': ['kriging', 'ordinary kriging', 'indicator kriging', 'resource estimation', 'geostatistics', 'kriging variance', 'kriging neighbourhood analysis'],
 'takeaways': [
  'Kriging is a weighted average of samples, but the weights come from the variogram model, not from distance alone.',
  'Unbiasedness plus minimum error variance gives the kriging system, which returns a kriging variance alongside the grade.',
  'Kriging automatically declusters grouped samples and screens samples that sit behind closer ones.',
  'Kriged estimates are smoother than reality; recoverable resources at the selective mining unit scale need change-of-support methods or simulation.',
  'Estimate quality depends on domaining, top-cutting, the variogram model and the search neighbourhood, and must be validated with swath plots and global statistics.'],
 'sections': [
  ('Kriging in plain language', '''<p>Suppose we want to estimate the copper grade of a 25 × 25 × 10 m block with a few drillholes around it. The simplest approach is to average the nearby samples. Inverse distance weighting goes one step further and gives closer samples more weight. <b>Kriging</b> completes the idea with two important differences: the weights come from a <a href="/en/articles/variogram/">variogram model</a> that describes the actual grade continuity of that deposit, and the geometry of the samples relative to each other is taken into account.</p>
<p>That is why kriging is called the Best Linear Unbiased Estimator (BLUE): linear because the estimate is a linear combination of samples, unbiased because on average it has no systematic error, and best because it minimises the estimation error variance. Georges Matheron formalised the method in the 1960s, building on Danie Krige's work in the Witwatersrand gold mines, and named it after Krige.</p>'''),
  ('The ordinary kriging equations', '''<p>In ordinary kriging, the grade of a point or block is estimated as:</p>
<p class="eq" dir="ltr">Z*(x₀) = Σ λᵢ · Z(xᵢ)&nbsp;&nbsp;&nbsp;,&nbsp;&nbsp;&nbsp;Σ λᵢ = 1</p>
<p>The constraint that the weights sum to one guarantees unbiasedness without knowing the deposit mean, which makes ordinary kriging suitable where the local mean changes from place to place. Minimising the error variance under this constraint, with a Lagrange multiplier μ, gives the kriging system:</p>
<p class="eq" dir="ltr">Σⱼ λⱼ γ(xᵢ, xⱼ) + μ = γ(xᵢ, x₀)&nbsp;&nbsp;&nbsp;&nbsp;i = 1 … n</p>
<p>Here <span class="math" dir="ltr">γ(xᵢ, xⱼ)</span> is the variogram between two samples and <span class="math" dir="ltr">γ(xᵢ, x₀)</span> the variogram between each sample and the estimation point. The left-hand side measures how redundant the samples are with each other; the right-hand side measures how statistically close each sample is to the target. Solving the system gives the weights and the <b>kriging variance</b>:</p>
<p class="eq" dir="ltr">σ²ₖ = Σ λᵢ γ(xᵢ, x₀) + μ</p>
<p>In block kriging, γ(xᵢ, x₀) is replaced by the average variogram between the sample and the whole block, and the average variogram within the block is subtracted from the variance. The kriging variance depends only on the sample geometry and the variogram model, not on the grade values, so it measures geometric confidence rather than a true confidence interval on grade.</p>'''),
  ('Weights in practice: declustering and screening', '''<p>The figure below shows ordinary kriging weights for seven samples around a point. The weights were actually computed with this variogram model, and they show two key behaviours of kriging:</p>
{{fig:kriging}}
<ul><li><b>Declustering:</b> the three closely spaced samples to the west carry largely redundant information, so kriging gives them together about the same weight as the single sample to the east at the same distance, whereas inverse distance gives the cluster nearly three times as much and lets it dominate.</li>
<li><b>Screening:</b> the sample sitting directly behind the closer northern one adds little new information and receives a very small or, as here, negative weight.</li></ul>
<p>Small negative weights are normal; large negative weights point to a poor search neighbourhood or an overly continuous variogram and can produce unrealistic, even negative, grades.</p>'''),
  ('Types of kriging and when to use them', '''<ul>
<li><b>Simple kriging (SK):</b> assumes a known global mean. Rarely used for direct estimation, but it is the engine of sequential Gaussian simulation (SGS).</li>
<li><b>Ordinary kriging (OK):</b> assumes an unknown mean that is constant within the neighbourhood; the standard method for most resource estimates.</li>
<li><b>Indicator kriging (IK):</b> transforms the data into 0/1 indicators at several grade thresholds and estimates the probability of exceeding each one; suited to highly skewed, high-nugget distributions such as vein gold.</li>
<li><b>Cokriging:</b> uses a correlated secondary variable — copper to help estimate molybdenum, or a geophysical attribute — to improve the primary estimate.</li>
<li><b>Kriging with a trend (UK, KED):</b> for a mean with a systematic spatial trend, such as grade decreasing away from the core of a deposit.</li>
<li><b>Lognormal kriging:</b> works on log-transformed data; the back-transform is sensitive to distributional assumptions and should be used with care.</li>
</ul>'''),
  ('Search neighbourhood and kriging neighbourhood analysis (KNA)', '''<p>Choosing which samples take part in each block estimate matters as much as the variogram itself. The search ellipse is usually aligned with the variogram anisotropy, and parameters such as minimum and maximum samples, maximum samples per drillhole and octant search are set.</p>
<p>In <b>kriging neighbourhood analysis</b> these parameters are varied for a set of test blocks while monitoring metrics such as the <b>slope of regression</b> (true grade on estimated grade) and <b>kriging efficiency</b>. A slope close to one means little conditional bias. Many practitioners look for values around 0.9 or higher in high-confidence blocks, but this is not a rule of the reporting codes and depends on the deposit and the purpose of the estimate.</p>
<p>Kriging efficiency is <span class="math" dir="ltr">KE = (BV − KV) / BV</span>, where BV is the block variance and KV the kriging variance. A negative value means the estimate is no better than simply using the global mean.</p>'''),
  ('Smoothing and the grade–tonnage curve', '''<p>Because kriging minimises error variance, its estimates are smoother than reality: high grades are underestimated and low grades overestimated. When drill spacing is large relative to the block size, smoothing is severe, and a grade–tonnage curve read directly from the kriged model misstates the tonnage and grade above cut-off.</p>
<p>Common remedies are estimating into blocks sized to the drill spacing rather than smaller, change-of-support methods such as uniform conditioning (UC) and localised uniform conditioning (LUC), and conditional simulation to assess uncertainty. For the economic side of this, see the <a href="/en/articles/cut-off-grade/">cut-off grade</a> article.</p>'''),
  ('Kriging or inverse distance?', '''<p>Inverse distance weighting (IDW) is simple and fast and needs no variogram, but it does not decluster and its distance power is an arbitrary choice. When there is enough data for a reliable variogram, ordinary kriging is the standard choice. In practice IDW and nearest-neighbour (NN) estimates are run alongside kriging so that validation can expose any bias.</p>'''),
  ('Common kriging mistakes', '''<ul>
<li>Estimating without domains, letting samples cross the boundaries of different mineralised zones (hard versus soft boundaries).</li>
<li>Not top-cutting extreme grades in skewed deposits.</li>
<li>A variogram with too low a nugget, which gives the estimate false confidence.</li>
<li>Ignoring anisotropy, or a search ellipse that is not aligned with the geology.</li>
<li>A neighbourhood that is too large and over-smooths, or too small and creates conditional bias.</li>
<li>Too many samples from a single drillhole, concentrating weight in one direction.</li>
<li>No validation: compare the global mean with declustered nearest-neighbour, check swath plots and review sections visually.</li>
</ul>'''),
 ],
 'faq': [
  ('Which software is used for kriging?', 'Specialist packages such as Isatis.neo, Leapfrog Edge, Datamine, Surpac and Vulcan run kriging, and libraries such as GSLIB or Python\'s gstools are used for custom analysis.'),
  ('Is kriging variance the same as grade uncertainty?', 'Not entirely. Kriging variance depends only on sample geometry and the variogram model and is insensitive to local grade values. Conditional simulation is the better tool for assessing real uncertainty.'),
  ('How many drillholes are needed for kriging?', 'There is no fixed number; what matters is having enough sample pairs to build a reliable variogram in each domain. With little data, inverse distance with conservative classification is usually the more sensible choice.'),
 ],
 'refs': [REF['krige'], REF['matheron'], REF['jh'], REF['is'], REF['vann'], REF['rd']],
 'related': {'art': ['variogram', 'cut-off-grade', 'resources-vs-reserves'], 'tools': ['variogram-lab'], 'svc': ['resource-estimation', '3d-geological-modelling']},
},
{
 'slug': 'variogram', 'short': 'Variogram', 'cat': 'Geostatistics', 'icon': 'chart', 'published': P, 'updated': P,
 'title': 'The Variogram Explained: Calculation, Modelling and Interpretation | Ali Alinaghi',
 'desc': 'The variogram explained: definition and formula, nugget, sill and range, experimental variogram calculation, spherical, exponential and Gaussian models, anisotropy, and use in drill spacing and resource estimation.',
 'h1': 'The variogram explained: calculation, modelling and interpretation',
 'lede': 'The variogram is the core geostatistical tool for describing the spatial continuity of grade. Almost every decision in a resource estimate — from kriging weights to drill spacing and classification — depends on it.',
 'card': 'Definition, components, spherical and exponential models, anisotropy and practical interpretation.',
 'keywords': ['variogram', 'variography', 'nugget effect', 'sill', 'range', 'anisotropy', 'geostatistics'],
 'takeaways': [
  'The variogram is half the average squared difference between samples separated by a distance h.',
  'The nugget is the variability at near-zero distance, including sampling and assay error; the sill is the total variance and the range is the distance at which correlation disappears.',
  'Experimental variograms must be calculated separately for each geological domain, with enough pairs in every lag.',
  'The spherical model is the most common for grades; the Gaussian model is rarely appropriate for grade.',
  'The nugget-to-sill ratio and the directional ranges steer the estimation method, block size and drill spacing.'],
 'sections': [
  ('What does a variogram measure?', '''<p>Two samples a short distance apart usually have more similar grades than two samples hundreds of metres apart. The variogram quantifies this "dissimilarity as a function of distance":</p>
<p class="eq" dir="ltr">γ(h) = 1 / (2N(h)) · Σ [ z(xᵢ) − z(xᵢ + h) ]²</p>
<p>N(h) is the number of sample pairs separated by the vector h. Because h has both length and direction, variograms can be calculated in different directions to show how continuity differs along strike, down dip and across the thickness of a mineralised zone. Strictly this is the semivariogram, but in practice it is simply called the variogram.</p>'''),
  ('Nugget, sill and range', '''{{fig:variogram}}
<ul>
<li><b>Nugget (C₀):</b> the variogram value at a distance close to zero; a combination of variability at scales smaller than the sample spacing and the errors of sampling, preparation and assay. The name comes from the behaviour of free gold nuggets.</li>
<li><b>Sill (C₀ + C₁):</b> the level at which the variogram flattens; for stationary data it is close to the data variance.</li>
<li><b>Range (a):</b> the distance beyond which samples are no longer meaningfully correlated. Samples within the range of the estimation point receive meaningful kriging weight.</li>
</ul>
<p>The nugget-to-sill ratio is one of the most important indicators. In the widely used classification of Cambardella et al. (1994), a ratio below 25% indicates strong spatial dependence and above 75% weak dependence; these limits are approximate guides, not hard rules.</p>'''),
  ('Calculating the experimental variogram', '''<p>Because samples are not exactly equally spaced, pairs are grouped into distance "lags". The main parameters are:</p>
<ul>
<li><b>Lag length:</b> usually close to the average sample or drillhole spacing in that direction.</li>
<li><b>Lag tolerance:</b> often half the lag, so each pair falls into one lag only.</li>
<li><b>Angular tolerance and bandwidth:</b> how far pairs may deviate from the target direction and still be accepted.</li>
<li><b>Number of pairs:</b> lags with few pairs — as a rule of thumb fewer than 30 — scatter widely and should not drive the model.</li>
</ul>
<p>A <b>downhole</b> variogram with a lag equal to the composite length gives the best estimate of the nugget, and a variogram map helps find the directions of maximum and minimum continuity. Always calculate on <b>equal-length composites</b> and separately for each geological domain.</p>'''),
  ('Variogram models', '''<p>The experimental variogram is fitted with an admissible mathematical function so it can be used in kriging. The three basic models:</p>
<p class="eq" dir="ltr">Spherical: γ(h) = C₀ + C₁ [1.5 (h/a) − 0.5 (h/a)³] for h ≤ a ; C₀ + C₁ for h &gt; a</p>
<p class="eq" dir="ltr">Exponential: γ(h) = C₀ + C₁ [1 − exp(−3h/a)]</p>
<p class="eq" dir="ltr">Gaussian: γ(h) = C₀ + C₁ [1 − exp(−3h²/a²)]</p>
<ul>
<li><b>Spherical:</b> the most common model for grade; nearly linear near the origin, reaching the sill at the range.</li>
<li><b>Exponential:</b> approaches the sill gradually; in these formulas a is the practical range, where about 95% of the sill is reached.</li>
<li><b>Gaussian:</b> very smooth near the origin, better suited to highly continuous variables such as thickness or topographic surfaces than to grade.</li>
</ul>
<p>Most deposits are fitted better by two or three nested structures — for example a short-range and a long-range structure. To see how each parameter changes the curve, try the <a href="/en/tools/variogram-lab/">interactive variogram lab</a>.</p>'''),
  ('Anisotropy', '''<p>Grade continuity is rarely the same in every direction; in a vein, continuity along strike and down dip is far greater than across it. In <b>geometric anisotropy</b> the sill is the same in all directions and only the range changes, described by a three-axis ellipsoid. In <b>zonal anisotropy</b> the sill itself changes with direction, which often signals layering or insufficient domaining. The principal directions should agree with the geology: the strike and dip of the zone and the controlling structures.</p>'''),
  ('Interpreting variograms in practice', '''<ul>
<li><b>High nugget:</b> common in vein gold; local prediction is difficult, so consider top-cutting, indicator kriging or simulation, and improving the sampling protocol.</li>
<li><b>Short range relative to drill spacing:</b> if holes are further apart than the range, block estimates collapse towards the local mean and classification must be conservative.</li>
<li><b>Proportional effect:</b> in lognormal data the local variance rises with the local mean; pairwise relative or normal-score variograms show the structure more clearly.</li>
<li><b>Continuous rise with no sill:</b> a sign of drift or mixed populations, usually solved by better domaining.</li>
<li><b>Hole effect:</b> a regular oscillation that may reflect repeating structures such as parallel veins.</li>
</ul>'''),
  ('Variograms and drill-hole spacing', '''<p>Variogram ranges are a good starting point for drill spacing: the smaller the spacing relative to the range, the more confident the estimate. Turning that principle into a fixed classification number is not sound, though. Better approaches are drill-spacing studies with kriging variance or conditional simulation, which show how accurately quarterly or annual production would be estimated at each spacing. For how this confidence maps onto resource categories, see <a href="/en/articles/resources-vs-reserves/">resources versus reserves</a>.</p>'''),
 ],
 'faq': [
  ('What is the difference between the variogram and the covariance?', 'For stationary data they are linked by γ(h) = C(0) − C(h): the variogram measures dissimilarity and the covariance similarity as a function of distance. The variogram needs a weaker assumption and is more common in mining.'),
  ('How many samples make a reliable variogram?', 'There is no fixed number; what matters is the number of pairs per lag and coverage of the main directions. In data-poor domains, use a downhole variogram for the nugget and conservative geological assumptions for the range.'),
 ],
 'refs': [REF['matheron'], REF['jh'], REF['is'], REF['goov'], REF['camb']],
 'related': {'art': ['kriging', 'resources-vs-reserves', 'qaqc'], 'tools': ['variogram-lab'], 'svc': ['resource-estimation']},
},
{
 'slug': 'cut-off-grade', 'short': 'Cut-off grade', 'cat': 'Economic evaluation', 'icon': 'calc', 'published': P, 'updated': P,
 'title': 'Cut-off Grade: What It Is and How to Calculate It (with Calculator) | Ali Alinaghi',
 'desc': 'Cut-off grade explained: break-even and marginal cut-off formulas, worked copper and gold examples, grade–tonnage curves, Lane\'s theory, cut-off in JORC resource reporting, and a free online calculator.',
 'h1': 'Cut-off grade: what it is and how to calculate it',
 'lede': 'The cut-off grade is the boundary between ore and waste — the number that decides which part of a deposit is worth mining and processing. This guide works through the formulas with numbers and shows why cut-off grade is never a fixed value.',
 'card': 'Break-even and marginal cut-off formulas, copper and gold examples, grade–tonnage curves and common mistakes.',
 'keywords': ['cut-off grade', 'cut-off grade calculation', 'break-even cut-off', 'marginal cut-off', 'grade tonnage curve'],
 'takeaways': [
  'The break-even cut-off is the grade at which the net revenue from a tonne of ore exactly covers its costs.',
  'The marginal cut-off excludes mining cost and applies to material that has to be mined anyway.',
  'Price, metallurgical recovery, payability and selling costs affect cut-off as much as operating costs do.',
  'Raising the cut-off lowers tonnage and raises average grade; the grade–tonnage curve shows the trade-off.',
  'Under JORC, a resource cut-off must be consistent with reasonable prospects for eventual economic extraction, with its assumptions disclosed.'],
 'sections': [
  ('Cut-off grade in plain language', '''<p>Every block in a deposit model can go to the mill, a low-grade stockpile or the waste dump. The <b>cut-off grade</b> is the lowest grade at which sending a block to a given destination pays. It is therefore not a geological property but an economic decision that depends on metal price, costs, recovery and mine strategy, and it changes whenever any of them changes.</p>'''),
  ('The break-even cut-off formula', '''<p>In its simplest form, the break-even cut-off is the cost per tonne of ore divided by the net revenue per unit of grade:</p>
<p class="eq" dir="ltr">Cut-off = (Mining + Processing + G&amp;A, $/t ore) / [ (Price − Selling cost) × Recovery × Payable ]</p>
<p>Costs are in dollars per tonne of ore, price and selling costs (smelting, refining, freight) in dollars per unit of metal, and recovery and payability as fractions. For base metals with grade in percent, multiply the result by 100; for gold, convert the price from dollars per ounce to dollars per gram by dividing by 31.1035.</p>'''),
  ('Worked examples: copper and gold', '''<p><b>Copper (hypothetical inputs):</b> price $9,000/t Cu, selling cost $1,000/t Cu, recovery 88%, payable 96.5%, mining $2.5, processing $12 and G&amp;A $2 per tonne of ore.</p>
<p class="eq" dir="ltr">(9000 − 1000) × 0.88 × 0.965 = 6,793.6 $ per tonne Cu<br>Break-even = (2.5 + 12 + 2) / 6,793.6 × 100 ≈ 0.24 % Cu<br>Marginal (excluding mining) = (12 + 2) / 6,793.6 × 100 ≈ 0.21 % Cu</p>
<p><b>Gold (hypothetical inputs):</b> price $2,000/oz, refining $5/oz, recovery 90%, payable 99.5%, mining $3, processing $18 and G&amp;A $4 per tonne.</p>
<p class="eq" dir="ltr">(2000 − 5) / 31.1035 × 0.90 × 0.995 ≈ 57.4 $ per gram<br>Break-even = (3 + 18 + 4) / 57.4 ≈ 0.44 g/t Au<br>Marginal = (18 + 4) / 57.4 ≈ 0.38 g/t Au</p>
<p>Run the same calculation with your own project numbers in the <a href="/en/tools/cut-off-grade/">cut-off grade calculator</a>, which also shows how cut-off responds to price.</p>'''),
  ('Break-even, marginal and optimum cut-off', '''<ul>
<li><b>Break-even cut-off:</b> includes all costs, mining among them; it answers whether a block is worth mining at all.</li>
<li><b>Marginal (in-pit) cut-off:</b> for material that must be removed anyway to reach ore, mining is a sunk cost, so only processing and G&amp;A are compared with revenue.</li>
<li><b>Optimum cut-off (Lane's theory):</b> Kenneth Lane showed that when mining, processing or market capacity is constrained, the cut-off that maximises net present value (NPV) is usually above break-even and declines over the mine life, because the opportunity cost of processing low-grade ore is highest in the early years.</li>
</ul>'''),
  ('The grade–tonnage curve', '''<p>The grade–tonnage curve shows how the tonnage above cut-off, and the average grade of that tonnage, change as the cut-off changes:</p>
{{fig:grade_tonnage}}
<p>As cut-off rises, tonnage falls and average grade rises, but contained metal — the product of the two — usually falls. The shape of these curves depends on the grade distribution and on block support, which is why a curve read from a small-block kriged model can differ from actual production (see <a href="/en/articles/kriging/">kriging</a>).</p>'''),
  ('Cut-off grade in resource reporting', '''<p>Reporting codes such as JORC require Mineral Resources to have "reasonable prospects for eventual economic extraction". In practice that means reporting above a realistic cut-off, often within an optimised pit shell at conservative prices, and disclosing the price, cost and recovery assumptions.</p>
<p>Polymetallic deposits use metal equivalents (for example copper equivalent) or net smelter return (NSR). The formula, prices and recovery of each metal must then be disclosed, and equivalents should only include metals with realistic recovery and sale.</p>'''),
  ('Common cut-off grade mistakes', '''<ul>
<li>Using a high spot price instead of a conservative long-term price.</li>
<li>Ignoring smelting and refining charges, freight and payability.</li>
<li>Applying cut-off to in-situ grade without allowing for dilution and mining recovery.</li>
<li>One cut-off for every domain, even though oxide and sulphide ore differ in recovery or processing cost.</li>
<li>Unit errors — price per pound with cost per tonne, or troy ounces mixed up with grams.</li>
</ul>'''),
 ],
 'faq': [
  ('What is the difference between cut-off grade and average grade?', 'Cut-off grade is the threshold separating ore from waste; average grade is the mean grade of all material above the cut-off and is always higher than the cut-off.'),
  ('Does the cut-off grade stay fixed over the mine life?', 'No. It changes with price, costs, recovery and capacity constraints, and the optimal strategy is often a higher cut-off in the early years that declines over time.'),
 ],
 'refs': [REF['lane64'], REF['lane88'], REF['rendu'], REF['jorc']],
 'related': {'art': ['resources-vs-reserves', 'kriging'], 'tools': ['cut-off-grade', 'grade-converter'], 'svc': ['resource-estimation', 'commodities']},
},
{
 'slug': 'resources-vs-reserves', 'short': 'Resources vs reserves', 'cat': 'Reporting', 'icon': 'layers', 'published': P, 'updated': P,
 'title': 'Mineral Resources vs Ore Reserves: JORC Classification and UNFC Codes | Ali Alinaghi',
 'desc': 'Mineral Resources and Ore Reserves under the JORC Code: Inferred, Indicated and Measured resources, Probable and Proved reserves, Modifying Factors, the Competent Person, and their UNFC equivalents (codes 111, 122, 333) used in Iranian reports.',
 'h1': 'Mineral resources vs ore reserves under the JORC Code',
 'lede': 'In everyday speech a "reserve" is any quantity of mineral, but the international reporting codes give the word a precise meaning. Confusing resources with reserves is one of the most common reasons mining projects are misjudged.',
 'card': 'Resource and reserve categories, Modifying Factors, the Competent Person and UNFC equivalents.',
 'keywords': ['mineral resources', 'ore reserves', 'JORC Code', 'resource classification', 'proved reserve', 'probable reserve', 'UNFC'],
 'takeaways': [
  'A Mineral Resource has reasonable prospects for eventual economic extraction; an Ore Reserve is the part of it shown to be economically mineable by a techno-economic study.',
  'Resources are classified by geological confidence as Inferred, Indicated and Measured.',
  'Only Indicated and Measured Resources, after applying the Modifying Factors, convert to Probable and Proved Reserves.',
  'Public reports under JORC must be based on the work of, and taken responsibility for by, a Competent Person.',
  'The three-digit codes common in Iranian reports (111, 122, 333 and so on) come from the UNFC framework and have approximate JORC equivalents.'],
 'sections': [
  ('Why classification matters', '''<p>Investors, banks and buyers need numbers whose meaning is clear and comparable. The CRIRSCO family of reporting codes — JORC in Australasia, NI 43-101 with the CIM definitions in Canada, SAMREC in South Africa, PERC in Europe and S-K 1300 in the United States — share common definitions so that a "Measured Resource" means broadly the same thing everywhere.</p>'''),
  ('Exploration results, mineral resources and ore reserves', '''{{fig:jorc}}
<ul>
<li><b>Exploration Results:</b> data and information from exploration — drillhole and sample results — not yet estimated as a Mineral Resource.</li>
<li><b>Mineral Resource:</b> a concentration or occurrence of material of economic interest whose form, quality and quantity give reasonable prospects for eventual economic extraction.</li>
<li><b>Ore Reserve:</b> the economically mineable part of a Measured or Indicated Resource, including dilution and mining losses, demonstrated by at least a Pre-Feasibility Study. NI 43-101 calls it a Mineral Reserve.</li>
</ul>'''),
  ('Mineral resource categories', '''<ul>
<li><b>Inferred:</b> quantity and grade estimated from limited geological evidence and sampling; geological and grade continuity are implied but not verified. Inferred Resources do not convert to reserves, although most are expected to be upgraded with further exploration.</li>
<li><b>Indicated:</b> confidence sufficient to apply the Modifying Factors in enough detail for mine planning and economic evaluation.</li>
<li><b>Measured:</b> geological and grade continuity confirmed with high confidence, sufficient for detailed mine planning and final evaluation.</li>
</ul>
<p>The codes set no fixed drill spacing for each category. Classification combines geological judgement with quantitative criteria: drill spacing relative to the <a href="/en/articles/variogram/">variogram range</a>, the number of holes and samples used, kriging variance and slope of regression, the quality of <a href="/en/articles/qaqc/">QA/QC data</a> and the adequacy of density data.</p>'''),
  ('Modifying factors and reserve categories', '''<p>The Modifying Factors are the considerations that convert a resource into a reserve: mining, processing, metallurgical, infrastructure, economic, marketing, legal, environmental, social and governmental factors.</p>
<ul>
<li><b>Probable Ore Reserve:</b> the economic part of an Indicated Resource and, in some circumstances, of a Measured Resource whose Modifying Factors carry uncertainty.</li>
<li><b>Proved Ore Reserve:</b> the economic part of a Measured Resource, with the highest level of confidence.</li>
</ul>'''),
  ('The Competent Person', '''<p>Under the JORC Code, public reports of Exploration Results, Mineral Resources and Ore Reserves must be based on the work of a <b>Competent Person</b>: a member of the AusIMM, the AIG or a Recognised Professional Organisation with at least five years of experience relevant to the style of mineralisation, type of deposit and activity for which they take responsibility. NI 43-101's equivalent is the Qualified Person.</p>'''),
  ('UNFC equivalents used in Iranian reports', '''<p>Many Iranian exploration reports state reserves with three-digit codes from the United Nations Framework Classification (UNFC, 1997 edition). The first digit is the economic axis (E), the second the feasibility axis (F) and the third the geological confidence axis (G). Approximate JORC equivalents:</p>
<div class="tbl-scroll"><table class="dtable"><thead><tr><th>UNFC code</th><th>UNFC name</th><th>Approximate JORC equivalent</th></tr></thead><tbody>
<tr><td>111</td><td>Proved mineral reserve</td><td>Proved Ore Reserve</td></tr>
<tr><td>121, 122</td><td>Probable mineral reserve</td><td>Probable Ore Reserve</td></tr>
<tr><td>211</td><td>Feasibility mineral resource</td><td>Measured Resource not yet shown to be economic</td></tr>
<tr><td>221, 222</td><td>Prefeasibility mineral resource</td><td>Measured (221) or Indicated (222) Resource</td></tr>
<tr><td>331</td><td>Measured mineral resource</td><td>Measured Resource</td></tr>
<tr><td>332</td><td>Indicated mineral resource</td><td>Indicated Resource</td></tr>
<tr><td>333</td><td>Inferred mineral resource</td><td>Inferred Resource</td></tr>
<tr><td>334</td><td>Reconnaissance mineral resource</td><td>Exploration results level; not a resource</td></tr>
</tbody></table></div>
<p>The match is not one-to-one; codes 211 and 221, for example, have no exact JORC home. Converting a national report to an international standard requires a Competent Person to review the data, QA/QC and economic assumptions.</p>'''),
  ('Common reporting mistakes', '''<ul>
<li>Calling something a "reserve" without a techno-economic study; a purely geological estimate is a resource, not a reserve.</li>
<li>Adding Inferred Resources to higher categories, or using them in a reserve.</li>
<li>Reporting resources without a cut-off or a realistic mining envelope.</li>
<li>Over-optimistic classification despite weak QA/QC, density data or geological model.</li>
<li>False precision, such as tonnage to the nearest tonne; reported figures should reflect estimation uncertainty.</li>
</ul>'''),
 ],
 'faq': [
  ('Can Inferred Resources be used in economic studies?', 'Under JORC they may be used in Scoping Studies with an explicit cautionary statement, but Inferred Resources never convert to Ore Reserves and must not support a reserve declared in a Pre-Feasibility or Feasibility Study.'),
  ('Is a "proved reserve" in an Iranian report the same as a JORC Proved Reserve?', 'It is usually treated as the equivalent, but the criteria behind national reports and CRIRSCO codes are not identical; before comparing, check the estimation method, QA/QC and techno-economic studies behind the number.'),
 ],
 'refs': [REF['jorc'], REF['crirsco'], REF['cim'], REF['unfc']],
 'related': {'art': ['cut-off-grade', 'qaqc', 'kriging'], 'tools': ['cut-off-grade'], 'svc': ['resource-estimation', 'project-management']},
},
{
 'slug': 'qaqc', 'short': 'QA/QC', 'cat': 'Data and QA/QC', 'icon': 'db', 'published': P, 'updated': P,
 'title': 'QA/QC in Mineral Exploration: Standards, Blanks and Duplicates | Ali Alinaghi',
 'desc': 'A practical guide to QA/QC of exploration data: quality assurance versus quality control, certified reference materials, blanks and duplicates, insertion rates, control charts, acceptance criteria and a pre-estimation checklist.',
 'h1': 'QA/QC of exploration data',
 'lede': 'A resource estimate is never better than its data. A QA/QC programme shows that laboratory results are precise, accurate and free of contamination, and it underpins both resource classification and investor confidence.',
 'card': 'Standards, blanks and duplicates, insertion rates, control charts and acceptance criteria.',
 'keywords': ['QA/QC', 'quality control mineral exploration', 'certified reference material', 'CRM', 'blanks', 'duplicates', 'control chart'],
 'takeaways': [
  'Quality assurance (QA) is the procedures that prevent errors; quality control (QC) measures quality with control samples.',
  'Standards measure accuracy, blanks measure contamination and duplicates measure precision at each preparation stage.',
  'A standard result beyond ±3 standard deviations, or two consecutive results beyond ±2 SD on the same side, usually fails the batch.',
  'Sending a share of pulps to a second (umpire) laboratory reveals inter-laboratory bias.',
  'QA/QC results and corrective actions must be documented in the resource report; assay data quality is a JORC Table 1 criterion.'],
 'sections': [
  ('QA versus QC', '''<p><b>Quality assurance</b> is everything done before errors happen: written sampling protocols, chain of custody, a laboratory accredited to ISO/IEC 17025, team training and database management. <b>Quality control</b> measures how well that worked: control samples of known or comparable value are inserted into the sample stream and their results are monitored continuously.</p>'''),
  ('Types of control samples', '''<ul>
<li><b>Certified reference material (CRM, "standard"):</b> material with a certified grade and known standard deviation that measures <b>accuracy</b>, the closeness to the true value. Use several standards near the cut-off, average and high grades, with a matrix similar to the deposit.</li>
<li><b>Blank:</b> material without the element of interest that reveals <b>contamination</b>. Coarse blanks go through crushing; pulp blanks reveal only contamination during assay.</li>
<li><b>Duplicates:</b> measure <b>precision</b> (repeatability) at each stage — field or half-core duplicates, coarse crush duplicates and pulp duplicates.</li>
<li><b>Umpire assays:</b> a share of pulps sent to a second laboratory to reveal bias between laboratories.</li>
</ul>'''),
  ('Insertion rates', '''<p>The reporting codes set no exact rate, but common industry practice is to insert each of standards, blanks and duplicates at about one in twenty samples (5%), so that control samples total roughly 10–15%, with about 5% of pulps sent for umpire assay. Control samples should be inserted blind so the laboratory cannot distinguish them from routine samples.</p>'''),
  ('The standard control chart', '''{{fig:control}}
<p>Each standard's results are plotted in time order on a control chart. Common acceptance rules:</p>
<ul>
<li>Within ±2 standard deviations: pass.</li>
<li>Between 2 and 3 standard deviations: warning; two consecutive warnings on the same side are treated as a failure.</li>
<li>Beyond ±3 standard deviations: failure; samples in the batch around it are usually re-assayed.</li>
</ul>
<p>Beyond individual results, the <b>trend</b> matters: results drifting away from the certified value or sitting consistently on one side indicate systematic bias even if none falls outside the limits.</p>'''),
  ('Evaluating blanks and duplicates', '''<p>Blank results are compared with the method detection limit; a common threshold is a few times the detection limit (for example three to five times), and anything higher calls for a contamination check — especially when the blank follows a high-grade sample.</p>
<p>Duplicate pairs are assessed with scatter plots, relative-difference plots and the half absolute relative difference (HARD). Targets commonly cited in the technical literature are that at least 90% of pairs fall within about 10% for pulp duplicates, 20% for coarse duplicates and 30% for field duplicates; for high-nugget gold these targets are usually wider.</p>'''),
  ('When QC fails', '''<p>A failed control sample does not mean throwing data away; it starts a documented process: check for sample swaps or labelling errors, contact the laboratory, re-assay all or part of the batch, and record the result and decision in the database. The resource report should summarise QA/QC results, failures and corrective actions.</p>'''),
  ('Pre-estimation checklist', '''<ul>
<li>Every assay batch contains standards, blanks and duplicates, and their results have been reviewed.</li>
<li>Failed batches have been re-assayed and replacement results stored in the database.</li>
<li>Primary laboratory bias has been checked against umpire results.</li>
<li>Historical data and different drilling types (diamond core and reverse circulation) have been compared for bias.</li>
<li>Core recovery, density measurements and downhole surveys have been checked.</li>
<li>QA/QC results are documented in the report and in JORC Table 1.</li>
</ul>'''),
 ],
 'faq': [
  ('Why should control samples be blind?', 'If the laboratory can identify control samples it may, even unintentionally, treat them differently, and their results would no longer represent the quality of routine samples.'),
  ('What can be done with historical data that has no QA/QC?', 'Re-assay a share of retained pulps or core, drill twin holes, and measure the bias of the historical data against new data; the outcome affects resource classification.'),
 ],
 'refs': [REF['abz08'], REF['abz16'], REF['sb'], REF['jorc']],
 'related': {'art': ['resources-vs-reserves', 'kriging', 'exploration-stages-iran'], 'tools': ['grade-converter'], 'svc': ['resource-estimation', 'project-management']},
},
{
 'slug': 'exploration-stages-iran', 'short': 'Exploration stages', 'cat': 'Exploration', 'icon': 'target', 'published': P, 'updated': P,
 'title': 'Stages of Mineral Exploration in Iran: From Reconnaissance to Discovery Certificate | Ali Alinaghi',
 'desc': 'The technical stages of mineral exploration (reconnaissance, prospecting, general and detailed exploration) and the administrative path in Iran: exploration licence, final exploration report, discovery certificate and exploitation licence, with common mistakes.',
 'h1': 'Stages of mineral exploration in Iran',
 'lede': 'Exploration is a staged process for reducing uncertainty: each stage should cost less than the next and answer clearly whether the licence deserves further investment. This article reviews the technical stages and the administrative path for exploration in Iran.',
 'card': 'Reconnaissance, prospecting, general and detailed exploration, and the path from licence to discovery certificate.',
 'keywords': ['mineral exploration stages', 'mineral exploration Iran', 'prospecting', 'general exploration', 'detailed exploration', 'exploration licence Iran', 'discovery certificate'],
 'takeaways': [
  'Exploration proceeds through reconnaissance, prospecting, general exploration and detailed exploration, with larger scales and higher costs at each stage.',
  'Each stage should end with go/no-go criteria agreed in advance.',
  'In Iran, exploration starts with registering an area and obtaining an exploration licence from the Ministry of Industry, Mine and Trade, and leads to a discovery certificate once the final exploration report is approved.',
  'Data collected with proper QA/QC from the earliest stages can later support a resource estimate that meets international standards.'],
 'sections': [
  ('The four technical stages', '''<ol class="steps">
<li><b>Reconnaissance:</b> regional geological maps, previous reports, satellite imagery and airborne geophysics; first field visits and selection of promising areas.</li>
<li><b>Prospecting:</b> geological mapping and geochemical sampling of stream sediments, soils and rocks to define anomalies; the aim is to shrink the area to a few clear targets.</li>
<li><b>General exploration:</b> large-scale maps, trenches, ground geophysics and the first drillholes to confirm mineralisation and make a first estimate of size and grade.</li>
<li><b>Detailed exploration:</b> systematic drilling, sampling with QA/QC, density measurements, metallurgical testing and a resource estimate as the basis of feasibility studies.</li>
</ol>
<p>Each stage brings larger map scales, denser data and higher cost. The sequence is consistent with international frameworks and with the geological confidence axis of the UNFC classification.</p>'''),
  ('Tools for each stage', '''<p>In the early stages, <a href="/en/services/remote-sensing/">remote sensing</a> and <a href="/en/services/exploration-geochemistry/">geochemistry</a> screen large areas cheaply. Closer to the target, <a href="/en/services/exploration-geophysics/">ground geophysics</a> and drilling take over. In detailed exploration, <a href="/en/services/3d-geological-modelling/">3D modelling</a> and <a href="/en/services/resource-estimation/">resource estimation</a> turn the data into a number decisions can rest on.</p>'''),
  ('The administrative path in Iran', '''<p>In Iran the legal framework for mining is set by the Mining Law and its executive regulations, and licences are issued by the Ministry of Industry, Mine and Trade. The general path is:</p>
<ol class="steps">
<li>Register the requested area in the mining cadastre system and check overlaps with other areas.</li>
<li>Obtain an <b>exploration licence</b> based on an exploration work programme, supervised by a qualified person.</li>
<li>Carry out the work and submit the <b>final exploration report</b>.</li>
<li>Have the report reviewed and approved, and receive a <b>discovery certificate</b> for a mineral with a defined reserve.</li>
<li>Prepare a mining plan and apply for an <b>exploitation (mining) licence</b>.</li>
</ol>
<p>Administrative details, documents and deadlines can change as regulations are amended; check the latest rules with the official authorities before acting.</p>'''),
  ('Staged decision making', '''<p>Most exploration spend goes into drilling. A good exploration programme states before each stage which results will lead to continuing and which to stopping — for example a minimum intercept thickness and grade, or anomaly continuity across several profiles. This avoids spending on areas without enough evidence and is transparent for investors.</p>'''),
  ('Common mistakes', '''<ul>
<li>Drilling before mapping and geochemistry are complete, with no deposit model to target against.</li>
<li>No <a href="/en/articles/qaqc/">QA/QC</a> in early sampling, which invalidates the data for a later resource estimate.</li>
<li>Poor recording of coordinates, downhole surveys and core recovery.</li>
<li>No budget for density measurements and metallurgical tests, which resource and reserve classification require.</li>
<li>Reporting results in a form that cannot be reconciled with international standards, making investment harder to attract.</li>
</ul>'''),
 ],
 'faq': [
  ('How long does exploring a licence take?', 'Depending on the size of the area, the commodity and access, from a few months for prospecting to several years for the detailed exploration of a large deposit.'),
  ('Can historical exploration data be used?', 'Yes, once validated: check coordinates, assay methods and QA/QC, and re-assay or drill confirmation holes where needed. Validated historical data can cut exploration cost substantially.'),
 ],
 'refs': ['Mining Law of the Islamic Republic of Iran (1998, amended 2011) and its executive regulations.', REF['unfc'], REF['jorc']],
 'related': {'art': ['qaqc', 'resources-vs-reserves'], 'tools': [], 'svc': ['mineral-exploration', 'project-management', 'exploration-geochemistry']},
},
]
