# Benchmark

Re-run with `python3 pipeline/benchmark.py` after every method change. Results land in `data/out/benchmark.json`.

## Baseline (Sat Nov 14, library of 167,471 Earth windows)

| # | Measure | What it asks | Baseline | Target |
|---|---|---|---|---|
| 1 | Coverage | How many of the 10 known analog sites are in the library at all? | 7 of 10 | 10 of 10 |
| 2 | Recovery | Of the known sites in the library, how many reach the top 1% of all windows for at least one lunar spot and purpose (300 random lunar spots x 3 purposes)? | 6 of 7 | keep at or above 6 of 7, report honestly |
| 3 | Rejection | Do forest and farmland controls score zero? Any vegetated windows in the library? | max control score 0.00; 0 vegetated windows | unchanged |
| 4 | Stability | Share of the top 10 regions that stay in the top 10 when any one weight moves by 10 points | mean 92%, worst case 50% | worst case 80% or better, or ties shown as ties |

### Details
- Coverage, missing: Teide and Craters of the Moon (vegetation index 0.26 and 0.27, just over the 0.20 cut-off) and McMurdo Dry Valleys (Antarctica has no vegetation data, so it never entered the bare-land mask).
- Recovery, best rank reached: Haughton Crater top 0.01% (darkness survival), Atacama top 0.01% (rover driving), Mauna Kea top 0.01% (rover driving), Askja and Black Point Lava Flow top 0.03% (rover driving), Svalbard top 0.04% (shadow work). Meteor Crater only reaches the top 15%.
- Recovery is a generous test: it takes each site's best result over 900 tries. It shows the method can find known sites, not that it always ranks them first.
- Meteor Crater fails because the crater is about 1.2 km wide and our window is 10 km: the window is mostly flat plateau. This is a scale limit of the method.
- Stability worst case (50%) is darkness survival on all three targets. Many Arctic sites tie, because darkness is capped at 120 hours and they all exceed it, so a small weight change reshuffles equal sites.
- Rejection passes partly by construction: vegetated land is filtered out before scoring.

## Version 2 (Sat Nov 14, late evening, library of 236,193 Earth windows)

Changes: multi-scale roughness (slope at 320 m and Hurst exponent) replaced the single-scale roughness factor; "slope classes" removed from the rover-driving weights because it duplicated slope match; vegetation cut-off loosened from 0.20 to 0.30; four ice-free Antarctic areas and the Teide square added by hand.

| # | Measure | Baseline | Version 2 |
|---|---|---|---|
| 1 | Coverage: known analog sites in the library | 7 of 10 | 10 of 10 |
| 2 | Recovery: known sites reaching the top 1% for some lunar spot and purpose | 6 of 7 | 8 of 10 |
| 3 | Rejection: forest and farmland controls, rover driving | 0.00 | 0.00 |
| 4 | Stability: top 10 kept when one weight moves 10 points | mean 92%, worst 50% | mean 91%, worst 60% |
| 5 | Independence: highest correlation between weighted terrain factors | 0.98 to 0.99 | 0.05 to 0.13 |
| 6 | Combination rule: top-100 agreement, weighted sum vs geometric mean | not measured | 91 to 99 |

Notes:
- Lunar check: the median Hurst exponent over our 11,221 lunar spots is 0.93; Rosenburg et al. (2011) report a median of 0.95 for the lunar highlands (different distance range and window size).
- Not in the top 1%: Meteor Crater (top 3.5%) and Craters of the Moon (top 8%). Both are small features inside flat surroundings; the 10 km window limit.
- Strong matches (0.8 or higher) for rover driving at Malapert Massif fell from 2,624 windows to 24 in the app: matching steepness alone is easy, matching steepness and terrain character is rare.
- A terrain tie-breaker inside the darkness score was tried and reverted (worst-case stability fell to 10%).
- Not done: overlapping Earth windows (would make the library about four times larger, too heavy for in-browser scoring). Stated as a limit.

## Version 3 validation: known sites against random land (Sat Nov 14, night)

The earlier "recovery" test is retired. It took each site's best result over 900 tries, and random windows pass it too (12% of random single windows reach the top 1% the same way).

New test (`pipeline/benchmark_auc.py`): for 80 landing-like lunar spots (within 6 degrees of the pole, under 15% permanent shadow, sunlit over 25% of the time), compare the best Earth window within 30 km of each known analog site against the best window within 30 km of 400 random bare-land points more than 300 km from any known site. The result is the chance that a known site beats a random area: 0.5 is no better than chance, 1.0 is always better. Near-flat Earth windows (median slope under 1 degree, 54% of the library) are excluded because radar noise is comparable to their relief.

Known sites (`pipeline/known_sites.csv`): 21. Fifteen come from the ESA Catalogue of Planetary Analogues (Preston, Grady and Barber, 2012, written for ESA), using only chapters that its directory lists for the Moon and that give a point coordinate; chapter and page are recorded for each. Six more come from Wikipedia pages that state both coordinates and an analog or astronaut-training use; these are marked "verified-secondary". Entries removed, with reasons, are in `pipeline/known_sites_excluded.csv`.

Of the 21, 15 are in the library. Not in the library (vegetated, farmland or small islands): Lonar, Mistastin, Etna, Ries, Sudbury, Piton de la Fournaise.

| Terrain score used | Best window per area | One random window per area |
|---|---|---|
| Slope match + roughness across scales (shipped) | 0.61 | 0.65 |
| Slope match only | 0.41 | 0.50 |
| Roughness across scales only | 0.65 | 0.71 |

Reading:
- On the primary-source list the shipped terrain score is only weakly better than chance (0.61 to 0.65; range 0.40 to 0.70 across the 80 lunar spots). This is at or below the 0.65 threshold we set in advance, so the tool is described as a terrain screen and the word "validated" is not used.
- Earlier, smaller lists gave 0.71 (14 sites, three with unsourced coordinates) and 0.67 (11 sites). The number fell as better-sourced sites were added.
- The result splits cleanly by the size of the feature. Sites that are analogs because of their broad landscape beat most random areas: Atacama (0.90), CHILL-ICE lava field (0.86), Askja (0.85), Antarctic Dry Valleys (0.83), Axel Heiberg Island (0.79), Haughton (0.79), Mauna Kea (0.74), Kilauea (0.71), Tenerife (0.66).
- Sites that are analogs because of a small feature or a rock type do worse than random areas: Black Point Lava Flow (0.46), Kilbourne Hole (0.43), Meteor Crater (0.38), Sunset Crater (0.33), Cinder Lake (0.33), Craters of the Moon (0.13). The ESA catalogue lists these for craters, regolith and basalt. A 10 km terrain window measures none of those.
- Slope match alone is no better than chance. The separating power comes from roughness across scales. We did not re-weight toward it: 15 sites is too few to tune on, and slope match answers a different question that a rover test still needs.
- Cinder Lake, Sunset Crater and Black Point are within about 40 km of each other, so they are not three independent tests.
- What this says about the method: it screens for landscape-scale terrain similarity. It cannot yet recognise crater-scale features or rock type, which is what many established lunar analog sites are valued for.

## Stage 2 test: 2 km windows at 30 m (Sun Nov 15, early morning)

Question, fixed before the data arrived: do known analog sites beat random bare-land areas more often at 2 km than at 10 km, and do the small sites that scored worse than random move above 0.5?

Data: Copernicus DEM GLO-30 for 371 Earth areas (21 known sites, 150 random bare-land areas, 200 shortlisted stage 1 windows), 34,075 windows of 2 km; LOLA 20 m lunar elevation resampled to 30 m; 120 lunar 2 km windows taken inside landing-like spots. Same measurement code as stage 1. Scripts: `pipeline/modal_zoom.py`, `pipeline/zoom_benchmark.py`.

| Terrain score used | 10 km windows (stage 1) | 2 km windows (stage 2) |
|---|---|---|
| Slope match + roughness across scales | 0.61 to 0.65 | 0.56 to 0.57 |
| Slope match only | 0.41 to 0.50 | 0.43 to 0.47 |
| Roughness across scales only | 0.65 to 0.71 | 0.52 to 0.58 |

Answer: no. The finer stage is slightly worse overall, so it is not added to the tool.

Per site (share of random areas beaten, 10 km then 2 km): Black Point Lava Flow 0.46 to 0.71 and Kilbourne Hole 0.43 to 0.53 improved. Meteor Crater 0.38 to 0.19, Cinder Lake 0.33 to 0.23, Sunset Crater 0.33 to 0.34 and Craters of the Moon 0.13 to 0.16 did not. The landscape-scale sites stayed high (Antarctic Dry Valleys 0.90, Askja 0.87, Atacama 0.82, Axel Heiberg 0.78, Haughton 0.76).

Reading:
- Window size was not the main reason the small sites were missed. Those sites are analogs for a specific feature (a crater, a cinder field) or a rock type, and general terrain statistics do not capture that at either scale.
- The lunar reference here is ordinary landing-like terrain, not individual craters. A fairer test for crater analogs would compare against lunar windows centred on craters of similar size; that needs a lunar crater catalogue and is not done.
- The two stages used different random samples (400 and 150 areas), so the comparison is approximate. Etna had only 6 usable windows.
- Sensor differences at 30 m (radar on Earth, interpolated laser tracks on the Moon) are not quantified.

## Improvement plan (ranked by benchmark gain per hour)

| Priority | Change | Fixes | Est. time | Status |
|---|---|---|---|---|
| 1 | Loosen the bare-ground cut-off (vegetation index up to 0.30, score already graded) and rescan on Modal; add ice-free Antarctic squares by hand | Coverage 7 to 10 | 1 to 1.5 h | todo |
| 2 | Show tied sites as ties in the app; rank ties by a stated secondary factor | Stability worst case | 0.5 h | todo |
| 3 | Cited coordinates for Artemis III regions; literature check on top new candidates (East Greenland, Peary Land, Taymyr) | Validity of claims | 1 h | todo |
| 4 | Faster scoring in the browser | Usability | 0.5 h | todo |
| 5 | Similar lunar spots (Moon to Moon), shareable brief | Reuse of earlier analyses | 1 to 2 h | optional |
| 6 | Plain-language site briefs from a Meta model | Readability | 1 h | optional |
| - | Smaller windows for crater-scale analogs (Meteor Crater case) | Scale limit | 3+ h | not planned; stated as a limit |

## Must-do for submission (Sunday)
1. Public GitHub repo and hosted app (public link, no login).
2. 30-second video with English subtitles.
3. Submission form text: summary, description, NASA data used, other data, references, AI use.
