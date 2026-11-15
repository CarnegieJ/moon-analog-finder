"""Numbers for the three site briefs: factor-by-factor comparison with lunar regions, monthly light and temperature calendar."""
import json, glob, sys, os, math, numpy as np
from pyhdf.SD import SD
sys.path.insert(0, os.path.dirname(__file__))
import lib_score as ls
SITES = {"East Greenland (Andree Land area)": (73.95, -25.18), "South-east Pamir, Tajikistan": (37.32, 73.11), "Tarso Tousside, Tibesti, Chad": (21.05, 16.45)}
L = ls.load(); moon = json.load(open("data/out/moon_profiles.json")); grid = json.load(open("data/out/moon_grid.json"))
land = [g for g in grid if g["lat"] <= -84 and g["psr_share"] < 0.15 and g["illum_mean"] > 0.25 and g["t_avg"] is not None]
lst = sorted(glob.glob("data/modis/lst/*.hdf")); vi = sorted(glob.glob("data/modis/ndvi/*.hdf"))
def cellidx(la, lo): return min(int((90 - la) / 0.05), 3599), min(int((lo + 180) / 0.05), 7199)
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(); out = {}
for name, (la, lo) in SITES.items():
    i = int(np.argmin((L["lat"] - la) ** 2 + (L["lon"] - lo) ** 2)); Li = {k: v[i:i+1] for k, v in L.items()}
    S = {"lat": float(L["lat"][i]), "lon": float(L["lon"][i]), "earth": {k: round(float(L[k][i]), 2) for k in ("slope_p50", "slope320_p50", "hurst", "relief", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun")}, "vs": {}}
    cls = ls.classes(L["hist"][i]); S["earth"]["share_lt5"], S["earth"]["share_5_10"], S["earth"]["share_10_20"], S["earth"]["share_gt20"] = [round(float(c), 2) for c in cls]
    for t in moon:
        f = ls.foms(Li, t["features"]); m = t["features"]
        S["vs"][t["name"]] = {"terrain_score": round(float(ls.afom(f, "mobility")[0]), 2), "slope_match": round(float(f["slope"][0]), 2), "roughness_across_scales": round(float(f["scale"][0]), 2),
                              "steep_share_match": round(float(f["classes"][0]), 2), "cold": round(float(f["t_cold"][0]), 2), "low_sun": round(float(f["lowsun"][0]), 2), "darkness": round(float(f["dark"][0]), 2),
                              "moon": {"slope_p50": round(m["slope_p50"], 1), "slope320_p50": round(m["slope320_p50"], 1), "hurst": round(m["hurst"], 2), "relief": round(m["relief_m"]), "t_avg": round(m["t_avg"]), "t_max": round(m["t_max"]), "illum_mean": round(m["illum_mean"], 2), "psr_share": round(m["psr_share"], 2)}}
    sc = np.array([float(ls.afom(ls.foms(Li, g), "mobility")[0]) for g in land]); S["landing_like"] = {"n": len(land), "mean": round(float(sc.mean()), 2), "p10": round(float(np.percentile(sc, 10)), 2), "p90": round(float(np.percentile(sc, 90)), 2), "share_ge_0.7": round(float((sc >= 0.7).mean()), 2)}
    allm = np.zeros(len(L["lat"]));  # rank of this window among all windows by mean landing-like score would need a full pass; use Malapert rank instead
    a = ls.afom(ls.foms(L, moon[1]["features"]), "mobility"); S["rank_for_malapert"] = {"rank": int((a > a[i]).sum()) + 1, "of": int(len(a)), "top_percent": round(100 * float((a > a[i]).mean()), 2)}
    r, c = cellidx(S["lat"] + 1e-6, S["lon"] + 1e-6); cal = []
    lmk = np.load("data/cache/landmask.npz"); mdk = np.load("data/cache/modis.npz")
    nb_red = lmk["red_min"][r-1:r+2, c-1:c+2]; nb_day = mdk["day_max"][r-1:r+2, c-1:c+2]
    S["neighbourhood_3x3"] = {"cells_bright_all_year(red_min>0.3)": int(np.nansum(nb_red > 0.3)), "cells_never_above_275K": int(np.nansum(nb_day < 275)), "red_min_range": [round(float(np.nanmin(nb_red)), 2), round(float(np.nanmax(nb_red)), 2)]}
    for mi in range(12):
        h = SD(lst[mi]); d = float(h.select("LST_Day_CMG")[r:r+1, c:c+1][0][0]) * 0.02; n = float(h.select("LST_Night_CMG")[r:r+1, c:c+1][0][0]) * 0.02
        v = SD(vi[mi]); red = float(v.select("CMG 0.05 Deg Monthly red reflectance")[r:r+1, c:c+1][0][0]) * 1e-4; nd = float(v.select("CMG 0.05 Deg Monthly NDVI")[r:r+1, c:c+1][0][0]) * 1e-4
        doy = 15 + 30.4 * mi; dec = -23.44 * math.cos(2 * math.pi * (doy + 10) / 365); el = [math.degrees(math.asin(math.sin(math.radians(la)) * math.sin(math.radians(dec)) + math.cos(math.radians(la)) * math.cos(math.radians(dec)) * math.cos(math.radians(15 * (hh - 12))))) for hh in np.arange(0, 24, 0.1)]
        el = np.array(el); cal.append({"month": MON[mi], "day_K": round(d) if d > 0 else None, "night_K": round(n) if n > 0 else None, "red": round(red, 2) if red >= 0 else None, "ndvi": round(nd, 2) if nd > -0.2 else None,
                                       "sun_max_deg": round(float(el.max()), 1), "daylight_h": round(float((el > 0).mean() * 24), 1), "hours_sun_0_to_12deg": round(float(((el > 0) & (el < 12)).mean() * 24), 1)})
    S["calendar"] = cal; out[name] = S
json.dump(out, open("data/out/site_numbers.json", "w"), indent=1)
for n, S in out.items():
    print("\n##", n, S["lat"], S["lon"]); print("  earth:", S["earth"]); print("  neighbourhood:", S["neighbourhood_3x3"]); print("  landing-like:", S["landing_like"], "| Malapert rank:", S["rank_for_malapert"])
    for k, v in S["vs"].items(): print("  vs", k, {x: y for x, y in v.items() if x != "moon"})
    print("  " + " | ".join(f'{c["month"]} d{c["day_K"]} n{c["night_K"]} red{c["red"]} sun{c["sun_max_deg"]} low{c["hours_sun_0_to_12deg"]}h' for c in S["calendar"]))
print("\nMOON:", {t["name"]: out[list(out)[0]]["vs"][t["name"]]["moon"] for t in moon})
