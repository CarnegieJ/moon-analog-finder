"""Known-site check repeated on the overlapping-square library (version 3), next to the old 10 km grid, using the same known sites,
the same 400 random bare-land areas (same centres) and the same 80 lunar spots as benchmark_auc.py."""
import csv, json, sys, os, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
rng = np.random.default_rng(11); L = ls.load(); RE = 6371.0
def xyz(lat, lon): la, lo = np.radians(lat), np.radians(lon); return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
chord = lambda km: 2 * np.sin(km / RE / 2)
usable = L["slope_p50"] >= 1.0; P = xyz(L["lat"], L["lon"]); tree = cKDTree(P)
known = list(csv.DictReader(open("pipeline/known_sites.csv"))); K = xyz(np.array([float(k["lat"]) for k in known]), np.array([float(k["lon"]) for k in known]))
kn = [np.array([i for i in tree.query_ball_point(K[j], chord(30)) if usable[i]]) for j in range(len(known))]; inlib = [j for j in range(len(known)) if len(kn[j])]
far = np.array([len(x) == 0 for x in cKDTree(K).query_ball_point(P, chord(300))]) & usable; cand = rng.permutation(np.where(far)[0]); rn, rc = [], []
for c in cand:
    idx = np.array([i for i in tree.query_ball_point(P[c], chord(30)) if usable[i]])
    if len(idx): rn.append(idx); rc.append(P[c])
    if len(rn) == 400: break
grid = json.load(open("data/out/moon_grid.json")); land = [g for g in grid if g["lat"] <= -84 and g["psr_share"] < 0.15 and g["illum_mean"] > 0.25 and g["t_avg"] is not None]
spots = [land[i] for i in rng.choice(len(land), min(80, len(land)), replace=False)]
# version 3 windows near the same centres
S = np.load("data/cache/lib3/s.npy", mmap_mode="r"); Hh = np.load("data/cache/lib3/hist.npy", mmap_mode="r"); cols = open("data/cache/lib3/cols.txt").read().split()
lat3, lon3 = np.array(S[:, 0]), np.array(S[:, 1]); t3 = cKDTree(xyz(lat3, lon3)); ok3 = np.array(S[:, 5]) >= 1.0; old3 = np.array(S[:, 19]) == 1
centres = [K[j] for j in inlib] + rc; near = [np.array([i for i in t3.query_ball_point(c, chord(30)) if ok3[i]], dtype=int) for c in centres]
allidx = np.unique(np.concatenate(near)); sub = np.array(S[allidx]); c3 = {k: sub[:, i] for i, k in enumerate(cols)}
L3 = {**c3, "hist": np.array(Hh[allidx], "float32") / 10000, "pzi": np.full(len(allidx), np.nan, "float32")}; L3["cls"] = ls.classes(L3["hist"])
loc = [np.searchsorted(allidx, x) for x in near]; loc_old = [x[old3[allidx[x]]] for x in loc]
def auc(a, b): a, b = np.asarray(a)[:, None], np.asarray(b)[None, :]; return float(((a > b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))
fn = lambda f: f["bare"] * (0.5 * f["slope"] + 0.5 * f["scale"]); nk = len(inlib); R = {"old library": [], "v3 old-grid squares only": [], "v3 all placements (best)": [], "v3 all placements (one random)": [], "old (one random)": []}
best_known = {known[j]["name"]: [[], []] for j in inlib}
for s in spots:
    a = fn(ls.foms(L, s)); a3 = fn(ls.foms(L3, s))
    kb = [a[kn[j]].max() for j in inlib]; rb = [a[x].max() for x in rn]; R["old library"].append(auc(kb, rb)); R["old (one random)"].append(auc([a[rng.choice(kn[j])] for j in inlib], [a[rng.choice(x)] for x in rn]))
    mx = lambda idx: a3[idx].max() if len(idx) else np.nan
    b_old = np.array([mx(x) for x in loc_old]); b_all = np.array([mx(x) for x in loc]); m = np.isfinite(b_old); mk, mr = m[:nk], m[nk:]
    R["v3 old-grid squares only"].append(auc(b_old[:nk][mk], b_old[nk:][mr])); R["v3 all placements (best)"].append(auc(b_all[:nk], b_all[nk:]))
    R["v3 all placements (one random)"].append(auc([a3[rng.choice(x)] for x in loc[:nk]], [a3[rng.choice(x)] for x in loc[nk:]]))
    for j, o, n in zip(inlib, kb, b_all[:nk]): best_known[known[j]["name"]][0].append(o); best_known[known[j]["name"]][1].append(n)
out = {k: {"auc_mean": round(float(np.mean(v)), 3), "auc_p10": round(float(np.percentile(v, 10)), 3), "auc_p90": round(float(np.percentile(v, 90)), 3)} for k, v in R.items()}
out["windows_near_centres_v3"] = int(len(allidx)); out["known_sites_in_library"] = nk; out["random_areas"] = len(rn); out["lunar_spots"] = len(spots)
out["known_site_best_score_old_vs_v3"] = {k: [round(float(np.mean(v[0])), 3), round(float(np.mean(v[1])), 3)] for k, v in best_known.items()}
rb_old = np.mean([fn(ls.foms(L, s))[np.concatenate(rn)].mean() for s in spots[:5]])
json.dump(out, open("data/out/benchmark_auc_v3.json", "w"), indent=1); print(json.dumps(out, indent=1))
