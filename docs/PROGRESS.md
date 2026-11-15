# Progress log

NASA Space Apps Challenge 2026 (Nov 14 to 15). Solo build. Times are US Eastern.
Live app: https://shashidharprakash33--moon-analog-finder-web.modal.run

## Status at a glance (Sat Nov 14, evening)

| Phase | What | Status |
|---|---|---|
| 0 | Setup: project folder, environment, keys kept in `.env` | Done |
| 1 | Moon reference numbers for lunar spots | Done |
| 2 | Earth sites and terrain scoring | Done |
| 3 | Bare surface, temperature, sun angle, darkness | Done |
| 4 | Wider Earth search (full bare-land scan) | Done |
| 5 | Web app | First version live |
| 6 | Benchmark baseline | Done |
| 7 | Improvements from the benchmark | Next |
| 8 | Video, submission text, repository | Sunday |

## What was built, in order

### Saturday morning: understanding and planning
- Read the challenge statement, the author's video and the resources page.
- Collected the judging criteria and submission rules (see `HANDOFF.md`).
- Scope decision: Moon only. Mars dropped.
- Found three separate pieces of NASA guidance and joined them into one method (see `METHOD_REASONING.md`):
  what a south pole base needs (architecture papers), how NASA scored analog fidelity (2011 Analog Assessment Tool), and how NASA scores physical similarity (lunar simulant Figure of Merit).

### Saturday midday: Moon side
- Downloaded NASA LRO products for 80 to 90 S: elevation and slope at 80 m, average sunlight, permanent shadow, Diviner temperatures.
- Computed reference numbers for three approximate Artemis III regions (Haworth, Malapert Massif, de Gerlache Rim 2).
- Check: our slope code matches NASA's own slope product within 0.2 degrees.
- Later extended to a grid of 11,221 lunar spots, one every 5 km, so any clicked spot can be scored.

### Saturday afternoon: Earth side and scoring
- 15 starter Earth sites: 10 known analogs, 3 that should score low, 2 little-studied candidates.
- First terrain-only ranking failed on purpose-built traps: a forested mountain ranked first for the steep lunar targets, and farmland was not rejected for the flat target.
- Added bare surface (vegetation), temperature, low sun and darkness. Forest and farmland then scored zero.
- Three test purposes introduced, each with its own weights: rover driving, shadow work and crater access, power and darkness survival.

### Saturday afternoon: wider search
- Sample search: 399 map squares, 25,761 windows, processed locally.
- Full search on Modal: 3,217 map squares (every square with at least 10% bare, snow-free land), 167,471 windows.
- Result: the best darkness-survival windows on Earth are on Devon Island, including the location of Haughton Crater, NASA's long-running analog site. The search had no knowledge of that site.
- New candidate regions surfaced: East Greenland, Peary Land, northern Ellesmere Island and the Taymyr Peninsula for shadow work; the Andes of northern Chile and northwest Argentina, western Tibet and central Afghanistan for rover driving on steep ground. Place names are read from coordinates and still need checking.

### Saturday evening: app, hosting, benchmark
- App built as a static site: polar map with four layer toggles, spot details, purpose picker with weight sliders, ranked Earth sites on a world map, side-by-side 3D terrain, scorecard with a "where it breaks" line.
- All scoring runs in the browser on about 21 MB of precomputed data. No server-side computation and no keys.
- Hosted on Modal at the link above.
- Benchmark baseline measured (see `BENCHMARK.md`): coverage 7 of 10 known sites, recovery 6 of 7, rejection passing, stability 92% on average and 50% at worst.

### Saturday night: audit and version 2
- Audit of our own method against published work (see `AUDIT.md`). Main finding: the three terrain factors were 98 to 99% correlated, and terrain was measured at one scale only.
- Added multi-scale roughness on both bodies (slope at 320 m, Hurst exponent). Lunar median 0.93 against a published 0.95 for the lunar highlands.
- Rescanned Earth on Modal: 4,242 map squares, 236,193 windows, now including ice-free Antarctic areas and slightly vegetated ground.
- Benchmark version 2: coverage 10 of 10, recovery 8 of 10, terrain factors now independent (see `BENCHMARK.md`).
- App moved to the new library and scoring.

## Known problems and limits
- Antarctica is represented only by four ice-free areas added by hand, and those windows are not ice-filtered.
- Earth windows do not overlap, so a match that straddles two windows can be missed.
- Lunar region centres are approximate. NASA's release names the regions but gives no coordinates.
- The 10 km window cannot resolve small features. Meteor Crater (about 1.2 km) is the clear failure case.
- Darkness-survival rankings contain many tied sites, so their order is not meaningful.
- No Earth site scores above about 0.63 for shadow work, and none matches the cold of permanently shadowed ground (about 39 K at the Haworth crater floor against about 233 K at Earth's coldest library sites).
- Ice is not scored. The Diviner ice-depth field shows a value of -1 in places and its meaning is not confirmed.
- Weights, the vegetation cut-off and the 200 K temperature range are set by the team, not by NASA.
- New candidate sites have not been checked against the literature, so "new" is a claim still to be verified.

## Next steps
1. Coverage fix: loosen the vegetation cut-off, rescan on Modal, add ice-free Antarctic squares by hand.
2. Show ties as ties in the app.
3. Cited coordinates for the Artemis III regions; literature check on the top candidates.
4. Faster scoring in the browser.
5. Optional: similar lunar spots, shareable brief, plain-language summaries.
6. Sunday: 30-second video with subtitles, submission form text, final repository.

## Tools and services used
- NASA data: Lunar Reconnaissance Orbiter (LOLA, Diviner), MODIS, GIBS imagery, Earthdata.
- ESA data: Copernicus DEM GLO-90.
- Modal for the full Earth scan and for hosting.
- Miro for the user-journey sketch.
- Claude (Anthropic) for research, planning and code. Scores come from the data and code in this repository, not from an AI model.
