# Method audit (Sat Nov 14, evening)

Purpose: find weaknesses in our own process and compare it with published methods for similar problems.
Labels: VERIFIED = read from the source or measured on our data today. UNVERIFIED = not confirmed.

## A. Weaknesses found in our process

| # | Finding | Evidence | Severity | Fix |
|---|---|---|---|---|
| 1 | The three terrain factors are near-duplicates. Slope match, slope classes and roughness move together, so "three factors" is really one. | Measured: correlations of 0.98 to 0.99 across the library for Malapert and de Gerlache (0.94 slope vs roughness for Haworth). VERIFIED | High | Replace roughness with a measure of how roughness changes with scale (second baseline, scaling exponent). |
| 2 | Terrain is measured at one scale (80 m). Published lunar roughness work uses several scales, because the Moon's surface changes character near 1 km. | Rosenburg et al. 2011; NASA PGDA product 70; Lemelin et al. 2018. VERIFIED | High | Same fix as 1. |
| 3 | "Coldest night" is mislabelled. The MODIS product is a monthly average, so our number is the coldest month's average night temperature, for 2024 only. | Product definition (MOD11C3, monthly). VERIFIED | Medium | Relabel now. Multi-year average later. |
| 4 | The cold factor does not discriminate for shadowed targets. For the Haworth floor it is 0.00 for almost every Earth window. | Measured: 1st to 99th percentile both 0.00. VERIFIED | Medium | Keep, but say plainly that Earth cannot match it. Consider scoring cold relative to Earth's own range, clearly labelled. |
| 5 | Darkness saturates. About 2% of windows (roughly 3,500) all score exactly 1.0 on darkness, so their order is arbitrary. | Measured: 2.1% of windows at the cap. VERIFIED | Medium | Show ties as ties; break ties with terrain match to the lunar spot. |
| 6 | Earth windows sit on a fixed, non-overlapping grid. A good match that straddles two windows is missed. | Scan design. VERIFIED | Medium | Half-step overlapping windows on the next scan. |
| 7 | The two elevation datasets are different kinds of measurement: laser altimetry on the Moon, radar on Earth, and Earth data is resampled from 90 m to 80 m. Any resulting bias in slopes is not quantified. | Dataset documentation. Bias itself UNVERIFIED | Medium | State as a limit. Check Earth slopes at native versus resampled grid if time allows. |
| 8 | Low sun on Earth is computed from latitude and ignores terrain shadowing. | Method. VERIFIED | Medium | Future work (terrain-aware illumination). |
| 9 | Results depend on how factors are combined. Switching from a weighted sum to "weakest factor decides" changes 24 to 39 of the top 100 sites. | Measured: top-100 overlap of 61, 63 and 76 for the three targets. Geometric mean agrees well (95 to 98). VERIFIED | Medium | Add this to the benchmark; report it. |
| 10 | Validation set is small: 10 known sites with approximate coordinates, and the recovery test takes the best of 900 tries. | docs/BENCHMARK.md. VERIFIED | High | State openly. Add more known sites from the ESA catalogue if time allows. |
| 11 | The bare-ground and snow filters are simple thresholds on 5.6 km cells and are not validated against a land-cover map. Three known analog sites are excluded by them. | Benchmark coverage 7 of 10. VERIFIED | High | Coverage fix (planned). |
| 12 | Histogram overlap depends on the 1-degree bin width. | Method. VERIFIED | Low | Acceptable; a distribution distance without bins is the alternative. |
| 13 | Showing one site per 2-degree square is an arbitrary display rule. | Method. VERIFIED | Low | Keep; state it. |

## B. Published methods for similar problems

| Method | What it does | Compared with ours | Status |
|---|---|---|---|
| Multi-scale lunar roughness (Rosenburg et al. 2011; NASA PGDA product 70, "Lunar slopes and Hurst exponent") | Median slope at 57 m, 225 m and 560 m baselines, plus the Hurst exponent (how roughness grows with scale, fitted from 57 m to 2.7 km). Uses medians because slope distributions have heavy tails. Reports a median Hurst exponent of 0.95 in the lunar highlands and 0.76 in the maria. | We use one baseline. This is the accepted lunar standard and a NASA data product we can check ourselves against. | VERIFIED |
| Wavelet roughness regimes (Lemelin et al. 2018) | Finds scale breaks in lunar roughness, the smallest near 659 m. | Supports using more than one scale. | VERIFIED (abstract) |
| Multi-criteria decision making for Artemis III sites (arXiv 2406.19863) | Ranks 1,247 candidate landing points with TOPSIS on six criteria (visibility, illumination, permanent shadow, geology, mineral signature). Tests robustness by changing weights and by comparing four ranking methods. No ground truth. | Same family as our weighted score. Their scores are normalised against the candidate pool; ours are absolute (0 to 1 against the lunar spot), which makes ours comparable across runs. Their cross-method robustness test is one we lack. | VERIFIED (most of paper) |
| Image similarity (Sanganeria 2026; Meng et al. 2024) | Texture statistics or CNN similarity on images. | Looks-based; the challenge asks to go beyond this. | VERIFIED earlier |
| Satellite foundation-model embeddings (Prithvi, arXiv 2403.02059) | Similar-image search on Earth imagery. | Not shown to work for Moon-to-Earth matching; validated with class labels we do not have. | Abstract only |
| Climate analog methods (Mahony et al. 2017, "sigma dissimilarity") | Believed to measure analog distance in units of natural variability, using a Mahalanobis distance. | Could replace our hand-set ranges and handle correlated factors properly. | UNVERIFIED (page could not be read) |
| Expert weighting (NASA Analog Assessment Tool 2011) | Fidelity times importance, from expert pairwise comparisons. | We took the structure and replaced expert fidelity with data. Our weights are still team-set. | VERIFIED earlier |

Could not be read: Stern et al. 2025 (analog field site framework for ocean worlds), Lee and Pascal 2008 (systematic lunar analogs), and a 2025 lunar base site selection paper in Geo-spatial Information Science.

## C. What to change, ranked

1. **Multi-scale roughness on both bodies**, replacing the duplicate roughness factor: slope at a second baseline (about 320 m) and a scaling exponent. Check our lunar values against NASA's published Hurst exponents. Fixes findings 1 and 2. Needs an Earth rescan, so combine with the coverage fix and overlapping windows (findings 6 and 11) in one Modal run.
2. **Add two robustness checks to the benchmark**: agreement across combination rules (finding 9) and factor independence (finding 1).
3. **Relabel temperature** and state the cold limit plainly (findings 3 and 4).
4. **Ties** shown as ties, broken by terrain match (finding 5).
5. Future work, stated in the submission: terrain-aware illumination, land-cover and mineral data, sensor bias check, variability-scaled distances, expert weights.

## D. Sensor check on the scaling number (Sat Nov 14, late)

Question: Earth's Hurst exponent is about 0.2 lower than the Moon's at matched slope. Is that real terrain or a difference between radar (Earth) and laser (Moon) elevation data?

Test (`pipeline/sensor_check.py`): 900 lunar and 2,441 Earth windows, grouped by median slope. RMS height difference measured at 80 m to 2.56 km; Hurst refitted over short distances only and long distances only. Sensor noise acts at short distances, so a sensor effect should shrink at long distances.

| Median slope | Gap, 80 m to 1.28 km (as shipped) | Gap, short only (80 to 320 m) | Gap, long only (320 m to 2.56 km) |
|---|---|---|---|
| 2 to 5 deg | 0.15 | 0.09 | 0.19 |
| 5 to 10 deg | 0.18 | 0.11 | 0.26 |
| 10 to 20 deg | 0.19 | 0.09 | 0.28 |

Result: the gap is larger at long distances, where sensor noise is negligible next to the terrain signal. This points to a real terrain difference: on Earth, height differences stop growing sooner with distance (valley and ridge spacing of roughly a kilometre), while lunar highland slopes persist across kilometres. VERIFIED on our data.

Not settled: a laser-to-laser comparison (ICESat-2 on Earth against LOLA) would be the direct proof. Near-flat Earth windows (median slope under about 1 degree) remain suspect because radar noise is comparable to their relief; they should be excluded from terrain matching.
