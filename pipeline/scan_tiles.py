"""Wider search: cut every downloaded Earth tile into 10 km windows on an 80 m grid and compute the same features as for the Moon.
Resumable: one output file per tile. Stops itself after TIME_BUDGET seconds so it can be called repeatedly."""
import json, os, sys, time, math, glob, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(__file__))
from terrain import features
from phase3 import sun_stats  # noqa (import runs nothing heavy? guarded below)
TIME_BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 150
RES, NW = 80.0, 125
_md = np.load("data/cache/modis.npz"); _lm = np.load("data/cache/landmask.npz")
md = {k: _md[k] for k in ("ndvi_max", "day_max", "night_min")}; lm = {k: _lm[k] for k in ("land", "red_min")}
def cell(g, lat, lon):
    i, j = min(int((90 - lat) / 0.05), 3599), min(int((lon + 180) / 0.05), 7199); v = g[i, j]
    return None if not np.isfinite(v) else float(v)
sun_cache = {}
def sun(lat):
    k = round(lat * 2) / 2
    if k not in sun_cache: sun_cache[k] = sun_stats(k, 12.0)
    return sun_cache[k]
t0 = time.time(); done = 0
names = [l.strip() for l in open("data/tiles_search.txt") if l.strip()]
for n in names:
    out = f"data/out/search/{n}.json"; src = f"data/earth/{n}.tif"
    if os.path.exists(out) or not os.path.exists(src): continue
    if time.time() - t0 > TIME_BUDGET: break
    rows = []
    try:
        ds = rasterio.open(src); a = ds.read(1).astype("float32"); b = ds.bounds
        lat0, lon0 = (b.top + b.bottom) / 2, (b.left + b.right) / 2
        hy = 111320 / 2; hx = 111320 * math.cos(math.radians(lat0)) / 2
        ny, nx = int(2 * hy / RES) // NW, max(int(2 * hx / RES) // NW, 1)
        crs = CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m")
        W, H = nx * NW, ny * NW; dst = np.full((H, W), np.nan, "float32")
        reproject(a, dst, src_transform=ds.transform, src_crs=ds.crs, dst_transform=from_origin(-W * RES / 2, H * RES / 2, RES, RES), dst_crs=crs,
                  resampling=Resampling.bilinear, dst_nodata=np.nan)
        tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        for iy in range(ny):
            for ix in range(nx):
                d = dst[iy*NW:(iy+1)*NW, ix*NW:(ix+1)*NW]
                if np.isfinite(d).mean() < 0.98: continue
                x = (-W / 2 + (ix + 0.5) * NW) * RES; y = (H / 2 - (iy + 0.5) * NW) * RES; lon, lat = tf.transform(x, y)
                i, j = min(int((90 - lat) / 0.05), 3599), min(int((lon + 180) / 0.05), 7199)
                nd = md["ndvi_max"][i, j]
                if lm["land"][i, j] < 90 or not np.isfinite(nd) or nd > 0.2 or not (lm["red_min"][i, j] < 0.4): continue   # bare, snow-free land only
                d = np.where(np.isfinite(d), d, np.nanmean(d)).astype("float64"); f, _ = features(d, RES)
                if f["relief_m"] < 2: continue                                                                      # flattened water surface
                f["slope_hist"] = [int(round(v * 10000)) for v in f["slope_hist"]]
                f.update({"lat": round(lat, 3), "lon": round(lon, 3), "ndvi_max": float(nd), "t_day_max": cell(md["day_max"], lat, lon),
                          "t_night_min": cell(md["night_min"], lat, lon), **sun(lat)})
                rows.append({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})
    except Exception as e:
        print("skip", n, str(e)[:80])
    json.dump(rows, open(out, "w")); done += 1
left = sum(1 for n in names if os.path.exists(f"data/earth/{n}.tif") and not os.path.exists(f"data/out/search/{n}.json"))
tot = sum(len(json.load(open(f))) for f in glob.glob("data/out/search/*.json"))
print(f"tiles this run: {done}, tiles left: {left}, windows so far: {tot}, {time.time()-t0:.0f}s")
