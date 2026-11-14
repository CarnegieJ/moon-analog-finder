# HANDOFF: NASA Space Apps 2026, "Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars"

Owner: Shashi (team "fightingdreamers", Raleigh, NC local event)
Prepared: Sat Nov 14, 2026
Read this whole file before writing code. Section 0 is the clock.
**Scope: Moon only for now** (Shashi, Nov 14). The method and its NASA reasoning are in **METHOD_REASONING.md**; read it first, it overrides Mars items elsewhere.
Start with the small v0 set in **STARTER_SET.md** (sites, data, scoring logic, reusable references). Then run the method selection tasks in **METHOD_TASKS.md** (same folder). They decide which dimensions and which similarity method to use.

---

## 0. Time budget (most important constraint)

- Hackathon runs **Nov 14 to Nov 15, 2026**. Submission opens Sat Nov 14 9:00 AM and closes **Sun Nov 15 11:59 PM, local time of the team's Local Event** (Raleigh, so Eastern Time; the ET part is inferred, the "local time" rule is verified on spaceappschallenge.org/2026).
- That leaves roughly 30 to 36 working hours. Scope everything to a working demo plus submission assets by **Sun ~8 PM ET**, leaving 4 hours of buffer.
- Precompute everything offline. The demo must be a static site that loads instantly. No live calls to NASA APIs during judging.

---

## 1. The problem, in plain terms

Source: challenge page (Details tab) plus the challenge author's video (NASA Earth Science Division; name auto-transcribed as "Sidameit Bukabara", spelling unconfirmed).

**Task:** Use open Earth, Moon, and Mars data from NASA and partner agencies to find and characterize Earth locations that are useful analogs for (a) candidate permanent Moon base sites and/or (b) future Mars landing/exploration sites. Present findings as a map, visualization, or tool.

What the author stressed in the video (paraphrased):

1. **Think scientifically, not visually.** "Not simply a place that looks like the Moon or Mars." Similarity must be argued with data: geology/minerals, temperature extremes, illumination, ice/permafrost, dust processes, volcanic terrain, caves/lava tubes.
2. **Operations matter too.** Analogs can be judged by usefulness for landing, navigation, mobility, robotics, construction, resource use (ISRU), and human ops.
3. **No analog is perfect. Say where it works, how well, and where it breaks.** Earth cannot reproduce lunar gravity, vacuum, the thin Martian atmosphere, or the radiation environment. Showing the breakdown is part of the score.
4. **Do not just rediscover known sites** (Atacama, Antarctica, Iceland, Hawaii, Mojave, Death Valley, Haughton Crater). "Surprise us." Find unexpected places or connections.
5. Accepted forms: one remarkable site, a comparison of sites, or **a map / similarity metric / interactive app / ML approach that systematically searches Earth for unrecognized analogs.**
6. Processes count, not only places (dust storms, ice dynamics, sedimentation, volcanism, water alteration).
7. Scale matters: a single crater or valley inside a desert can be a better analog than the whole desert.

Dimensions the page lists (use these as the feature taxonomy):
geology/mineralogy; terrain (elevation, slope, roughness, craters); temperature, illumination, extremes; water/ice/permafrost; dust, wind, erosion; biology/habitability; caves/subsurface; landing/mobility/navigation/construction conditions.

---

## 2. How it will be judged (verified, from Space Apps guides; guides are 2024/2025 versions, 2026 may differ slightly)

Five criteria, equally weighted in practice: **Influence (aka Impact), Creativity, Validity (scientifically valid, works in real world), Relevance (answers the challenge, complete, usable), Presentation.**

Relevant global awards: Best Use of Science, **Best Use of Data**, Best Use of Technology, Best Mission Concept, Best Storytelling.

Submission requirements (2025 guide, assume same for 2026):
- Demo: **video up to 30 seconds** (English subtitles) **or up to 7 slides** including title. Going over = ineligible for global judging.
- Public links only (no login): demo link + final project link (GitHub repo / live site).
- Form fields: Project name, high-level summary, detailed description, **NASA data used and how**, partner/other data, references (all code, data, images), **Use of AI** disclosure.
- **Must use NASA data** to be eligible for global awards.
- AI-generated images/video need a visible "AI-generated" watermark. No NASA logos in AI content.
- Team 1 to 6 people, all at the same local event.

---

## 3. Project options (Shashi picks one; do not start building until he confirms)

Each option opens with its one-line core: what goes in, what comes out, who it helps.

### Option A: "Analog Fidelity Map" (multi-dimension similarity search over the whole Earth)
**Core:** Takes a target planetary site (e.g., an Artemis III region or a Mars landing site) and NASA/partner Earth grids, outputs a global ranked map of Earth cells scored per dimension with an explicit "where it breaks" panel, helping mission planners and analog-field-test teams find under-studied test sites.
- Compute a feature vector for each target from Moon/Mars data and the same features for Earth grid cells. Score similarity per dimension (not one blended number), then a weighted composite the user can re-weight with sliders.
- Known analog sites are shown as reference pins and **filtered out of the "new candidates" list**, which directly answers "surprise us".
- Always-on "cannot match" row: gravity, vacuum/atmosphere, radiation, shown as 0% for every Earth site.
- Fits: systematic search, similarity metric, map, Best Use of Data. Highest coverage of the brief.
- Risk: data wrangling across 3 bodies in 30 hours. Mitigate by keeping the grid coarse and features few (see Section 5).

### Option B: "Pin Report Card" (drop a pin anywhere on Earth, get an analog scorecard)
**Core:** Takes any Earth location a user clicks, outputs a scorecard of how it compares with the lunar south pole and one Mars site on each dimension plus what it is useful for testing, helping students, educators, and field teams quickly judge a site.
- Same features as A, but evaluated on demand at a point instead of a ranked global map.
- Easier to explain and demo. Weaker on "systematic discovery".
- Can be the front end of A (A's map, click a cell, get B's card). A+B together is the strongest combo if time allows.

### Option C: "Long Shadows" (lunar south pole illumination and cold-trap ops analog)
**Core:** Takes lunar south pole illumination/temperature data (LRO LOLA + Diviner) and Earth terrain plus sun geometry and surface temperature, outputs a short list of Earth sites where low sun angle, long shadows, and extreme cold together mimic base operations at the Artemis III regions, helping rover navigation and lighting/power test planning.
- Narrow, deep, very "Artemis base" focused. Strong Validity and Mission Concept story.
- Needs horizon/shadow modeling from DEMs, which is fiddly. Earth sites will cluster at high latitudes (likely Arctic Canada, Svalbard, Greenland, Antarctica), which risks rediscovering known areas.

### Option D: "Dust Engine" (Mars dust process analog)
**Core:** Takes Earth aerosol/dust climatology from NASA satellites and Mars dust records, outputs a map of Earth regions whose dust-storm regime (frequency, seasonality, lofting) best mirrors Mars, helping engineers test dust mitigation for solar panels, seals, and habitats.
- Process-based analog, which the author explicitly invited. Few teams will do it.
- Mars dust datasets are not yet verified (see Section 4), so higher data risk.

**Suggested default if Shashi has no preference: A with B as the click interaction, Moon target first, Mars second if time remains.** This is a suggestion, not a decision. Prior art check (Section 6) shows existing work uses only image texture or a single basin, so a multi-dimension, physically grounded, explainable score is a defensible novelty claim.

---

## 4. Data sources (status: VERIFIED = URL/content confirmed by fetch today; UNVERIFIED = from general knowledge, confirm before relying on it)

### Moon
| Data | What | Where | Status |
|---|---|---|---|
| LRO Diviner Polar Resource Products (PRP) | Polar thermal/resource table, north + south, ~605 MB each, ASCII fixed-width, to 80 deg latitude. Columns: triangle vertices, center lon/lat/alt, temp_avg (K, 2 cm depth), temp_max (K), ice_depth (m, -999 invalid) | https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/ (field offsets in dlre_prp_south.xml; the .FMT file is not in the archive) | VERIFIED |
| Diviner Polar Cumulative Products (PCP) | diurnal + seasonal polar temperature products | .../data_derived_pcp/ | VERIFIED (format unknown) |
| Diviner Global High-Res Mosaics (GHRM) | GeoTIFF + IMG | .../data_derived_ghrm/ | VERIFIED |
| Diviner landing page | all bundles, caveat on solar channels after 2019 | https://pds-geosciences.wustl.edu/missions/lro/diviner.htm | VERIFIED |
| LOLA GDR / SLDEM2015 | gridded topography (slope/roughness derivable) | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/ and .../sldem2015/ | VERIFIED |
| LOLA data node (more current, polar products) | | http://imbrium.mit.edu/ | VERIFIED link exists; polar slope/illumination products UNVERIFIED |
| Mini-RF radar mosaics | radar roughness, possible ice signatures | https://pds-geosciences.wustl.edu/lro/lro-l-mrflro-5-global-mosaic-v1/lromrf_1001/ | VERIFIED |
| Lunar ODE search | query tool | https://ode.rsl.wustl.edu/moon/ | VERIFIED link |
| Moon Trek WMTS tiles | visual basemaps for UI | https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon (template `.../1.0.0/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png`, layer IDs from GetCapabilities) | VERIFIED template; specific layers UNVERIFIED |

Moon targets: Artemis III candidate regions, **nine regions (NASA, Oct 28 2024, RELEASE24-136): Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain.** VERIFIED: https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/
Selection criteria NASA used (2022 release, VERIFIED): slope, Earth comms, lighting (continuous sun over 6.5 days), proximity to permanently shadowed regions. Region boundary coordinates are NOT in the release; approximate centers must be sourced (UNVERIFIED, flag in UI as approximate).

### Mars (all UNVERIFIED today, confirm first)
- MOLA global DEM (USGS Astrogeology / PDS Geosciences), TES thermal inertia and albedo, Mars Trek WMTS (https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars, template VERIFIED).
- Targets: Jezero Crater (Perseverance), Gale Crater (Curiosity). Human landing candidate zones list UNVERIFIED.
- Mars ODE: https://ode.rsl.wustl.edu/mars/ (UNVERIFIED).

### Earth
| Data | What | Where | Status |
|---|---|---|---|
| Copernicus DEM GLO-30 / GLO-90 | elevation -> slope, roughness, relief | AWS S3 `copernicus-dem-30m`, `copernicus-dem-90m` (eu-central-1), anonymous: `aws s3 ls --no-sign-request s3://copernicus-dem-90m/` | VERIFIED |
| AppEEARS API | point/area extraction of MODIS etc., GeoTIFF/NetCDF | https://appeears.earthdatacloud.nasa.gov/api (Earthdata Login, Bearer token ~48h; task types point/area; e.g. MOD11A1.061 LST_Day_1km, SRTMGL1_NC.003) | VERIFIED |
| MODIS LST (MOD11) | surface temperature min/max/diurnal range | via AppEEARS or Earthdata Search | VERIFIED product exists in AppEEARS docs; monthly 0.05 deg CMG variant (MOD11C3) UNVERIFIED |
| Earthdata Search | discovery portal | https://search.earthdata.nasa.gov/ | VERIFIED (resource page) |
| Worldview | imagery for visuals | https://worldview.earthdata.nasa.gov/ | VERIFIED |
| Copernicus Data Space | Sentinel-1 SAR, Sentinel-2 optical; STAC, Sentinel Hub, openEO; free login | https://dataspace.copernicus.eu/ (STAC: https://browser.stac.dataspace.copernicus.eu/) | VERIFIED |
| CSA RADARSAT-1 / RCM | SAR | https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1 , .../rcm | VERIFIED links |
| CSA SAR tutorial | beginner RADARSAT plotting (GDAL, cartopy, QGIS) | https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial | VERIFIED |
| ESA Open Science Catalog | | https://opensciencedata.esa.int/ | VERIFIED link |
| JAXA G-Portal | snow, vegetation, precipitation products | https://gportal.jaxa.jp/gpr/ | VERIFIED link |
| ASTER GED (emissivity, proxy for mineralogy/silica) | | AppEEARS / LP DAAC | UNVERIFIED |
| MODIS NDVI, MODIS albedo, MERRA-2 / MODIS AOD (dust), ESA CCI permafrost | | | UNVERIFIED |

Needs: an **Earthdata Login** account (free) for AppEEARS. Shashi must create it himself; do not create accounts for him.

---

## 5. Recommended technical plan (for Option A + B; adapt if he picks another)

### Feature set (keep to 5 to 6; each must be computable on both bodies)
| Dimension | Earth source | Moon source | Mars source |
|---|---|---|---|
| Slope distribution (median, p90) | Copernicus DEM | LOLA GDR/SLDEM | MOLA |
| Roughness (std of elevation residual at ~1 km) | Copernicus DEM | LOLA | MOLA |
| Local relief / crater-like depressions | Copernicus DEM | LOLA | MOLA |
| Temperature extremes (min, max, range) | MODIS LST | Diviner PCP/PRP | TES / MCS (UNVERIFIED) |
| Bareness (no vegetation) | NDVI | always bare | always bare |
| Ice/frozen ground presence | permafrost / snow products | Diviner ice stability (if in PRP) | known ice maps (UNVERIFIED) |

Scoring rule: per dimension, similarity = 1 minus normalized distance, where normalization uses physically meaningful ranges (document them in `docs/methods.md`). Report per-dimension scores, never only the composite. Temperature will score low for the Moon everywhere on Earth (lunar extremes far exceed Earth's); show that honestly rather than rescaling it away. That honesty is a Validity point.

### Grid
- Earth: ~5 km cells (aggregate GLO-90), pre-masked to bare/arid/polar land with NDVI to cut compute. Process continent-by-continent, cache to Parquet.
- If time is short: sample 50k random bare-land points instead of a full grid.

### Stack
- Pipeline: Python 3.11, rasterio, xarray, numpy, geopandas, scikit-learn, requests. Scripts in `pipeline/`, one per source, each idempotent with a local cache dir.
- Output: `web/public/data/*.geojson` or FlatGeobuf/PMTiles for the map, plus `targets.json`.
- Front end: React + Vite + MapLibre GL (or deck.gl for the heat layer). Panels: target picker, weight sliders, ranked list ("New candidates" vs "Known analogs"), radar chart per site, "Where it breaks" box.
- Deploy: GitHub Pages or Vercel, public, no login.

### Repo layout
```
/pipeline   fetch_*.py, features_*.py, score.py
/data       (gitignored caches)
/web        React app
/docs       methods.md, data_sources.md, ai_use.md
README.md
```

### Milestones (ET)
1. **Sat by 6 PM:** Shashi confirms option; Earthdata login works; Copernicus DEM tiles for 2 test regions downloaded; LOLA south pole DEM downloaded; DLRE_PRP.FMT read.
2. **Sat by midnight:** Slope/roughness/relief features on Moon targets + Earth test regions. First similarity numbers.
3. **Sun by noon:** Global (masked) Earth grid scored for 2 to 3 Moon targets. Static map app showing results.
4. **Sun by 4 PM:** Report card panel, known-analog filter, breakdown box. Mars target if feasible.
5. **Sun by 8 PM:** 30-second video or 7 slides, README, NASA data section, AI disclosure, submit.

### Validation (do not skip; this is the Validity score)
- Sanity check: known analogs (Haughton Crater, Atacama, Mauna Kea area, Death Valley) should score reasonably high on at least some dimensions. If they score near zero, the features are wrong.
- Spot-check top 5 new candidates in Worldview imagery and explain each in one paragraph with numbers.
- Never claim a site "is" a good analog beyond what the scores show. Label every number with its source dataset.

---

## 6. Prior art (to position novelty; all VERIFIED via fetch, abstracts only where noted)

- Meng et al., "Deep learning selection of analogues for Mars landing sites in the Qaidam Basin" (arXiv 2501.08584, Dec 2024): CNN image similarity, single basin. Abstract only. https://arxiv.org/abs/2501.08584
- Sanganeria, NHSJS (Apr 2026): 10 Earth sites vs Moon/Mars using two grayscale image texture metrics; authors say it is not physical slope/roughness. https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- Warren-Rhodes et al., Nature Astronomy 2023: orbit-to-ground biosignature prediction in the Andes with drone + simulated HiRISE + deep learning. Abstract only. https://www.nature.com/articles/s41550-022-01882-x

Gap we fill: a global, multi-dimension, physically grounded (DEM + thermal), per-dimension explainable score tied to specific Artemis III regions, with explicit breakdown reporting.

---

## 7. Rules for the building agent

- Confirm the chosen option with Shashi before coding.
- Plain, direct writing. No em dashes in any submission text.
- Mark any claim not backed by a fetched source as UNVERIFIED in docs and UI.
- Do not hardcode planetary values from memory; compute them from downloaded data, or label them as literature values with a citation.
- Do not create accounts or enter credentials; ask Shashi to do it.
- Log every AI tool used in `docs/ai_use.md` (required for the submission form).
- Keep NASA logos out of any AI-generated media.
- If a data source fails or is too slow after ~45 minutes, drop that dimension and note it, rather than burning the clock.

---

## 8. Open questions for Shashi
1. Which option (A, B, C, D, or A+B)?
2. Team size and who else is building (front end vs pipeline split)?
3. Moon only, or Moon + Mars?
4. Demo format: 30-second video or 7 slides?

## Sources
- Challenge page: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ (Details + Resources tabs)
- 2026 event page: https://www.spaceappschallenge.org/2026/
- Submission guide: https://www.spaceappschallenge.org/resources/project-submission-guide/
- Judging guide: https://www.spaceappschallenge.org/resources/judging-awards-guide
- Artemis III 2024 regions: https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/
- Artemis III 2022 criteria: https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-moon/
- PDS Geosciences LRO: https://pds-geosciences.wustl.edu/missions/lro/
- Copernicus DEM on AWS: https://registry.opendata.aws/copernicus-dem/
- AppEEARS API: https://appeears.earthdatacloud.nasa.gov/api/
- Solar System Treks API: https://trek.nasa.gov/tiles/apidoc/
