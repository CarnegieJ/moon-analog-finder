# Moon-First Method: what NASA already tells us, where it stops, and how we improve it

Scope decision (Shashi, Nov 14): **Moon only for now.** Mars is out of scope until the Moon pipeline works.

Status labels: VERIFIED = read from the source on Nov 14, 2026. UNVERIFIED = not confirmed. Page numbers are from the documents' printed footers.

---

## 1. Short answer

Yes, NASA gives direction, but in three separate pieces that nobody has joined:

1. **What a south pole base needs** (architecture and site-selection papers). These tell us which dimensions matter and what an analog would be used to test. They give few hard numbers and say nothing about Earth sites.
2. **How NASA has scored analog fidelity before** (Human Research Program Analog Assessment Tool, 2011). A weighted "fidelity x importance" score, but filled in by expert opinion, and practical only for 10 to 12 analogs.
3. **How NASA scores physical similarity** (lunar regolith simulant Figure of Merit). A data-driven 0 to 1 per-property score comparing distributions, but never combined across properties and never applied to terrain or sites.

**Our improvement:** take the structure of (2), replace its expert opinions with the data-driven scoring of (3), and set its importance weights from the needs in (1). The result is a data-driven, use-case-specific Analog Figure of Merit that can rank the whole Earth, not just 12 expert-picked sites.

---

## 2. What NASA says the base needs (the "requirements" layer)

| Need | What NASA says | Source | Status |
|---|---|---|---|
| Lighting for first landings | Site should be sunlit for about 6 to 6.5 days; no south pole location is continuously sunlit; higher terrain gets longer sunlight | Lunar Site Selection white paper, 2023 Architecture Concept Review, p.2 to 3 | VERIFIED |
| Terrain for landing | Relatively flat, only small blocks and craters within lander hazard tolerance (no numeric slope limit given) | same, p.2 | VERIFIED |
| Earth visibility | Direct-to-Earth comms need Earth in view; sites toward the far side may see Earth only from high terrain | same, p.3 | VERIFIED |
| Seasons | About 11 lunar seasonal cycles per 10 Earth years | same, p.4 | VERIFIED |
| Traverse slopes | Traverses could meet slopes up to 20 deg; slopes over 10 deg are common at the south pole | Lunar Mobility Drivers and Needs, 2024 ACR, p.4 to 6 | VERIFIED |
| Traverse distances | 5 m to 5,000 m; lander ejecta keep-out over 1,000 m | same, p.3, p.7 | VERIFIED |
| Habitat placement | Minimize darkness, which favors ridges and high ground | same, p.4 to 5 | VERIFIED |
| Dust and wheels | Wheel wear and dust accumulation need mitigation | same, p.6 | VERIFIED |
| Darkness survival | Power systems must survive 120+ hours of darkness | Moon Base User's Guide, NASA, Apr 2026, p.10 | VERIFIED |
| PSR access | Mobility must descend and climb extreme crater slopes to reach permanently shadowed volatiles; gaps FN-M-302 (sunlit mobility) and FN-M-304 (PSR mobility) | same, p.7, p.10 | VERIFIED |
| Rover speed | Large rovers at 10 km/hr | same, p.10 | VERIFIED |
| Knowledge gaps NASA lists | DN-002 high-fidelity elevation maps of south pole zones; DN-007 shallow water ice distribution for ISRU; DN-008 geotechnical properties of highland regolith; DN-017 plume-surface interaction particle speeds | 2025 Architecture Update, p.10 | VERIFIED |
| Construction gaps | #0504 autonomous surface construction; #0505 in-situ construction | same, p.14 | VERIFIED |

**What these give us:** a fixed list of things a base team must test on Earth before flying. That list becomes our **use cases**.
**What they do not give us:** any thresholds for temperature or PSR distance, and no link to Earth sites.

---

## 3. How NASA has scored analogs before (the "method" layer)

### 3a. HRP Analog Assessment Tool (NASA/TP-2011-216146, Keeton et al., May 2011). VERIFIED (partly via summary of a truncated read)
- Score for analog i: **w_i = sum over j of (a_ij x r_j)**
  - r_j = how important characteristic j is (criticality), from expert pairwise comparisons using the Analytic Hierarchy Process (AHP).
  - a_ij = how well analog i matches the space scenario on characteristic j (fidelity), also from expert pairwise comparisons.
- Separate scores for research fidelity and practical utility (cost, access, feasibility), then averaged.
- Built for human behavior risks (isolation, team, sleep), not terrain.
- **Limits the report itself notes:** results are only as good as the experts; rankings came out in tiers with non-significant differences; results shifted between iterations; about 10 to 12 analogs is the practical maximum.

### 3b. Lunar simulant Figure of Merit (Schrader et al., AIAA 2009). VERIFIED (full text read)
- Each property gets a **FoM between 0 and 1**: 1 minus the normalized difference between the reference distribution and the candidate distribution (used for particle composition and particle size distribution).
- **No combining or weighting across properties.**
- Paper's own caution: a low FoM does not rule a simulant out; it may still be fit for some uses.

### 3c. Frameworks we could not read (note for the record)
- Lee and Pascal, 2008, systematic terrestrial analogs for lunar science and exploration (CMU PDF blocked).
- Stern et al. 2025, JGR Planets, framework for assessing analog field sites for ocean worlds (page failed).
Both are worth citing as related work if a teammate can open them; do not describe their content until read.

---

## 4. Gaps in what exists, and our improvements

| Gap | Our improvement |
|---|---|
| AHP fidelity scores come from expert opinion and stop at ~12 analogs | Compute fidelity a_ij from NASA data with a Schrader-style FoM, so every Earth cell can be scored |
| FoM is per property, never combined, never tied to a purpose | Combine FoMs with importance weights r_j that come from a named NASA use case |
| One score per analog hides why | Report per-dimension FoM, per-use-case score, and a fixed "cannot match" row |
| Architecture papers list needs but never map them to Earth | Each use case is labeled with the NASA gap ID it supports (FN-M-302, FN-M-304, DN-007, DN-008, DN-017) |
| Prior Earth-to-Moon comparisons use image texture (NHSJS 2026) or CNN look-alikes (Meng et al. 2024) | Physical features at matched scales; image similarity is not used for scoring |
| Experts cannot easily say how sure a ranking is | Bootstrap the FoM inside each site window and show a confidence band; flag ties instead of forcing a rank |
| A low score can wrongly read as "useless" (Schrader's caution) | Scores are per use case: a site can be poor for lighting but strong for traverse testing |

---

## 5. The method: Analog Figure of Merit (AFoM), Moon version

### 5.1 Dimensions and their FoM

Each FoM is 0 to 1. Distribution FoMs follow Schrader: 1 minus normalized difference of distributions.

| Dimension | Lunar reference | Earth candidate | FoM rule |
|---|---|---|---|
| D1 Slope distribution | PGDA 5 m site DEMs resampled to 30 m (products 78, 81) | Copernicus GLO-30 | 1 minus normalized Wasserstein distance of slope histograms (normalizer = distance from target to flat ground) |
| D2 Roughness / ruggedness | same | same | same rule on roughness or terrain ruggedness index histograms (xDEM) |
| D3 Steep-slope access | share of window with slopes 10 to 20 deg and over 20 deg (NASA mobility thresholds) | same | 1 minus absolute difference of the two shares, averaged |
| D4 Low sun / long shadows | PGDA product 69 average illumination (AVGVISIB) | computed from latitude: share of the year with sun below 5 deg, and maximum sun elevation | 1 minus normalized difference |
| D5 Long darkness | NASA darkness-survival target (120+ hours) plus local illumination | computed from latitude: longest continuous night in hours | FoM = 1 if Earth darkness covers the lunar target duration, scaled down below it |
| D6 Cold extremes | Diviner PRP temp_max, temp_avg | MODIS MOD11C3 annual max day / min night LST | 1 minus normalized difference, with a stated physical range. Expect low scores; Earth cannot reach lunar cold-trap temperatures. Show it honestly |
| D7 Frozen ground / ice in soil | Diviner PRP ice_depth (shallow stable ice present) | Earth permafrost product (UNVERIFIED, pick in build) | presence-based FoM. Deferred if Earth data not found in time |
| D8 Bare surface | Moon fully bare | MODIS vegetation index | FoM = 1 minus vegetation fraction |
| Never matchable | gravity, vacuum, radiation | n/a | always 0, always shown |

Notes:
- D4 and D5 on the Earth side are pure astronomy (no download), so they are fast and exact. Document the formulas.
- D6 compares surface temperature (MODIS skin) with Diviner surface max and 2 cm average. Note the depth mismatch in the UI.

### 5.2 Use cases (from Section 2) and importance weights

Default weights r_j per use case, written down with the NASA statement that justifies each. Weights sum to 1.

| Use case | Supports NASA gap | Main dimensions (weight) |
|---|---|---|
| U1 Sunlit traverse and rover mobility testing | FN-M-302 | D1 slope 0.30, D2 roughness 0.25, D3 steep access 0.25, D8 bare 0.20 |
| U2 Shadow navigation and PSR access testing | FN-M-304 | D3 steep access 0.30, D4 low sun 0.30, D1 slope 0.20, D6 cold 0.20 |
| U3 Power and darkness survival testing | Moon Base power target (120+ h dark) | D5 darkness 0.40, D4 low sun 0.30, D6 cold 0.30 |
| U4 Ice prospecting and ISRU rehearsal | DN-007 | D7 frozen ground 0.40, D6 cold 0.30, D8 bare 0.15, D2 roughness 0.15 |
| U5 Landing, plume, and site preparation testing | DN-017, #0504 | D1 slope 0.35, D2 roughness 0.35, D8 bare 0.30 |

These numbers are a starting proposal, not NASA values. Label them "team-set, justified by NASA needs".

**Weighting options (Shashi picks):**
- **W1 Fixed weights from the table above** with a written reason per weight. Simple, transparent.
- **W2 W1 as default plus UI sliders.** Users explore trade-offs; the default stays defensible.
- **W3 AHP-lite:** the team does quick pairwise comparisons per use case (same math as the 2011 NASA tool, applied only to weights). Most rigorous, adds 1 to 2 hours.

### 5.3 Score

For Earth site i, lunar target t, use case u:

  AFoM(i, t, u) = sum over j of FoM_j(i, t) x r_j(u)

Reported together with: every FoM_j, a bootstrap confidence band, and the never-matchable row.

### 5.4 Validation (Validity score)
- Positive controls (known analogs, e.g. Haughton Crater, McMurdo Dry Valleys, Svalbard, Meteor Crater, Black Point Lava Flow) should beat negative controls (rainforest, farmland) on U1 and U5.
- High-latitude sites should win U3 and U4; desert sites should not. If the opposite happens, a feature is broken.
- Sensitivity: change each weight by plus or minus 0.1 and report whether the top 5 changes. Stable rankings are a stronger claim.

---

## 6. Moon-only starter run (replaces S1/S2 choice)

- Targets: Haworth, Malapert Massif (PGDA Site23), de Gerlache rim (PGDA Site11, approximate match to Artemis III "de Gerlache Rim 2").
- Earth sites: the 12 from STARTER_SET.md.
- Dimensions in the first run: D1, D2, D3, D4, D5, D6, D8. D7 only if an Earth frozen-ground product loads within 45 minutes.
- Use cases: all five scored, U1 to U3 shown first.
- Output: table of AFoM per site x target x use case, plus per-dimension FoMs and the control check.

---

## 7. The pitch, in one line

"NASA has a way to score analog fidelity (expert-driven) and a way to score physical similarity (data-driven), and its Moon base papers list what must be tested. We joined them into one data-driven Analog Figure of Merit that ranks any place on Earth for a specific Artemis base test, shows why, and shows where the analogy breaks."

---

## Sources (VERIFIED unless noted)
- Lunar Site Selection, 2023 ACR white paper: https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf
- Lunar Mobility Drivers and Needs, 2024 ACR white paper: https://www.nasa.gov/wp-content/uploads/2024/06/acr24-lunar-mobility-drivers-and-needs.pdf
- Moon Base User's Guide, Apr 2026: https://nasa.gov/wp-content/uploads/2026/04/moon-base-architecture-users-guide.pdf
- 2025 Architecture Update: https://www.nasa.gov/wp-content/uploads/2025/12/2025-architecture-update-for-publication.pdf
- NASA/TP-2011-216146 Analog Assessment Tool Report: https://nasa.gov/sites/default/files/atoms/files/analog_assessment_tools.pdf
- Schrader et al., simulant Figure of Merit (AIAA 2009): https://ares.jsc.nasa.gov/projects/simulants/attachments/conf_papr_AIAA_2009_Schrader%20-%20Lunar%20Regolith%20Characterization%20for%20Simulant%20Design%20and%20Evaluation%20Using%20Figure%20of%20Merit%20Algorithms.pdf
- Lunar Regolith Simulant User's Guide (NASA/TM-2010-216446), abstract: https://ntrs.nasa.gov/citations/20100038451
- Artemis III regions (Oct 2024): https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/
- Not read (blocked): Lee and Pascal 2008 (CMU); Stern et al. 2025 JGR Planets https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JE008803
