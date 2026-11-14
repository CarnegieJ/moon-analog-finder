"""Phase 2: terrain features for Earth sites from Copernicus DEM GLO-90, resampled to the lunar grid (80 m, 10 km window)."""
import csv, json, math, os, sys, glob
import numpy as np, rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
from rasterio.io import MemoryFile
sys.path.insert(0, os.path.dirname(__file__))
from terrain import features
RES, WIN_KM = 80.0, 10.0
N = int(WIN_KM * 1000 / RES)

def tile_names(lat, lon, dl=0.08):
    dlo = dl / max(math.cos(math.radians(lat)), 0.05); out = set()
    for la in {math.floor(lat-dl), math.floor(lat+dl)}:
        for lo in {math.floor(lon-dlo), math.floor(lon+dlo)}:
            out.add(f"Copernicus_DSM_COG_30_{'N' if la>=0 else 'S'}{abs(la):02d}_00_{'E' if lo>=0 else 'W'}{abs(lo):03d}_00_DEM.tif")
    return out

def window(lat, lon, folder="data/earth"):
    paths = [os.path.join(folder, t) for t in tile_names(lat, lon) if os.path.exists(os.path.join(folder, t))]
    if not paths: return None
    srcs = []
    for p in paths:  # skip truncated downloads
        try:
            ds = rasterio.open(p); ds.read(1, window=((0, 8), (0, 8))); ds.read(1, out_shape=(8, 8)); srcs.append(ds)
        except Exception: print("  unreadable tile skipped:", os.path.basename(p))
    if not srcs: return None
    mos, tr = merge(srcs)
    dst = np.full((N, N), np.nan, "float32")
    crs = CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    reproject(mos[0].astype("float32"), dst, src_transform=tr, src_crs=srcs[0].crs, dst_transform=from_origin(-WIN_KM*500, WIN_KM*500, RES, RES),
              dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
    return dst

if __name__ == "__main__":
    out = []
    for r in csv.DictReader(open("data/sites_earth.csv")):
        lat, lon = float(r["lat"]), float(r["lon"]); d = window(lat, lon)
        if d is None or np.isfinite(d).mean() < 0.9: print("MISSING DATA:", r["name"]); continue
        f, _ = features(d, RES); f.update({"psr_share": None, "illum_mean": None, "illum_max": None})
        out.append({**r, "lat": lat, "lon": lon, "features": f})
        print(f'{r["name"]:40s} p50 {f["slope_p50"]:5.1f}  >10deg {f["share_10_20"]+f["share_gt20"]:.2f}  tri {f["tri_p50"]:5.1f}  relief {f["relief_m"]:6.0f}')
    json.dump(out, open("data/out/earth_profiles.json", "w"), indent=1)
