"""Stage 2 test, fixed before the data arrived: at 2 km windows and 30 m detail, do known analog sites beat random bare-land
areas more often than they did at 10 km? Lunar reference: the central 2 km of landing-like lunar spots, from LOLA 20 m data
resampled to 30 m, measured with the same code (terrain.py)."""
import json, glob, os, sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import zoom
sys.path.insert(0, os.path.dirname(__file__))
from terrain import features
rng = np.random.default_rng(31); H_RANGE, RET_RANGE = 0.4, 0.5
areas = {a["id"]: a for a in json.load(open("data/zoom_areas.json"))}
A = {}
for f in glob.glob("data/out/zoom/*.json"):
    r = json.load(open(f))
    if not r: continue
    nd = np.array([np.nan if x["ndvi_max"] is None else x["ndvi_max"] for x in r])
    A[os.path.basename(f)[:-5]] = {"hist": np.array([x["slope_hist"] for x in r], "float32") / 10000, "H": np.array([x["hurst"] for x in r]),
        "ret": np.array([x["slope320_p50"] / max(x["slope_p50"], 1e-6) for x in r]), "s50": np.array([x["slope_p50"] for x in r]),
        "bare": np.where(np.isnan(nd), 1.0, np.clip(1 - (nd - 0.2) / 0.4, 0, 1)), "lat": np.array([x["lat"] for x in r]), "lon": np.array([x["lon"] for x in r])}
ds = rasterio.open("data/moon/LDEM_80S_20MPP_ADJ.TIF")
grid = json.load(open("data/out/moon_grid.json"))
land = [g for g in grid if g["lat"] <= -84 and g["psr_share"] < 0.15 and g["illum_mean"] > 0.25]
moon = []
for g in [land[i] for i in rng.permutation(len(land))]:
    ox, oy = rng.uniform(-3000, 3000, 2)                                   # a 2 km window somewhere inside the 10 km spot
    d = ds.read(1, window=from_bounds(g["x"] + ox - 1000, g["y"] + oy - 1000, g["x"] + ox + 1000, g["y"] + oy + 1000, ds.transform)).astype("float64")
    if d.shape != (100, 100) or not np.isfinite(d).all(): continue
    f, _ = features(zoom(d, 0.67, order=1), 2000 / 67); moon.append(f)
    if len(moon) == 120: break
ms = np.array([m["slope_p50"] for m in moon]); print("lunar 2 km windows:", len(moon), "| median slope p10 %.1f p50 %.1f p90 %.1f | Hurst median %.2f" % (*np.percentile(ms, [10, 50, 90]), np.median([m["hurst"] for m in moon])))
def score(a, m, mode="both"):
    sl = 1 - 0.5 * np.abs(a["hist"] - np.array(m["slope_hist"], "float32")).sum(1)
    sc = 0.5 * (np.clip(1 - np.abs(a["H"] - m["hurst"]) / H_RANGE, 0, 1) + np.clip(1 - np.abs(a["ret"] - m["slope320_p50"] / max(m["slope_p50"], 1e-6)) / RET_RANGE, 0, 1))
    s = {"both": 0.5 * sl + 0.5 * sc, "slope": sl, "scale": sc}[mode]
    return s * a["bare"] * (a["s50"] >= 1.0)
def auc(a, b): a, b = np.asarray(a)[:, None], np.asarray(b)[None, :]; return float(((a > b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))
K = [k for k in A if areas[k]["group"] == "known"]; R = [k for k in A if areas[k]["group"] == "random"]
out = {"lunar_windows": len(moon), "known_areas_with_windows": len(K), "random_areas": len(R), "auc": {}}
per = {areas[k]["name"]: [] for k in K}
for mode, label in (("both", "slope match + roughness across scales"), ("slope", "slope match only"), ("scale", "roughness across scales only")):
    best, one = [], []
    for m in moon:
        kb = [score(A[k], m, mode).max() for k in K]; rb = [score(A[k], m, mode).max() for k in R]
        k1 = [rng.choice(score(A[k], m, mode)) for k in K]; r1 = [rng.choice(score(A[k], m, mode)) for k in R]
        best.append(auc(kb, rb)); one.append(auc(k1, r1))
        if mode == "both":
            for k, s in zip(K, kb): per[areas[k]["name"]].append(float((np.array(rb) < s).mean()))
    out["auc"][label] = {"best_window_per_area": round(float(np.mean(best)), 3), "one_window_per_area": round(float(np.mean(one)), 3), "p10_p90": [round(float(np.percentile(best, 10)), 2), round(float(np.percentile(best, 90)), 2)]}
s1 = json.load(open("data/out/benchmark_auc.json"))["per_site_share_of_random_areas_beaten"]
out["per_site"] = {k: {"stage2_2km": round(float(np.mean(v)), 2), "stage1_10km": s1.get(k), "windows": int(len(A[[a for a in K if areas[a]["name"] == k][0]]["H"]))} for k, v in sorted(per.items(), key=lambda z: -np.mean(z[1]))}
json.dump(out, open("data/out/zoom_benchmark.json", "w"), indent=1); print(json.dumps(out, indent=1))
