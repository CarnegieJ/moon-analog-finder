"""Write compact binary data files for the browser app (app/data)."""
import json, csv, numpy as np, rasterio
from rasterio.enums import Resampling
z = np.load("data/cache/library_v2.npz"); s = z["s"]; c = {k: s[:, i] for i, k in enumerate(z["cols"])}; c["pzi"] = np.load("data/cache/pzi.npy")   # pipeline/permafrost.py
q = lambda h: np.clip(np.round(h * 255), 0, 255).astype("uint8")
np.round(z["hist"].astype("float64") * 10000).astype("uint16").tofile("app/data/earth_hist16.bin")   # full precision (rounding to 256 levels moved scores by up to 0.02)
ecols = ["lat", "lon", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun", "slope_p50", "relief", "hurst", "slope320_p50", "nomask", "pzi"]
np.stack([c[k] for k in ecols], 1).astype("float32").tofile("app/data/earth_meta.bin")
g = json.load(open("data/out/moon_grid.json"))
np.round(np.array([r["slope_hist"] for r in g], "float64") * 10000).astype("uint16").tofile("app/data/moon_hist16.bin")   # full precision, used by the app
mcols = ["x", "y", "lat", "lon", "hurst", "slope320_p50", "psr_share", "illum_mean", "illum_max", "t_avg", "t_max", "slope_p50", "relief_m", "ice_share", "slope_p90"]
np.array([[np.nan if r[k] is None else r[k] for k in mcols] for r in g], "float32").tofile("app/data/moon_meta.bin")
dem = rasterio.open("data/moon/LDEM_80S_80MPP_ADJ.TIF").read(1, out_shape=(1520, 1520), resampling=Resampling.average)
np.nan_to_num(dem).round().astype("int16").tofile("app/data/moon_dem400.bin")
dem2 = rasterio.open("data/moon/LDEM_80S_80MPP_ADJ.TIF").read(1, out_shape=(3040, 3040), resampling=Resampling.average)
np.nan_to_num(dem2).round().astype("int16").tofile("app/data/moon_dem200.bin")
known = [{"name": r["name"], "lat": float(r["lat"]), "lon": float(r["lon"]), "why": r["use"], "source": r["use_source"]} for r in csv.DictReader(open("pipeline/known_sites.csv")) if r["status"].startswith("verified")]
regions = [{"name": t["name"], "lat": t["lat"], "lon": t["lon"], "x": t["x"], "y": t["y"], "note": t["note"], "kind": t.get("kind", "artemis")} for t in json.load(open("data/out/moon_profiles.json"))]   # kind: "artemis" for the nine NASA candidate regions
# Real landed spacecraft at the south pole: coordinates from NASA NSSDC "Lunar Artifact Impacts and Landings" table (checked Nov 15, 2026)
import math
for nm, la, lo in (("IM-2 lander (2025)", -84.7906, 29.1957), ("IM-1 Odysseus lander (2024)", -80.13, 1.44)):
    r = 2 * 1737400.0 * math.tan(math.radians(90 + la) / 2); x, y = r * math.sin(math.radians(lo)), r * math.cos(math.radians(lo))
    if math.hypot(round(x / 5000) * 5000, round(y / 5000) * 5000) <= 299000:
        regions.append({"name": nm, "lat": la, "lon": lo, "x": x, "y": y, "note": "NASA NSSDC coordinates", "cited": True, "kind": "lander"})
json.dump({"earth": {"n": len(s), "cols": ecols, "bins": 46}, "moon": {"n": len(g), "cols": mcols, "bins": 46, "step_m": 5000, "dem": {"n": 1520, "res_m": 400, "half_m": 304000}, "dem200": {"n": 3040, "res_m": 200, "half_m": 304000}},
           "known": known, "regions": regions, "squares_scanned": 4242}, open("app/data/manifest.json", "w"))
print("earth", len(s), "moon", len(g))
