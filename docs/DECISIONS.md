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
