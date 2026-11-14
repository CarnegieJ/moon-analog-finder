"""Baseline benchmark: coverage, recovery, rejection, stability. Re-run after every method change and compare."""
import json, csv, sys, os, copy, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
rng = np.random.default_rng(7)
L = ls.load(); N = len(L["lat"])
sites = list(csv.DictReader(open("data/sites_earth.csv")))
known = [s for s in sites if s["group"] == "known"]
grid = json.load(open("data/out/moon_grid.json")); named = json.load(open("data/out/moon_profiles.json"))
P = list(ls.W); PN = {"mobility": "rover driving", "shadow": "shadow work", "darkness": "darkness survival"}
out = {"library_windows": N}

# 1. Coverage: is each known analog site represented in the library (a window within 0.3 degrees)?
near = {}
for s in known:
    la, lo = float(s["lat"]), float(s["lon"])
    m = (np.abs(L["lat"] - la) < 0.3) & (np.abs(L["lon"] - lo) * np.cos(np.radians(la)) < 0.3)
    near[s["name"]] = np.where(m)[0]
out["coverage"] = {"in_library": int(sum(len(v) > 0 for v in near.values())), "of": len(known), "missing": [k for k, v in near.items() if len(v) == 0]}

# 2. Recovery: over a sample of lunar spots, the best percentile rank each known site reaches for any purpose
spots = [g for g in grid if g["t_avg"] is not None]; pick = [spots[i] for i in rng.choice(len(spots), 300, replace=False)]
best = {k: {"pct": 100.0} for k in near if len(near[k])}
for g in pick:
    f = ls.foms(L, g)
    for p in P:
        a = ls.afom(f, p); srt = np.sort(a)
        for k, idx in near.items():
            if not len(idx): continue
            sc = float(a[idx].max()); pct = 100.0 * (1 - np.searchsorted(srt, sc, side="left") / N)      # top X percent
            if pct < best[k]["pct"]: best[k] = {"pct": round(pct, 2), "score": round(sc, 2), "purpose": PN[p], "spot": f'{abs(g["lat"]):.1f}S {g["lon"]:.0f}E, median slope {g["slope_p50"]:.0f} deg'}
out["recovery"] = {"lunar_spots_sampled": len(pick), "sites": best, "top1pct": int(sum(v["pct"] <= 1 for v in best.values())), "top5pct": int(sum(v["pct"] <= 5 for v in best.values())), "of": len(best)}

# 3. Rejection: negative controls (scored on the 15-site table) and vegetation leakage in the library
sc = json.load(open("data/out/scores.json")); neg = []
for tid, T in sc["targets"].items():
    for r in T["purposes"]["mobility"]:
        if r["group"] == "negative": neg.append(r["afom"])
out["rejection"] = {"negative_control_max_score_rover_driving": float(max(neg)), "library_windows_with_vegetation_index_over_0.2": int(np.nansum(L["ndvi"] > 0.2001))}

# 4. Stability: top-10 regions when each weight moves by +/-0.10 (then renormalised)
def top10(a):
    o = np.argsort(-a); seen, t = set(), []
    for i in o:
        k = (int(np.floor(L["lat"][i] / 2)), int(np.floor(L["lon"][i] / 2)))
        if k in seen: continue
        seen.add(k); t.append(k)
        if len(t) == 10: break
    return set(t)
W0 = copy.deepcopy(ls.W); stab = {}
for t in named:
    f = ls.foms(L, t["features"])
    for p in P:
        base = top10(ls.afom(f, p)); keep = []
        for k in W0[p]:
            for d in (-0.10, 0.10):
                w = dict(W0[p]); w[k] = max(0.0, w[k] + d); s = sum(w.values()); ls.W[p] = {q: v / s for q, v in w.items()}
                keep.append(len(base & top10(ls.afom(f, p))) / 10)
        ls.W[p] = dict(W0[p]); stab[f'{t["name"]} / {PN[p]}'] = {"mean_kept": round(float(np.mean(keep)), 2), "worst_kept": round(float(np.min(keep)), 2)}
out["stability"] = {"cases": stab, "mean_kept": round(float(np.mean([v["mean_kept"] for v in stab.values()])), 2), "worst_kept": round(float(min(v["worst_kept"] for v in stab.values())), 2)}
json.dump(out, open("data/out/benchmark.json", "w"), indent=1)
print(json.dumps(out, indent=1))
