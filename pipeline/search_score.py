"""Score every candidate Earth window against the three starter lunar targets, for each purpose. Summarise by region."""
import json, glob, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from score import foms, afom, PURPOSES
cand = []
for f in glob.glob("data/out/search/*.json"):
    for r in json.load(open(f)):
        r["slope_hist"] = [v / 10000 for v in r["slope_hist"]]; cand.append(r)
print("candidate windows:", len(cand))
known = [(s["name"], s["lat"], s["lon"]) for s in json.load(open("data/out/earth_profiles.json")) if s["group"] == "known"]
def near_known(la, lo):
    for n, a, b in known:
        if abs(la - a) < 0.5 and abs(lo - b) * np.cos(np.radians(la)) < 0.5: return n
    return None
moon = json.load(open("data/out/moon_profiles.json")); out = {}
for t in moon:
    for pk in PURPOSES:
        sc = []
        for c in cand:
            f = foms(c, t["features"]); sc.append((afom(f, pk), c, f))
        sc.sort(key=lambda z: -z[0])
        top, seen = [], set()
        for a, c, f in sc:                                # best window per 1-degree square, so the list shows distinct places
            key = (int(np.floor(c["lat"])), int(np.floor(c["lon"])))
            if key in seen: continue
            seen.add(key); top.append({"score": round(a, 3), "lat": c["lat"], "lon": c["lon"], "known": near_known(c["lat"], c["lon"]),
                                       "f": {k: round(v, 2) for k, v in f.items()}, "slope_p50": c["slope_p50"], "t_night_min": c["t_night_min"], "dark_h": c["dark_longest_h"]})
            if len(top) == 12: break
        out[f'{t["id"]}|{pk}'] = top
        print(f'\n{t["name"]} / {PURPOSES[pk]["name"]}  (all-window score: median {np.median([z[0] for z in sc]):.2f}, max {sc[0][0]:.2f})')
        for r in top[:6]: print(f'   {r["score"]:.2f}  {r["lat"]:8.2f} {r["lon"]:9.2f}  slope_p50 {r["slope_p50"]:5.1f}  nightmin {r["t_night_min"]}  dark {r["dark_h"]:.0f}h')
json.dump(out, open("data/out/search_top.json", "w"), indent=1)
