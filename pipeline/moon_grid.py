"""Lunar spot grid: full-detail (80 m) features for a 10 km window every 5 km across the south polar cap (80-90 S).
Lets the app score ANY clicked spot (snapped to the nearest grid spot, at most ~2.5-3.5 km away)."""
import json, os, sys, numpy as np, rasterio
from rasterio.enums import Resampling
sys.path.insert(0, os.path.dirname(__file__))
from terrain import features
M = "data/moon/"; STEP, HALF, R = 5000.0, 5000.0, 1737400.0
dem = rasterio.open(M + "LDEM_80S_80MPP_ADJ.TIF").read(1)
n80 = dem.shape[0]
psr = rasterio.open(M + "LPSR_80S_20MPP_ADJ.TIF").read(1, out_shape=(n80, n80), resampling=Resampling.average)
ill_ds = rasterio.open(M + "AVGVISIB_75S_120M_201608.TIF"); ill = ill_ds.read(1).astype("float32") * 4e-5; ill[ill < 0] = np.nan
dv = np.load("data/cache/diviner_south.npz")
rr = 2 * R * np.tan(np.radians(90 + dv["lat"]) / 2); dx = rr * np.sin(np.radians(dv["lon"])); dy = rr * np.cos(np.radians(dv["lon"]))
edges = np.arange(-305000, 305001, STEP)
def binsum(w): return np.histogram2d(dx, dy, bins=[edges, edges], weights=w)[0]
cnt = binsum(None); s_avg = binsum(dv["tavg"]); s_max = binsum(dv["tmax"]); ice_ok = (dv["ice"] > -900).astype("float32"); s_ice = binsum(ice_ok)
def win4(a, ix, iy): return a[ix-1:ix+1, iy-1:iy+1].sum()      # 4 bins around a spot = its 10 km window
rows = []
ks = np.arange(-59, 60)
for kx in ks:
    for ky in ks:
        x, y = kx * STEP, ky * STEP; r = np.hypot(x, y)
        if r > 299000: continue
        c0, r0 = int((x - HALF + 304000) / 80), int((304000 - (y + HALF)) / 80)
        if c0 < 0 or r0 < 0 or c0 + 125 > n80 or r0 + 125 > n80: continue
        d = dem[r0:r0+125, c0:c0+125]
        if not np.isfinite(d).all(): continue
        f, _ = features(d.astype("float64"), 80.0)
        ic, ir = int((x - HALF + 457440) / 120), int((457440 - (y + HALF)) / 120); iw = ill[ir:ir+83, ic:ic+83]
        ix, iy = int(round((x + 305000) / STEP)), int(round((y + 305000) / STEP)); n = win4(cnt, ix, iy)
        lat = -90 + np.degrees(2 * np.arctan(r / (2 * R))); lon = np.degrees(np.arctan2(x, y))
        f.update({"x": x, "y": y, "lat": round(float(lat), 3), "lon": round(float(lon), 2), "psr_share": float(np.nanmean(psr[r0:r0+125, c0:c0+125] > 0.5)),
                  "illum_mean": float(np.nanmean(iw)), "illum_max": float(np.nanmax(iw)),
                  "t_avg": float(win4(s_avg, ix, iy) / n) if n else None, "t_max": float(win4(s_max, ix, iy) / n) if n else None,
                  "ice_share": float(win4(s_ice, ix, iy) / n) if n else None, "sun_max_elev": float(90 - abs(lat) + 1.54)})
        rows.append(f)
print("spots:", len(rows))
json.dump(rows, open("data/out/moon_grid.json", "w"))
for k in ("slope_p50", "share_gt20", "psr_share", "illum_mean", "t_avg", "t_max"):
    v = np.array([r[k] for r in rows if r[k] is not None]); print(k, "min %.2f med %.2f max %.2f" % (v.min(), np.median(v), v.max()))
