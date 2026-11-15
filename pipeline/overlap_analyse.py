"""Analyse the placement experiment: rover-terrain score (slope + roughness across scales, as in lib_score) for shifted squares."""
import glob, json, numpy as np
H_RANGE, RET_RANGE = 0.4, 0.5
grid = json.load(open("data/out/moon_grid.json")); rng = np.random.default_rng(3)
land = [g for g in grid if g["slope_p50"] < 10 and g["psr_share"] < 0.2]; spots = [land[i] for i in rng.choice(len(land), 150, replace=False)]
mh = np.array([s["slope_hist"] for s in spots], "float32"); mH = np.array([s["hurst"] for s in spots]); mret = np.array([s["slope320_p50"] / max(s["slope_p50"], 1e-6) for s in spots])
gain, sd, flips, tiles, ok8a, ok8b = [], [], 0, 0, 0, 0; allbest_a, allbest_s = [], []
for f in sorted(glob.glob("data/cache/overlap/*.npz")):
    R = np.load(f)["rows"]
    if len(R) < 50: continue
    r, c, hu, sp, s320 = R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4]; hist = R[:, 6:]; keep = sp >= 1.0
    slope = 1 - 0.5 * np.abs(hist[None] - mh[:, None]).sum(2)
    scale = 0.5 * (np.clip(1 - np.abs(hu[None] - mH[:, None]) / H_RANGE, 0, 1) + np.clip(1 - np.abs((s320 / np.maximum(sp, 1e-6))[None] - mret[:, None]) / RET_RANGE, 0, 1))
    sc = (0.5 * slope + 0.5 * scale) * keep[None]                                  # spots x windows
    al = ((r % 124 == 0) & (c % 124 == 0))                                           # squares on the 10 km grid (what the library holds)
    if al.sum() < 4: continue
    ba, bs = sc[:, al].max(1), sc.max(1); gain.append(bs - ba); allbest_a.append(ba); allbest_s.append(bs); tiles += 1
    # how much does the score change when an aligned square moves by 2.5 km in any direction?
    ai = np.where(al)[0]; pos = {(int(a), int(b)): i for i, (a, b) in enumerate(zip(r, c))}
    for i in ai[::3]:
        nb = [pos.get((int(r[i]) + dr, int(c[i]) + dc)) for dr in (-31, 0, 31) for dc in (-31, 0, 31) if (dr or dc)]; nb = [n for n in nb if n is not None]
        if len(nb) >= 3 and keep[i]: sd.append(np.abs(sc[:, nb] - sc[:, [i]]).mean())
g = np.concatenate(gain); A = np.stack(allbest_a); S = np.stack(allbest_s)
print("tiles", tiles, "lunar spots", len(spots))
print(f"best score per map square: 10 km grid {A.mean():.3f}, with 2.5 km shifts {S.mean():.3f}; mean gain {g.mean():.3f}, median {np.median(g):.3f}, 90th pct {np.percentile(g,90):.3f}, max {g.max():.3f}")
print(f"squares reaching 0.80: {100*(A>=.8).mean():.1f}% -> {100*(S>=.8).mean():.1f}% ; reaching 0.90: {100*(A>=.9).mean():.1f}% -> {100*(S>=.9).mean():.1f}%")
print(f"score change when one square is moved 2.5 km: mean {np.mean(sd):.3f}, 90th pct {np.percentile(sd,90):.3f}")
# does the best map square for a lunar spot change?
print(f"best map square (of {tiles}) changes for {100*(A.argmax(0)!=S.argmax(0)).mean():.0f}% of lunar spots; top-5 overlap {np.mean([len(set(np.argsort(-A[:,k])[:5])&set(np.argsort(-S[:,k])[:5]))/5 for k in range(len(spots))]):.2f}")
