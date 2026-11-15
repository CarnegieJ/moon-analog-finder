"""Experiment: does it matter where the 10 km square is placed on Earth?
For local Copernicus tiles, compute the same terrain features for squares shifted in 2.5 km steps (the library uses 10 km steps, no overlap).
Usage: python pipeline/overlap_test.py START COUNT   -> one npz per tile in data/cache/overlap/"""
import sys, os, glob, math, time, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
sys.path.insert(0, "pipeline"); from terrain import features
RES, NW, ST = 80.0, 125, 31
tiles = sorted(glob.glob("data/earth/*_DEM.tif")); rng = np.random.default_rng(7); tiles = [tiles[i] for i in rng.permutation(len(tiles))]
t0 = time.time()
for p in tiles[int(sys.argv[1]):int(sys.argv[1]) + int(sys.argv[2])]:
    out = "data/cache/overlap/" + os.path.basename(p)[:-4] + ".npz"
    if os.path.exists(out): continue
    if time.time() - t0 > 120: break
    with rasterio.open(p) as ds:
        a = ds.read(1).astype("float32"); b = ds.bounds; lat0, lon0 = (b.top + b.bottom) / 2, (b.left + b.right) / 2
        hy = 111320 / 2; hx = 111320 * math.cos(math.radians(lat0)) / 2; ny, nx = int(2 * hy / RES) // NW, max(int(2 * hx / RES) // NW, 1)
        crs = CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m"); W, H = nx * NW, ny * NW; dst = np.full((H, W), np.nan, "float32")
        reproject(a, dst, src_transform=ds.transform, src_crs=ds.crs, dst_transform=from_origin(-W * RES / 2, H * RES / 2, RES, RES), dst_crs=crs, resampling=Resampling.average, dst_nodata=np.nan)
    rows = []
    for r in range(0, H - NW + 1, ST):
        for c in range(0, W - NW + 1, ST):
            d = dst[r:r+NW, c:c+NW]
            if np.isfinite(d).mean() < 0.98: continue
            d = np.where(np.isfinite(d), d, np.nanmean(d)).astype("float64")
            if d.max() - d.min() < 2 or (d == 0).mean() > 0.2: continue       # flat or mostly sea
            f, _ = features(d, RES); rows.append([r, c, f["hurst"], f["slope_p50"], f["slope320_p50"], f["relief_m"]] + list(f["slope_hist"]))
    np.savez_compressed(out, rows=np.array(rows, "float32"), lat0=lat0, lon0=lon0, shape=(H, W)); print(os.path.basename(p), len(rows), round(time.time() - t0), "s", flush=True)
