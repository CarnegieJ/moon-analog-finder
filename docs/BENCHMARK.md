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
