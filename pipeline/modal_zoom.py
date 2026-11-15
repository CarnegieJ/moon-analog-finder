"""Stage 2 on Modal: 2 km windows at 30 m for the Earth areas in data/zoom_areas.json.
Each worker downloads the Copernicus DEM GLO-30 tiles covering one area, reprojects them to a 30 m grid centred on the area,
cuts 2 km windows and computes the same terrain features as stage 1 (same code, terrain.py). Results go to data/out/zoom/.
Run from the project folder:  modal run pipeline/modal_zoom.py     (resumable)"""
import json, os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-zoom")
image = modal.Image.debian_slim(python_version="3.11").pip_install("numpy", "rasterio", "pyproj", "requests")
if modal.is_local():
    image = (image.add_local_file(os.path.join(HERE, "terrain.py"), "/root/terrain.py")
                  .add_local_file(os.path.join(ROOT, "data", "cache", "modal_grids_v2.npz"), "/root/modal_grids.npz"))
_G = None

@app.function(image=image, timeout=900, retries=2, max_containers=60, memory=4096)
def zoom_area(area: dict):
    import math, sys, numpy as np, requests, rasterio
    from rasterio.io import MemoryFile
    from rasterio.merge import merge
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
    from pyproj import Transformer
    sys.path.insert(0, "/root")
    from terrain import features
    global _G
    if _G is None:
        z = np.load("/root/modal_grids.npz"); _G = {k: z[k] for k in z.files}
    g = _G; RES, NW = 30.0, 67                      # 67 px x 30 m = 2.01 km windows
    lat, lon, rad = area["lat"], area["lon"], area["radius_km"]
    dl = rad / 111.0 + 0.02; dlo = dl / max(math.cos(math.radians(lat)), 0.05); names = set()
    for la in range(math.floor(lat - dl), math.floor(lat + dl) + 1):
        for lo in range(math.floor(lon - dlo), math.floor(lon + dlo) + 1):
            lo2 = ((lo + 180) % 360) - 180
            names.add(f"Copernicus_DSM_COG_10_{'N' if la >= 0 else 'S'}{abs(la):02d}_00_{'E' if lo2 >= 0 else 'W'}{abs(lo2):03d}_00_DEM")
    mems, srcs = [], []
    for n in sorted(names):
        r = requests.get(f"https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif", timeout=180)
        if r.status_code == 200:
            mf = MemoryFile(r.content); mems.append(mf); srcs.append(mf.open())
    if not srcs: return area["id"], None
    mos, tr = merge(srcs, bounds=(lon - dlo, lat - dl, lon + dlo, lat + dl))
    n_side = (int(2 * rad * 1000 / RES) // NW) * NW; dst = np.full((n_side, n_side), np.nan, "float32")
    crs = CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    reproject(mos[0].astype("float32"), dst, src_transform=tr, src_crs=srcs[0].crs, dst_transform=from_origin(-n_side * RES / 2, n_side * RES / 2, RES, RES),
              dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
    tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True); rows = []
    for iy in range(n_side // NW):
        for ix in range(n_side // NW):
            d = dst[iy*NW:(iy+1)*NW, ix*NW:(ix+1)*NW]
            if np.isfinite(d).mean() < 0.98: continue
            x = (-n_side / 2 + (ix + 0.5) * NW) * RES; y = (n_side / 2 - (iy + 0.5) * NW) * RES; wlon, wlat = tf.transform(x, y)
            i, j = min(int((90 - wlat) / 0.05), 3599), min(int((wlon + 180) / 0.05), 7199)
            if not area.get("nomask") and not g["bare"][i, j]: continue
            d = np.where(np.isfinite(d), d, np.nanmean(d)).astype("float64"); f, _ = features(d, RES)
            if f["relief_m"] < 1: continue
            f["slope_hist"] = [int(round(v * 10000)) for v in f["slope_hist"]]
            nd = g["ndvi"][i, j]; f.update({"lat": round(wlat, 4), "lon": round(wlon, 4), "ndvi_max": None if not np.isfinite(nd) else float(nd)})
            rows.append({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})
    return area["id"], rows

@app.local_entrypoint()
def main(limit: int = 0):
    out = os.path.join(ROOT, "data", "out", "zoom"); os.makedirs(out, exist_ok=True)
    areas = json.load(open(os.path.join(ROOT, "data", "zoom_areas.json")))
    todo = [a for a in areas if not os.path.exists(os.path.join(out, a["id"] + ".json"))]
    if limit: todo = todo[:limit]
    print(f"{len(areas)} areas listed, {len(todo)} to scan")
    done = wins = miss = 0
    for res in zoom_area.map(todo, return_exceptions=True, order_outputs=False):
        if isinstance(res, Exception): print("  failed:", str(res)[:120]); continue
        aid, rows = res
        if rows is None: miss += 1; rows = []
        json.dump(rows, open(os.path.join(out, aid + ".json"), "w")); done += 1; wins += len(rows)
        if done % 50 == 0: print(f"  {done}/{len(todo)} areas, {wins} windows")
    print(f"Done: {done} areas scanned ({miss} had no elevation data), {wins} windows")
