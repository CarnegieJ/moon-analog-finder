# PLAN v2 (replaces the build plans in HANDOFF.md, METHOD_TASKS.md, STARTER_SET.md)

Written Sat Nov 14, 2026, 12:15 PM ET. Deadline: Sun Nov 15, 11:59 PM local event time. About 35 hours left, zero code written.
This is the single file to build from. The older files stay as reference only:
- HANDOFF.md: problem statement, judging rules, submission rules (still valid).
- METHOD_REASONING.md: NASA sources behind the scoring method (still valid).
- METHOD_TASKS.md and STARTER_SET.md: superseded by this file.

Labels: VERIFIED = read from the source today. UNVERIFIED = confirm before relying on it.

---

## 1. Where we stand

Done:
- Problem, judging criteria, and submission rules understood and sourced.
- Scope set: **Moon only.**
- Method chosen: **Analog Figure of Merit (AFoM)** = data-driven per-dimension similarity (0 to 1, after NASA's simulant Figure of Merit) x importance weights per test purpose (structure of NASA's 2011 Analog Assessment Tool), with weights justified by NASA Moon base needs.
- Data sources located and verified.

Not done: any code, any downloaded data, any result.

Main risk: we have planned more than 35 hours can hold. The fix is below.

---

## 2. What is cut, and why

| Cut | Why |
|---|---|
| All Mars work | Scope decision. No Mars thermal data found anyway. |
| Method bake-off (4 methods compared) | Method is already chosen and sourced. We keep only its validation check. |
| Image/CNN similarity | Prior art already does it; the challenge says to go beyond looks. |
| SAR / radar roughness | Different radar bands on Earth and Moon; qualitative only; costs hours. |
| Team pairwise weighting (AHP) | 1 to 2 hours for little judging value. Use fixed weights with written reasons plus sliders. |
| Per-site 5 m lunar DEMs (several GB, one site each) | Replaced by one 80 m file covering the whole south pole (see Section 3). |
| Resampling lunar data to 30 m | Not needed: lunar 80 m and Earth 90 m are already close. Compare at ~90 m. |
| Full global search at 30 m | Replaced by a coarse-to-fine funnel over bare land at 90 m. |
| Earth frozen-ground dimension (D7) | No verified Earth product yet. Moon ice shown as context only. Add only if time remains. |
| 5 test purposes | Reduced to 3 (rover mobility, shadow and PSR access, power and darkness survival). |
| All 9 Artemis regions at start | Start with 3. The single 80 m file makes the other 6 cheap once we have cited coordinates. |

---

## 3. New resources found today that make this faster

| Resource | What it gives | Status |
|---|---|---|
| **PGDA product 90**, "A New View of the Lunar South Pole from LOLA" (Barker et al. 2023, doi 10.3847/PSJ/acf3e1): https://pgda.gsfc.nasa.gov/products/90 | Cloud-optimized GeoTIFFs for 80 to 90 S at 80 m/px: `LDEM_80S_80MPP_ADJ.TIF` (181 MB, elevation) and `LDSM_80S_80MPP_ADJ.TIF` (231 MB, slope), base URL `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/`. Also `LPSR_80S_20MPP_ADJ.TIF` (148 MB, permanent shadow). One download covers every Artemis III region. | VERIFIED |
| PGDA product 69, polar illumination: https://pgda.gsfc.nasa.gov/products/69 | `AVGVISIB_75S_120M_201608.TIF` average sunlight; Earth-visibility variants | VERIFIED |
| Copernicus DEM GLO-90 | AWS `s3://copernicus-dem-90m/` anonymous (VERIFIED). Also on Microsoft Planetary Computer STAC as `cop-dem-glo-90` COGs (collection VERIFIED; whether access needs token signing UNVERIFIED) | see left |
| MODIS land surface temperature | MOD11C3 monthly 0.05 deg via Earthdata Login (VERIFIED). Planetary Computer `modis-11A2-061` 8-day 1 km COGs (collection VERIFIED; access signing UNVERIFIED) | see left |
| xDEM (Apache-2.0): https://pypi.org/project/xdem/ | Slope, roughness, ruggedness index from any DEM | VERIFIED |
| solshade (`pip install solshade`): https://solshade.readthedocs.io | Terrain-aware sunlight and horizon modeling from a DEM; could model Earth shadows in Phase 4. License not stated on docs, check repo before use | VERIFIED docs, license UNVERIFIED |
| LunarSite (MIT, per its author's article): https://github.com/AlanSEncinas/LunarSite | Open ML pipeline for south pole landing site scoring using the same PGDA 69 and 90 data. Useful as code reference and prior art. The article cites NASA "CASSA" thresholds: slope <= 5 deg, illumination >= 33%, Earth visibility >= 50% | Article VERIFIED; repo not opened; thresholds are secondhand, find the NASA source before citing |
| ESA Catalogue of Planetary Analogues PDF; Wikipedia analog site table | Seed list of known analogs and the "already known" filter | VERIFIED (PDF not opened) |

---

## 4. The product (unchanged idea, smaller build)

**Core:** Takes an Artemis III region and a test purpose, outputs a ranked map of Earth sites with per-dimension scores, a confidence note, and a "where it breaks" panel, helping teams pick under-used Earth test sites for Moon base work.

Dimensions in the build:
- D1 slope distribution, D2 roughness, D3 share of steep ground (10 to 20 deg, over 20 deg; NASA mobility figures)
- D4 low sun, D5 longest darkness (Earth side from latitude math; Moon side from PGDA 69)
- D6 temperature extremes (Diviner vs MODIS), honest low scores expected
- D8 bare surface (vegetation)
- Always shown as 0: gravity, vacuum, radiation

Test purposes: U1 rover mobility, U2 shadow and PSR access, U3 power and darkness survival. Default weights are team-set with a written NASA-based reason each; sliders in the app.

---

## 5. Phases (ET). Each phase ends with a gate; if the gate fails, fix before moving on.

### Phase 0: Setup. Sat 12:30 to 1:30 PM
- Repo, Python env (rasterio, xdem, numpy, pandas, scipy, geopandas, earthaccess), folder layout.
- `sites.csv`: 3 lunar targets (Haworth, Malapert Massif, de Gerlache Rim 2) and 12 Earth sites (6 known analogs, Black Point Lava Flow, 3 negative controls, 2 lesser-known), each with a coordinate source column.
- **Gate:** one remote GeoTIFF window read works.

### Phase 1: Moon reference profiles. Sat 1:30 to 3:30 PM
- Download LDEM/LDSM 80S 80 m, AVGVISIB, LPSR.
- For each target, 10 km window: slope histogram, roughness, steep-ground shares, average sunlight, PSR share.
- **Gate:** a table of lunar numbers per target, sanity-checked against NASA's statement that slopes over 10 deg are common at the south pole.

### Phase 2: Earth v0 and scoring. Sat 3:30 to 7:00 PM
- Copernicus GLO-90 windows for the 12 Earth sites; same terrain features.
- Scoring code: D1, D2, D3, D8 and the AFoM for U1.
- **Gate (the key one):** known analogs outrank negative controls. If not, the features are wrong; stop and fix.

### Phase 3: Light and temperature. Sat 7:00 to 10:00 PM
- D4, D5 from solar geometry. D6 from Diviner Polar Resource Products (`temp_max`, `temp_avg`) and MODIS.
- U2 and U3 scores. Bootstrap confidence and weight-sensitivity check.
- **Gate:** high-latitude sites win U3; deserts do not.
- If Diviner or MODIS takes more than 60 minutes, ship D6 for the Moon side only and say so.

### Phase 4: Discovery search. Sat 10 PM to Sun 10 AM (long jobs run overnight)
- Coarse filter: bare land only (vegetation mask), then sample candidate windows across bare regions worldwide at 90 m.
- Score all candidates, remove known analog sites, keep top candidates per target and purpose.
- Hand-check the top 5 in NASA Worldview and write 3 short site write-ups with numbers.
- **Gate:** at least 3 defensible "new candidate" sites. Fallback if the global run fails: 30 to 50 hand-picked bare regions.

### Phase 5: Web app. Sun 8 AM to 4 PM (can start Saturday on Phase 2 output if a second person is available)
- Static React + MapLibre site: target picker, purpose picker, weight sliders, ranked list (new vs known), per-site score card, "where it breaks" panel, data source list.
- Loads precomputed JSON only. Deployed to a public URL.
- **Gate:** works on a fresh browser with no login.

### Phase 6: Submission. Sun 4 to 8 PM, buffer to 11:59 PM
- 30-second video or 7 slides, README, methods page, NASA data list, references, AI-use disclosure.
- Submit by 8 PM.

---

## 6. Constraint found today

The cloud workspace used for planning **cannot reach NASA data hosts** (pgda.gsfc.nasa.gov, pds-geosciences, AWS S3, Planetary Computer all blocked; only package registries work). The data pipeline must run on Shashi's computer or another machine with open internet.

## 6a. Decisions (Shashi, Sat Nov 14)
- Build runs on Shashi's computer, linked to the Claude session.
- Solo build. Phases run in sequence; web app starts Sunday morning on real Phase 2 to 4 output.
- Earthdata Login: Shashi creates it. Temperature (D6) stays in.
- Demo: 30-second video with English subtitles. Reserve Sun 4 to 6 PM for recording and editing; keep the script to 4 shots (problem, map, score card, "where it breaks").
- Solo scope guard: if Phase 4 is not passing its gate by Sun 10 AM, use the fallback list of 30 to 50 hand-picked bare regions and move on to the app.

## 7. Needed from Shashi
1. A machine to run the pipeline (about 5 GB free disk, Python 3.10+).
2. Free NASA Earthdata Login (for MODIS temperature).
3. A public GitHub repo and a hosting choice (GitHub Pages or Vercel).
4. Team size and who takes front end vs pipeline.
5. Demo format: video or slides.

## Sources added in this file
- PGDA product 90: https://pgda.gsfc.nasa.gov/products/90
- PGDA product 69: https://pgda.gsfc.nasa.gov/products/69
- Planetary Computer GLO-90: https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-90
- Planetary Computer MODIS LST: https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-11A2-061
- solshade: https://solshade.readthedocs.io/en/latest/
- LunarSite article: https://dev.to/alan_scottencinas/lunarsite-an-end-to-end-ml-pipeline-for-lunar-south-pole-landing-site-selection-2lda
- xDEM: https://pypi.org/project/xdem/
