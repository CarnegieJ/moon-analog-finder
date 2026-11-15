"""Is the Earth-Moon gap in the scaling number (Hurst) real terrain, or a sensor effect?
Radar DEM noise inflates short-distance height differences (lowers H); gridded laser data is smoothed at short distances (raises H).
Test: measure RMS height difference at each distance on both bodies for windows of matched slope, and recompute H from long distances only."""
import os, sys, glob, math, json, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
sys.path.insert(0, os.path.dirname(__file__))
from terrain import horn_slope
rng = np.random.default_rng(5); LAGS = np.array([1, 2, 4, 8, 16, 32]); RES = 80.0
def rms_lags(dem):
    n, m = dem.shape; yy, xx = np.mgrid[0:n, 0:m]; A = np.c_[xx.ravel(), yy.ravel(), np.ones(n * m)]
    d = dem - (A @ np.linalg.lstsq(A, dem.ravel(), rcond=None)[0]).reshape(n, m); out = []
    for l in LAGS:
        a = d[:, l:] - d[:, :-l]; b = d[l:, :] - d[:-l, :]; out.append(np.sqrt((np.sum(a*a) + np.sum(b*b)) / (a.size + b.size)))
    return np.array(out)
def H(v, i0, i1): return float(np.polyfit(np.log(LAGS[i0:i1] * RES), np.log(np.maximum(v[i0:i1], 1e-6)), 1)[0])
rows = []
dem = rasterio.open("data/moon/LDEM_80S_80MPP_ADJ.TIF").read(1)
for _ in range(900):
    r, c = rng.integers(400, 7000, 2); d = dem[r:r+125, c:c+125].astype("float64")
    if np.isfinite(d).all(): rows.append(("moon", float(np.median(horn_slope(d, RES))), rms_lags(d)))
tiles = sorted(glob.glob("data/earth/*.tif")); rng.shuffle(tiles)
for t in tiles[:110]:
    try:
        ds = rasterio.open(t); a = ds.read(1).astype("float32"); b = ds.bounds
    except Exception: continue
    lat0, lon0 = (b.top + b.bottom) / 2, (b.left + b.right) / 2
    hx = 111320 * math.cos(math.radians(lat0)) / 2; ny, nx = 11, max(int(2 * hx / RES) // 125, 1); W, Hh = nx * 125, ny * 125
    dst = np.full((Hh, W), np.nan, "float32")
    reproject(a, dst, src_transform=ds.transform, src_crs=ds.crs, dst_transform=from_origin(-W*RES/2, Hh*RES/2, RES, RES),
              dst_crs=CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m"), resampling=Resampling.bilinear, dst_nodata=np.nan)
    for iy in range(0, ny, 2):
        for ix in range(0, nx, 2):
            d = dst[iy*125:(iy+1)*125, ix*125:(ix+1)*125].astype("float64")
            if np.isfinite(d).all() and np.ptp(d) > 5: rows.append(("earth", float(np.median(horn_slope(d, RES))), rms_lags(d)))
print("windows: moon", sum(r[0] == "moon" for r in rows), "earth", sum(r[0] == "earth" for r in rows))
print("distances (m):", (LAGS * RES).astype(int).tolist())
for lo, hi in ((2, 5), (5, 10), (10, 20)):
    sel = {b: np.array([r[2] for r in rows if r[0] == b and lo <= r[1] < hi]) for b in ("moon", "earth")}
    if min(len(v) for v in sel.values()) < 15: continue
    med = {b: np.median(v, 0) for b, v in sel.items()}
    print(f"\nmedian slope {lo}-{hi} deg  (moon n={len(sel['moon'])}, earth n={len(sel['earth'])})")
    print("  RMS height difference, Earth / Moon ratio at each distance:", np.round(med["earth"] / med["moon"], 2).tolist())
    for name, i0, i1 in (("80 m - 1.28 km (as shipped)", 0, 5), ("320 m - 2.56 km (long only)", 2, 6), ("80 - 320 m (short only)", 0, 3)):
        hm = np.median([H(v, i0, i1) for v in sel["moon"]]); he = np.median([H(v, i0, i1) for v in sel["earth"]])
        print(f"  H over {name:28s} Moon {hm:.2f}  Earth {he:.2f}  gap {hm-he:+.2f}")
