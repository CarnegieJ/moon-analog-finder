"""Write compact binary data files for the browser app (app/data)."""
import json, csv, numpy as np, rasterio
from rasterio.enums import Resampling
z = np.load("data/cache/library_v2.npz"); s = z["s"]; c = {k: s[:, i] for i, k in enumerate(z["cols"])}
q = lambda h: np.clip(np.round(h * 255), 0, 255).astype("uint8")
q(z["hist"]).tofile("app/data/earth_hist.bin")
ecols = ["lat", "lon", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun", "slope_p50", "relief", "hurst", "slope320_p50", "nomask"]
np.stack([c[k] for k in ecols], 1).astype("float32").tofile("app/data/earth_meta.bin")
g = json.load(open("data/out/moon_grid.json"))
q(np.array([r["slope_hist"] for r in g], "float32")).tofile("app/data/moon_hist.bin")
mcols = ["x", "y", "lat", "lon", "hurst", "slope320_p50", "psr_share", "illum_mean", "illum_max", "t_avg", "t_max", "slope_p50", "relief_m", "ice_share", "slope_p90"]
np.array([[np.nan if r[k] is None else r[k] for k in mcols] for r in g], "float32").tofile("app/data/moon_meta.bin")
dem = rasterio.open("data/moon/LDEM_80S_80MPP_ADJ.TIF").read(1, out_shape=(1520, 1520), resampling=Resampling.average)
np.nan_to_num(dem).round().astype("int16").tofile("app/data/moon_dem400.bin")
known = [{"name": r["name"], "lat": float(r["lat"]), "lon": float(r["lon"]), "why": r["use"], "source": r["use_source"]} for r in csv.DictReader(open("pipeline/known_sites.csv")) if r["status"].startswith("verified")]
regions = [{"name": t["name"], "lat": t["lat"], "lon": t["lon"], "x": t["x"], "y": t["y"], "note": t["note"]} for t in json.load(open("data/out/moon_profiles.json"))]
json.dump({"earth": {"n": len(s), "cols": ecols, "bins": 46}, "moon": {"n": len(g), "cols": mcols, "bins": 46, "step_m": 5000, "dem": {"n": 1520, "res_m": 400, "half_m": 304000}},
           "known": known, "regions": regions, "squares_scanned": 4242}, open("app/data/manifest.json", "w"))
print("earth", len(s), "moon", len(g))
