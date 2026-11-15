# Decision log

Rule (Shashi, Nov 14): every step must be justified by a real use case. If a step has no real-use reason, we do not do it.

Primary user: an engineer or field-test planner who has a lunar south pole site in mind and must choose where on Earth to test hardware or procedures for it.

| # | Decision | Real-use justification | Evidence | Status |
|---|---|---|---|---|
| 1 | Moon-first flow (pick lunar spot, get Earth sites) is the main flow | In practice the lunar site is chosen first, then test locations are sought for it. The challenge also asks for Earth locations that analog the Moon base locations. | NASA named Artemis III candidate regions (Oct 2024); challenge statement | VERIFIED |
| 2 | Earth-first flow is secondary, built only if cheap | Real but smaller audience: teams that already own or use a field site and want to know what it is good for. | Our judgement | Team-set |
| 3 | User states a test purpose before ranking | A site can be good for rover tests and useless for thermal tests. One blended score would mislead a planner. | NASA simulant Figure of Merit paper: a low score does not rule a simulant out for some uses | VERIFIED |
| 4 | Three purposes: rover mobility, shadow and crater access, darkness survival | These are things NASA says must be solved for the base. | NASA gaps FN-M-302, FN-M-304; 120+ hours darkness survival (Moon Base User's Guide 2026) | VERIFIED |
| 5 | Moon map is clickable anywhere, not only presets | An engineer evaluates candidate spots that are not on any preset list; NASA's own site list changed from 13 to 9 regions. | NASA 2022 and 2024 releases | VERIFIED |
| 6 | Window size 10 km (5 km radius) around the chosen spot | Matches how far surface assets are expected to travel from a landing point. | NASA Lunar Mobility Drivers and Needs 2024: traverse ranges of 5 to 5,000 m | VERIFIED |
| 7 | Terrain compared at 80 to 90 m on both bodies with the same code | A planner needs like-for-like numbers; slope depends on pixel size. | Our slope code matches NASA's slope product within 0.2 deg | VERIFIED |
| 8 | Always show "cannot match": gravity, vacuum, radiation | A planner must know what an Earth test cannot prove. | Challenge statement | VERIFIED |
| 9 | Tool recommends where to test and what each site can prove; it does not plan missions | Overclaiming would mislead users and fail scientific validity. | Judging criterion: Validity | VERIFIED |
| 10 | Known analog sites shown separately from new candidates | A planner wants both the trusted options and under-used alternatives; the challenge asks for new ones. | Challenge statement | VERIFIED |
| 11 | Each factor is scored as "the fraction that is the same" (0 to 1) | A planner needs a number that means the same thing for every factor and can be explained in one sentence. | NASA lunar simulant Figure of Merit (Schrader et al. 2009) | VERIFIED |
| 12 | Vegetated ground is scored zero for rover driving and shadow work (a gate, not a weight) | A site that matches the Moon's shape but is forested cannot be used. Terrain-only ranking put a forested mountain first. | Our test with Appalachian forest, Iowa farmland and Amazon controls | VERIFIED |
| 13 | Darkness is scored against a 120-hour target | A power system test needs a real dark period at least as long as the one NASA says the base must survive. | Moon Base User's Guide, NASA, April 2026 | VERIFIED |
| 14 | Earth search covers all bare, snow-free land, not a hand-picked list | A planner should not be limited to sites someone already thought of; the challenge asks for unrecognised analogs. | Challenge statement; 3,217 squares scanned | VERIFIED |
| 15 | The app says "no strong match" or "partial match" when the best score is low | Presenting a weak best result as a recommendation would mislead the user. | Our results: no site above about 0.63 for shadow work | VERIFIED |
| 16 | Known analog sites are scored and shown next to new candidates | A planner trusts a new site more when the same method also rates familiar sites sensibly. | Benchmark: 6 of 7 known sites reach the top 1% | VERIFIED |
| 17 | All scoring runs in the browser on precomputed data | The tool must work for anyone with a link, with no account, key or server wait. | Submission rule: public link, no login | VERIFIED |
| 18 | Flat south-pole map, not a globe | All candidate regions are within 10 degrees of the pole and would be crammed at the edge of a globe. | Our judgement | Team-set |
| 19 | 3D terrain is shown next to the factor scores, never alone | The challenge warns against choosing analogs because they look alike. | Challenge statement | VERIFIED |
| 20 | A benchmark of four measures is re-run after every method change | Without a fixed test we cannot tell whether a change improved the tool. | docs/BENCHMARK.md | Team-set |
| 21 | Mars, radar roughness, image similarity and a full weighting exercise were cut | None could be finished and validated in two days by one person. | Time budget | Team-set |


## Added Sun Nov 15 (afternoon)

- **Sun, reach and line-of-sight tests** (app step 4, `pipeline/shadow_sim.py`). Why: shadow length, joined-up drivable ground and visible ground decide what a field rehearsal can test, and the terrain score cannot see them. Check: the Moon-side shadow calculation reproduces NASA's average sunlight map within 1.5 percentage points and the permanent shadow map within 1.2 on average over 63 spots. Both use the same LOLA elevation, so this checks the calculation only. The Earth side is unchecked.
- **Frozen ground factor and "Ice drilling and digging" purpose** (`pipeline/permafrost.py`). Why: the challenge lists ice and permafrost, and ice is the main reason for going to the south pole. Moon: share of the window with stable ground ice in the Diviner model. Earth: Global Permafrost Zonation Index (Gruber 2012). Score: smaller share divided by larger share. Weights 50 frozen, 30 cold, 20 slope, team-set. Checks: for Haworth, Haughton (Devon Island) ranks in the top 1% and Axel Heiberg Island in the top 2% of 236,193 windows; top-100 overlap under 20% weight changes is 95% on average, 79% worst. Limits: the map stops at 60 S (Antarctic Dry Valleys not scored); permafrost is frozen soil near 260 K, not lunar ice.
- **Not built, on purpose:** dust (lunar dust is not wind-driven), lava tubes (none known at these targets), rock type as a score (the GLiM rock classes have no anorthosite class; not verified against other maps).
