"""Full bare-Earth scan on Modal, version 2 (multi-scale roughness, looser vegetation cut-off, Antarctic ice-free areas). Each cloud worker downloads one Copernicus DEM tile (open data on AWS), cuts it into
10 km windows on an 80 m grid and computes the same features as the lunar side. Results are written to data/out/search/.
Run from the project folder:  modal run pipeline/modal_scan_v2.py      (resumable: tiles already scanned are skipped)"""
import json, os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-scan-v2")
image = modal.Image.debian_slim(python_version="3.11").pip_install("numpy", "rasterio", "pyproj", "requests")
if modal.is_local():   # local files are attached only when launching from the project folder
    image = (image.add_local_file(os.path.join(HERE, "terrain.py"), "/root/terrain.py")
                  .add_local_file(os.path.join(ROOT, "data", "cache", "modal_grids_v2.npz"), "/root/modal_grids.npz"))
_G = None

@app.function(image=image, timeout=600, retries=2, max_containers=60)
def scan_tile(item: str):
    name, nomask = (item.split()[0], item.endswith(" nomask"))
    import io, math, sys, numpy as np, requests, rasterio
    from rasterio.io import MemoryFile
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
    from pyproj import Transformer
    sys.path.insert(0, "/root")
    from terrain import features
    global _G
    if _G is None:
        z = np.load("/root/modal_grids.npz"); _G = {k: z[k] for k in z.files}
    g = _G
    r = requests.get(f"https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif", timeout=120)
    if r.status_code != 200: return name, None            # square is open sea or not published
    RES, NW = 80.0, 125
    def sun(lat):
        phi = math.radians(lat); doy = np.arange(365)[:, None]; h = np.arange(0, 24, 0.25)[None, :]
        dec = np.radians(-23.44 * np.cos(2 * np.pi * (doy + 10) / 365)); ha = np.radians(15 * (h - 12))
        el = np.degrees(np.arcsin(np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.cos(ha))).ravel(); up = el > 0
        d = np.concatenate([~up, ~up]).astype(int); best = run = 0
        for v in d:
            run = run + 1 if v else 0; best = max(best, run)
        return {"sun_max_elev": float(el.max()), "dark_longest_h": float(min(best, el.size) * 0.25),
                "lowsun_share": float(((el > 0) & (el < 12.0)).sum() / max(up.sum(), 1))}
    rows = []
    with MemoryFile(r.content) as mf, mf.open() as ds:
        a = ds.read(1).astype("float32"); b = ds.bounds
        lat0, lon0 = (b.top + b.bottom) / 2, (b.left + b.right) / 2
        hy = 111320 / 2; hx = 111320 * math.cos(math.radians(lat0)) / 2
        ny, nx = int(2 * hy / RES) // NW, max(int(2 * hx / RES) // NW, 1)
        crs = CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m")
        W, H = nx * NW, ny * NW; dst = np.full((H, W), np.nan, "float32")
        reproject(a, dst, src_transform=ds.transform, src_crs=ds.crs, dst_transform=from_origin(-W * RES / 2, H * RES / 2, RES, RES),
                  dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
        tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True); s = sun(round(lat0 * 2) / 2)
        for iy in range(ny):
            for ix in range(nx):
                d = dst[iy*NW:(iy+1)*NW, ix*NW:(ix+1)*NW]
                if np.isfinite(d).mean() < 0.98: continue
                x = (-W / 2 + (ix + 0.5) * NW) * RES; y = (H / 2 - (iy + 0.5) * NW) * RES; lon, lat = tf.transform(x, y)
                i, j = min(int((90 - lat) / 0.05), 3599), min(int((lon + 180) / 0.05), 7199)
                if not nomask and not g["bare"][i, j]: continue
                d = np.where(np.isfinite(d), d, np.nanmean(d)).astype("float64"); f, _ = features(d, RES)
                if f["relief_m"] < 2: continue
                f["slope_hist"] = [int(round(v * 10000)) for v in f["slope_hist"]]
                tv = lambda k: (None if not np.isfinite(g[k][i, j]) else float(g[k][i, j]))
                f.update({"lat": round(lat, 3), "lon": round(lon, 3), "ndvi_max": tv("ndvi"), "t_day_max": tv("day_max"), "t_night_min": tv("night_min"), **s})
                if nomask: f["nomask"] = 1
                rows.append({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})
    return name, rows

@app.local_entrypoint()
def main(limit: int = 0):
    out = os.path.join(ROOT, "data", "out", "search_v2"); os.makedirs(out, exist_ok=True)
    names = [l.strip() for l in open(os.path.join(ROOT, "data", "tiles_v2.txt")) if l.strip()]
    todo = [n for n in names if not os.path.exists(os.path.join(out, n.split()[0] + ".json"))]
    if limit: todo = todo[:limit]
    print(f"{len(names)} squares listed, {len(todo)} to scan")
    done = wins = miss = 0
    for res in scan_tile.map(todo, return_exceptions=True, order_outputs=False):
        if isinstance(res, Exception): print("  failed:", str(res)[:100]); continue
        name, rows = res
        if rows is None: miss += 1; rows = []
        json.dump(rows, open(os.path.join(out, name + ".json"), "w")); done += 1; wins += len(rows)
        if done % 100 == 0: print(f"  {done}/{len(todo)} squares, {wins} windows")
    print(f"Done: {done} squares scanned ({miss} had no data), {wins} new windows")
