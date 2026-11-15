# Findings

What the search found, three characterised candidate sites, and the limits of each claim.
Written Sun Nov 15, 2026. All numbers come from the code and data in this repository. Every cited site fact was checked against the wording of its source, and the supporting quote is recorded in `SOURCES_CHECK.md` so anyone can confirm it with a text search.

Status words used here:
- **Measured**: computed from NASA or ESA data by the code in `pipeline/`.
- **Cited**: stated on a page we read; link given.
- **Not established**: we looked and found nothing, or did not look. Never filled with a guess.

---

## 1. Three findings from the search

### 1.1 At kilometre scale, most of Earth's bare land is shaped differently from the lunar south pole
We measured how fast height differences grow with distance (the Hurst exponent used in lunar roughness studies) on both bodies with the same code.
- Lunar south pole, 11,221 spots: median 0.93. Published value for the lunar highlands: 0.95 (Rosenburg et al. 2011).
- Earth bare land at the same slope (5 to 10 degrees): 0.71. Only 3.3% of 236,193 Earth windows reach 0.85.
- The gap is larger over long distances (320 m to 2.6 km) than short ones, so it is unlikely to be a sensor effect (see `AUDIT.md`, section D).

Plain reading: on Earth, valleys and ridges repeat every kilometre or so, so the ground stops rising. On the lunar highlands, slopes carry on across several kilometres. Matching a lunar slope is easy on Earth; matching its slope and its broad, smooth character is rare.

### 1.2 The places that do match are polar deserts, high cold deserts and young volcanic massifs
Scoring every bare-land window on Earth against 1,737 lunar spots suitable for landing, the best 200 fall in a few regions: the Canadian Arctic islands, north and east Greenland, the central Andes, the high plateaus of Asia, and the Tibesti massif in the Sahara. Without being told about them, the search also ranked the Antarctic Dry Valleys 4th for Malapert Massif terrain and placed Devon Island (site of Haughton Crater) at the top for long darkness. Both are established analog sites.

### 1.3 What the method can and cannot recognise
Tested against 21 known lunar analog sites (15 from the ESA Catalogue of Planetary Analogues), the terrain score beats random bare land 61 to 65% of the time, where 50% is chance. That is weak-to-modest skill, so we call the tool a terrain screen, not a validated analog finder.
- Recognised: sites valued for their landscape (Atacama 0.90, Askja 0.85, Antarctic Dry Valleys 0.83, Axel Heiberg Island 0.79, Haughton 0.79).
- Not recognised: sites valued for one small feature or a rock type (Meteor Crater 0.38, Cinder Lake 0.33, Craters of the Moon 0.13).
- A finer second stage (2 km windows at 30 m) was built and tested. It did not help (56 to 57%), so it is not part of the tool.

Details: `BENCHMARK.md`.

### 1.4 Which parts of the lunar south pole can be rehearsed on Earth, and which cannot
Every one of the 11,221 lunar spots was scored against the whole Earth library (`pipeline/modal_testability.py`).
- Rover-scale terrain: 96% of lunar spots have at least one Earth window scoring 0.8 or higher. For spots suitable for landing the figure is also 96%.
- The steepest lunar ground is the exception. Where the median slope exceeds 20 degrees, only 33% of spots have such a match; between 15 and 20 degrees, 70%.
- For 62% of lunar spots the single best terrain match is in Greenland or the Canadian Arctic, and for 21% it is in the central Andes.
- Shadow work, as we score it, has no strong stand-in anywhere: no lunar spot has an Earth window at 0.7 or higher, mainly because Earth is far warmer than shadowed lunar ground.

Caution: taking the best of 236,193 windows will always find something that scores well, and the terrain score has only modest measured skill. This map shows where Earth offers candidates, not where a proven analog exists. It is available in the app as the "Earth match" layer.

---

## 2. Three characterised candidate sites

How they were chosen: the 200 best windows by average terrain score, then removed if within 300 km of a known analog site (43 removed) or flagged by an ice and snow proxy (23 removed). From the 139 left we took one polar, one high-altitude and one hot-desert site to show how an analog can be strong on one dimension and weak on another.

All three are **screened candidates characterised from satellite data and secondary literature. None has been visited or field-checked.** Place names are matched from coordinates.

Lunar reference values (measured): Malapert Massif has median slope 16.5 degrees, scaling number 0.96, relief 1,475 m, average temperature 138 K, peak 273 K, sunlit 39% of the time. Typical landing-like spots near the pole have median slopes of about 7 to 8 degrees.

Common to all three (measured): average terrain score 0.75 to 0.76 across the 1,737 landing-like lunar spots (range 0.56 to 0.89; at or above 0.70 for 75% of them). All three are gentler than the lunar massifs: median slope about 7 degrees, so against Malapert Massif they match its terrain character (0.87 to 0.95) far better than its steepness (0.45 to 0.58).

### 2.1 East Greenland, inner fjord zone (73.95 N, 25.18 W)

| | |
|---|---|
| Stands in for | Typical landing-like terrain near the lunar south pole, for traverse and low-sun operations |
| Terrain score | 0.76 average over landing-like spots; 0.70 against Malapert Massif; 0.69 against de Gerlache Rim 2 |
| Status | Screened candidate |

**What matches (measured)**
- Terrain character: scaling number 0.93 (Moon 0.93 to 0.96). Slope keeps 95% of its value from 80 m to 320 m, as on the Moon.
- Bare ground in summer: vegetation index 0.12.
- Low sun: in February and October the sun never rises above 2.5 and 6.3 degrees, close to the 5.5 degree maximum at Malapert Massif.
- Long darkness: about 92 days of continuous polar night, far beyond the 120 hours NASA says base systems must survive.
- Summer ground temperature 275 to 282 K, close to the lunar peak of 268 to 273 K on sunlit ground.

**Where it breaks (measured)**
- Gentler and lower: median slope 7.3 degrees and relief 630 m, against 16.5 degrees and 1,475 m at Malapert Massif.
- The low-sun months are the snow months. Ground is snow-covered from October to May and bare only June to September, when the sun reaches 18 to 39 degrees. September is the best compromise: bare ground and about 6 hours a day with the sun below 12 degrees.
- Cold is not matched: coldest-month night average 246 K against a lunar average of 138 K.
- Ice margin: 2 of the 9 surrounding map cells stay bright all year, so permanent snow or ice is within about 5 km.
- Earth's atmosphere scatters light and softens shadows. Gravity, vacuum and radiation cannot be reproduced.

**Surface and geology**
- Cited: the part of the East Greenland Caledonian fold belt studied at about 73.5 to 74 N (Andree Land) is "dominated by metasedimentary rocks, variably intruded by granite sheets and veins" (GEUS Report 1998/28).
- Not established: the rock type at this exact window, and whether the named land area is Andree Land (its stated centre is 73.58 N, 26.00 W).

**Operations**
- Cited: inside Northeast Greenland National Park. Mestersvig, about 195 km south, has an 1,800 m gravel runway (military outpost). Zackenberg research station, about 150 km east-north-east, operates in summer.
- Not established: permit rules, cost and season of access.

**Prior analog use:** none found on the pages read. This is not a full literature search.

**How it could help:** rehearsing rover traverses and navigation on bare, kilometre-smooth terrain under a low sun with long shadows, and testing power and operations through a real polar night.

### 2.2 South-east Pamir, on the Afghanistan and Tajikistan border (37.32 N, 73.11 E)

| | |
|---|---|
| Stands in for | Typical landing-like terrain near the lunar south pole, for traverse-scale terrain on bare ground |
| Terrain score | 0.76 average over landing-like spots; 0.69 against Malapert Massif; 0.68 against de Gerlache Rim 2 |
| Status | Screened candidate |

**What matches (measured)**
- Terrain character: scaling number 0.90; slope keeps 87% of its value from 80 m to 320 m.
- Bare ground for most of the year: vegetation index 0.11; snow shows only in single months (March and December in 2024).
- Large day to night ground temperature swing: about 27 K in July, and coldest-month nights near 245 K.

**Where it breaks (measured)**
- No low sun and no long darkness: midday sun between 29 and 76 degrees all year, longest night about 15 hours. It is a terrain analog only.
- Gentler and lower than the massifs: median slope 7.1 degrees, relief 766 m.
- Summer ground reaches 307 K, well above any lunar polar temperature.
- Gravity, vacuum and radiation cannot be reproduced.

**Surface and geology**
- Cited: the high Pamir plateau is a cold continental desert environment, in one of the most tectonically active places in the world (UNESCO World Heritage listing for Tajik National Park). Lake Zorkul, about 55 km east, lies at 4,130 m.
- Not established: rock type at the window; elevation of the window itself.

**Which country (measured, with a caution)**
- On Natural Earth boundaries at 1:50 million, the window centre falls in Afghanistan (the Wakhan Corridor), about 4 km from the border with Tajikistan. That map scale is too coarse to be certain, and the 10 km window probably spans both countries. An earlier version of this brief placed the site in Tajikistan; that was a naming error, corrected here.
- Nearest town of over 1,000 people on the Afghan side: Khandud, about 81 km (GeoNames).

**Operations**
- Cited, for the Tajik side: the Pamir Highway is the region's main road. Murghob, the nearest town named on the pages read (about 120 km north-north-east), sits at about 3,600 m with an annual mean of -3.9 C. Tajik National Park covers almost the whole Pamir and has the country's highest protection status; the Zorkul Nature Reserve is nearby.
- Not established: which country the usable ground is in, whether it lies inside a protected area on either side, what permits a border-zone site needs, and current security and access conditions on the Afghan side. Until those are known this site should not be described as reachable by road.

**Prior analog use:** none found for the Pamir on the pages read. A related region is in use: ISRO began the Ladakh Human Analogue Mission at Leh, India, in November 2024, so high Asian cold deserts are being taken up as analogs.

**How it could help:** if access proves possible, long rover traverse tests on bare, lunar-like terrain at traverse scale, with strong daily thermal cycling. Otherwise, like Tarso Tousside, as a terrain model for simulation.

### 2.3 Tarso Tousside, Tibesti massif, Chad (21.05 N, 16.45 E)

| | |
|---|---|
| Stands in for | Malapert Massif and de Gerlache Rim terrain, as a terrain model only |
| Terrain score | 0.76 against Malapert Massif (rank 238 of 236,193 windows, top 0.1%); 0.74 against de Gerlache Rim 2 |
| Status | Screened candidate; not usable for field work at present |

**What matches (measured)**
- The closest terrain character of the three: scaling number 0.96 (Malapert 0.96); relief 1,052 m; 38% of ground steeper than 10 degrees.
- Bare all year: vegetation index 0.12, no snow signal.

**Where it breaks (measured and cited)**
- Hot, not cold: ground 297 to 314 K by day, 279 to 293 K at night.
- High sun, short nights: no low-sun or darkness analogy.
- Volcanic rock. The Global Volcanism Program lists trachyte, trachyandesite and basalt. The lunar south pole is highland terrain, not a volcano, so the similarity is in shape, not in origin or material.
- Access: a 2007 scientific paper on the massif calls travel "problematic" and mentions "perhaps tens of thousands" of landmines in the wider region; the range has a history of hostage-taking and armed struggles. Current conditions: not established.
- Gravity, vacuum and radiation cannot be reproduced.

**Surface and geology (cited)**
- The window centre coincides with Tarso Tousside (21.03 N, 16.45 E, 3,265 m), a volcano with young lava flows and fumaroles and no confirmed recent eruption (Global Volcanism Program).

**Prior analog use (cited):** the Tibesti volcanoes have been compared with Martian volcanoes, including Elysium Mons (Malin 1977, as cited in Permenter and Oppenheimer 2007; also noted on the Tibesti Mountains page). No lunar use was found. So this is a known Mars comparison turning up in a lunar terrain search.

**How it could help:** as a terrain twin for simulation. Its open 30 m elevation data could stand in for massif-like lunar terrain when testing rover path planning and slope handling in software, without visiting the site.

---

## 3. What these three show together

| | East Greenland | South-east Pamir (border zone) | Tarso Tousside |
|---|---|---|---|
| Terrain character | Strong | Strong | Strongest |
| Steepness of the massifs | Weak | Weak | Partial |
| Low sun and long shadows | Yes, but in snow months | No | No |
| Long darkness | Yes | No | No |
| Cold | Partial (summer peak only) | Partial (nights) | No |
| Bare ground season | June to September | Most of the year | All year |
| Field access | Remote, by air | Not established (international border zone) | Not at present |
| Rock type like lunar highlands | Not established | Not established | No (volcanic) |

No single site matches on every dimension. The polar site adds the light and darkness that the other two lack, but only when the ground is snow-covered. That trade-off is itself a result.

A fourth area, northern Ellesmere Island (81.1 N, 71.5 W), has the best terrain score of the shortlist (0.77 against Malapert Massif, scaling number 0.95). We did not brief it because it lies 406 km from Axel Heiberg Island and in the same island group as Haughton Crater, both established analog sites.

Separate context (cited): NASA already uses anorthosite from West Greenland, about 85 km south-west of Kangerlussuaq, as a lunar highlands soil simulant (GreenSpar). That is a different part of Greenland from our terrain candidates and we make no claim about the rock at our sites.

---

## 4. Limits that apply to everything above

- The terrain score has weak-to-modest measured skill (61 to 65% against chance of 50%).
- Windows are 10 km at 80 to 90 m detail. Rocks, small craters, soil strength and dust are not seen.
- Rock type is not part of the score.
- Ice and snow are screened with a proxy from surface temperature and brightness, not a glacier map.
- Earth temperatures are 2024 monthly averages from one satellite product.
- Lunar region centres are approximate.
- Darkness and low-sun scores depend almost entirely on Earth latitude, not on the lunar spot.
- Site literature checks used the pages listed below. Absence of prior analog use on those pages is not proof of absence.
- Independent project. Not a NASA product.

---

## 5. Sources

Data
- NASA LRO LOLA south pole elevation, slope and permanent shadow (PGDA product 90, Barker et al. 2023): https://pgda.gsfc.nasa.gov/products/90
- NASA LRO lunar polar illumination (PGDA product 69, Mazarico): https://pgda.gsfc.nasa.gov/products/69
- NASA LRO Diviner Polar Resource Products: https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/
- Copernicus DEM GLO-90 and GLO-30 (ESA): https://registry.opendata.aws/copernicus-dem/
- NASA MODIS land surface temperature MOD11C3 and vegetation MOD13C2 (2024)

Method
- Rosenburg et al. 2011, lunar slopes and roughness; NASA PGDA product 70: https://pgda.gsfc.nasa.gov/products/70
- Schrader et al. 2009, lunar simulant Figure of Merit (NASA)
- ESA Catalogue of Planetary Analogues (Preston, Grady and Barber 2012): https://esamultimedia.esa.int/docs/gsp/The_Catalogue_of_Planetary_Analogues.pdf
- NASA Moon Base User's Guide (2026) and Lunar Mobility Drivers and Needs (2024); links in `METHOD_REASONING.md`

Sites
- Global Volcanism Program, Tarso Tousside: https://volcano.si.edu/volcano.cfm?vn=225010
- Permenter and Oppenheimer 2007, Volcanoes of the Tibesti massif (Bulletin of Volcanology): https://repository.geologyscience.ru/server/api/core/bitstreams/e3581337-5b60-46f6-a83f-761305e28290/content
- Tibesti Mountains: https://en.wikipedia.org/wiki/Tibesti_Mountains
- GEUS Report 1998/28, Caledonian geology of East Greenland 72 to 74 N: https://data.geus.dk/pure-pdf/14977.pdf
- Northeast Greenland National Park: https://en.wikipedia.org/wiki/Northeast_Greenland_National_Park
- Andree Land: https://en.wikipedia.org/wiki/Andr%C3%A9e_Land_(Greenland)
- UNESCO World Heritage List, Tajik National Park: https://whc.unesco.org/en/list/1252
- Zorkul: https://en.wikipedia.org/wiki/Zorkul
- Murghob: https://en.wikipedia.org/wiki/Murghob
- Pamir Mountains: https://en.wikipedia.org/wiki/Pamir_Mountains
- Ladakh Human Analogue Mission: https://en.wikipedia.org/wiki/Ladakh_Human_Analogue_Mission
- NASA GreenSpar lunar highlands simulant: https://ares.jsc.nasa.gov/projects/simulants/greenspar.html

Use of AI: research, planning, code and drafting of this document were done with Claude (Anthropic). Cited facts were then checked one by one against the source wording (`SOURCES_CHECK.md`); one claim that could not be confirmed was removed.
