"""Stage 2 (2 km windows at 30 m): choose the Earth areas to examine.
known     = every known analog site in pipeline/known_sites.csv (15 km radius)
random    = 150 random bare-land points more than 300 km from any known site (15 km radius), same rule as the stage 1 benchmark
shortlist = the 200 best stage 1 windows by mean terrain score over landing-like lunar spots, at least 30 km apart (7 km radius)"""
import csv, json, sys, os, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
rng = np.random.default_rng(21); L = ls.load(); RE = 6371.0
def xyz(lat, lon): la, lo = np.radians(lat), np.radians(lon); return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
chord = lambda km: 2 * np.sin(km / RE / 2)
usable = L["slope_p50"] >= 1.0; P = xyz(L["lat"], L["lon"])
known = list(csv.DictReader(open("pipeline/known_sites.csv"))); K = xyz(np.array([float(k["lat"]) for k in known]), np.array([float(k["lon"]) for k in known]))
areas = [{"id": f"known_{i:02d}", "group": "known", "name": k["name"], "lat": float(k["lat"]), "lon": float(k["lon"]), "radius_km": 15, "nomask": float(k["lat"]) < -60} for i, k in enumerate(known)]
far = np.array([len(x) == 0 for x in cKDTree(K).query_ball_point(P, chord(300))]) & usable
for n, c in enumerate(rng.permutation(np.where(far)[0])[:150]):
    areas.append({"id": f"random_{n:03d}", "group": "random", "name": "", "lat": float(L["lat"][c]), "lon": float(L["lon"][c]), "radius_km": 15, "nomask": False})
grid = json.load(open("data/out/moon_grid.json"))
land = [g for g in grid if g["lat"] <= -84 and g["psr_share"] < 0.15 and g["illum_mean"] > 0.25 and g["t_avg"] is not None]
spots = [land[i] for i in rng.choice(len(land), 120, replace=False)]; acc = np.zeros(len(L["lat"]))
for s in spots: acc += ls.afom(ls.foms(L, s), "mobility")
acc /= len(spots); order = np.argsort(-acc); chosen = []
for i in order:
    if all(np.linalg.norm(P[i] - P[j]) > chord(30) for j in chosen): chosen.append(i)
    if len(chosen) == 200: break
dk = cKDTree(K).query(P[chosen])[0]
for n, i in enumerate(chosen):
    areas.append({"id": f"short_{n:03d}", "group": "shortlist", "name": "", "lat": float(L["lat"][i]), "lon": float(L["lon"][i]), "radius_km": 7, "nomask": bool(L["nomask"][i] > 0),
                  "stage1_mean_score": round(float(acc[i]), 3), "km_to_nearest_known": round(float(2 * RE * np.arcsin(dk[n] / 2)), 0)})
json.dump(areas, open("data/zoom_areas.json", "w"), indent=0)
print("areas:", {g: sum(a["group"] == g for a in areas) for g in ("known", "random", "shortlist")})
print("windows with mean terrain score >= 0.70:", int((acc >= 0.70).sum()), "| shortlist score range", round(float(acc[chosen[0]]), 2), "to", round(float(acc[chosen[-1]]), 2))
for a in [x for x in areas if x["group"] == "shortlist"][:8]: print("  ", a["lat"], a["lon"], a["stage1_mean_score"], a["km_to_nearest_known"], "km from nearest known")
