"""Gate the stage 1 shortlist: novelty (distance to known analog sites), ice/snow proxy, stage 2 support, and scores for named lunar regions."""
import json, csv, sys, os, glob, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
L = ls.load(); md = np.load("data/cache/modis.npz"); lm = np.load("data/cache/landmask.npz"); RE = 6371.0
day_max, red_min, night_min = md["day_max"], lm["red_min"], md["night_min"]
def cell(g, la, lo): return float(g[min(int((90 - la) / 0.05), 3599), min(int((lo + 180) / 0.05), 7199)])
def hav(a, b, c, d): a, b, c, d = map(np.radians, (a, b, c, d)); return 2 * RE * np.arcsin(np.sqrt(np.sin((c - a) / 2) ** 2 + np.cos(a) * np.cos(c) * np.sin((d - b) / 2) ** 2))
known = list(csv.DictReader(open("pipeline/known_sites.csv")))
areas = [a for a in json.load(open("data/zoom_areas.json")) if a["group"] == "shortlist"]
moon = {t["name"]: t["features"] for t in json.load(open("data/out/moon_profiles.json"))}
z = json.load(open("data/out/zoom_benchmark.json")) if os.path.exists("data/out/zoom_benchmark.json") else None
rows = []
for a in areas:
    la, lo = a["lat"], a["lon"]; i = int(np.argmin((L["lat"] - la) ** 2 + (L["lon"] - lo) ** 2))
    d = [hav(la, lo, float(k["lat"]), float(k["lon"])) for k in known]; j = int(np.argmin(d))
    dm, rm = cell(day_max, la, lo), cell(red_min, la, lo)
    Li = {k: v[i:i+1] for k, v in L.items()}; sc = {n: float(ls.afom(ls.foms(Li, f), "mobility")[0]) for n, f in moon.items()}
    rows.append({"id": a["id"], "lat": round(la, 2), "lon": round(lo, 2), "mean_score": a["stage1_mean_score"], "km_known": round(d[j]), "nearest_known": known[j]["name"],
                 "warmest_month_K": round(dm, 1), "red_min": round(rm, 2), "coldest_month_night_K": round(cell(night_min, la, lo), 1),
                 "ice_flag": bool(dm < 275 or rm > 0.30), "median_slope": round(float(L["slope_p50"][i]), 1), "hurst": round(float(L["hurst"][i]), 2),
                 **{"s_" + n.split()[0]: round(v, 2) for n, v in sc.items()}})
json.dump(rows, open("data/out/shortlist_gated.json", "w"), indent=1)
ok = [r for r in rows if not r["ice_flag"] and r["km_known"] > 300]
print("shortlist 200 -> ice-flagged:", sum(r["ice_flag"] for r in rows), "| within 300 km of a known site:", sum(r["km_known"] <= 300 for r in rows), "| passing both:", len(ok))
def region(r):
    la, lo = r["lat"], r["lon"]
    if la > 78 and -45 < lo < -10: return "North / Northeast Greenland"
    if la > 60 and -60 < lo < -10: return "East / West Greenland"
    if la > 76 and -100 < lo <= -60: return "Ellesmere / Axel Heiberg"
    if 60 < la <= 76 and -100 < lo <= -60: return "Baffin Island / Canadian Arctic"
    if la > 60 and lo > 0: return "Eurasian Arctic"
    if la > 60: return "Other Arctic"
    if la < -40: return "Patagonia / sub-Antarctic"
    if -35 < la < -15 and -75 < lo < -60: return "Central Andes"
    if 25 < la < 45 and 60 < lo < 105: return "High Asia"
    return "Other"
by = {}
for r in ok: by.setdefault(region(r), []).append(r)
for k, v in sorted(by.items(), key=lambda z: -len(z[1])):
    v.sort(key=lambda r: -r["mean_score"]); b = v[0]
    print(f'\n{k}: {len(v)} areas. Best: {b["lat"]}, {b["lon"]}  mean {b["mean_score"]}  slope {b["median_slope"]} deg  Hurst {b["hurst"]}  warmest month {b["warmest_month_K"]} K  red_min {b["red_min"]}  {b["km_known"]} km from {b["nearest_known"][:24]}')
    print("   scores for Haworth / Malapert / de Gerlache:", b["s_Haworth"], b["s_Malapert"], b["s_de"])
flag = [r for r in rows if r["ice_flag"]]; print("\nice-flagged examples:", [(r["lat"], r["lon"], r["warmest_month_K"], r["red_min"]) for r in flag[:6]])
