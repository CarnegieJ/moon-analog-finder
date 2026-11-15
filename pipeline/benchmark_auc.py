"""Honest validation: do known analog sites score higher than random bare land?
For many landing-like lunar spots, compare the best Earth window within 30 km of each known analog site with the best window within
30 km of random bare-land points more than 300 km from every known site. AUC = chance that a known site beats a random area
(0.5 = no better than chance, 1.0 = always better). Also reported with one random window per area, which removes any advantage
from an area simply holding more windows."""
import csv, json, sys, os, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
rng = np.random.default_rng(11); L = ls.load(); N = len(L["lat"]); RE = 6371.0
def xyz(lat, lon): la, lo = np.radians(lat), np.radians(lon); return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
chord = lambda km: 2 * np.sin(km / RE / 2)
usable = L["slope_p50"] >= 1.0                      # near-flat windows excluded: radar noise is comparable to their relief
P = xyz(L["lat"], L["lon"]); tree = cKDTree(P)
known = list(csv.DictReader(open("pipeline/known_sites.csv"))); K = xyz(np.array([float(k["lat"]) for k in known]), np.array([float(k["lon"]) for k in known]))
kn = [np.array([i for i in tree.query_ball_point(K[j], chord(30)) if usable[i]]) for j in range(len(known))]
inlib = [j for j in range(len(known)) if len(kn[j])]
far = np.array([len(x) == 0 for x in cKDTree(K).query_ball_point(P, chord(300))]) & usable
cand = rng.permutation(np.where(far)[0]); rn = []
for c in cand:
    idx = np.array([i for i in tree.query_ball_point(P[c], chord(30)) if usable[i]])
    if len(idx): rn.append(idx)
    if len(rn) == 400: break
grid = json.load(open("data/out/moon_grid.json"))
land = [g for g in grid if g["lat"] <= -84 and g["psr_share"] < 0.15 and g["illum_mean"] > 0.25 and g["t_avg"] is not None]
spots = [land[i] for i in rng.choice(len(land), min(80, len(land)), replace=False)]
def auc(a, b): a, b = np.asarray(a)[:, None], np.asarray(b)[None, :]; return float(((a > b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))
variants = {"slope + roughness across scales (shipped)": lambda f: f["bare"] * (0.5 * f["slope"] + 0.5 * f["scale"]),
            "slope only": lambda f: f["bare"] * f["slope"], "roughness across scales only": lambda f: f["bare"] * f["scale"]}
res = {v: {"best": [], "one": []} for v in variants}; per_site = {known[j]["name"]: [] for j in inlib}
for s in spots:
    f = ls.foms(L, s)
    for v, fn in variants.items():
        a = fn(f); kb = [a[kn[j]].max() for j in inlib]; rb = [a[x].max() for x in rn]
        k1 = [a[rng.choice(kn[j])] for j in inlib]; r1 = [a[rng.choice(x)] for x in rn]
        res[v]["best"].append(auc(kb, rb)); res[v]["one"].append(auc(k1, r1))
        if v.startswith("slope + "):
            for j, sc in zip(inlib, kb): per_site[known[j]["name"]].append(float((np.array(rb) < sc).mean()))
out = {"lunar_spots": len(spots), "landing_like_spots_available": len(land), "known_sites_total": len(known), "known_sites_in_library": len(inlib),
       "known_not_in_library": [known[j]["name"] for j in range(len(known)) if j not in inlib], "random_areas": len(rn),
       "auc": {v: {"best_window_per_area": round(float(np.mean(r["best"])), 3), "one_window_per_area": round(float(np.mean(r["one"])), 3),
                   "spread_over_lunar_spots_p10_p90": [round(float(np.percentile(r["best"], 10)), 2), round(float(np.percentile(r["best"], 90)), 2)]} for v, r in res.items()},
       "per_site_share_of_random_areas_beaten": {k: round(float(np.mean(v)), 2) for k, v in sorted(per_site.items(), key=lambda z: -np.mean(z[1]))}}
json.dump(out, open("data/out/benchmark_auc.json", "w"), indent=1); print(json.dumps(out, indent=1))
