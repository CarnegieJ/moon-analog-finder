"""Collect every scanned Earth window into one compact library (arrays), for fast scoring and for the app."""
import json, glob, numpy as np
H, S = [], []
for f in glob.glob("data/out/search/*.json"):
    for r in json.load(open(f)):
        H.append(r["slope_hist"])
        S.append([r["lat"], r["lon"], r["tri_p50"], r["tri_p90"], r["relief_m"], r["slope_p50"], r["ndvi_max"] if r["ndvi_max"] is not None else np.nan,
                  r["t_day_max"] or np.nan, r["t_night_min"] or np.nan, r["dark_longest_h"], r["lowsun_share"]])
H = np.array(H, "float32") / 10000; S = np.array(S, "float32")
np.savez_compressed("data/cache/library.npz", hist=H, s=S, cols=np.array(["lat", "lon", "tri_p50", "tri_p90", "relief", "slope_p50", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun"]))
print("library windows:", len(S), " lat range", S[:, 0].min(), S[:, 0].max())
