"""Full bare-Earth scan on Modal, version 3: overlapping squares. Same data and features as version 2, but the 10 km square is placed
every 2.5 km instead of every 10 km, so a good match is no longer missed or under-scored because it straddles two squares.
(Measured on 64 map squares: moving a square by 2.5 km changes the rover-terrain score by 0.06 on average.)
Squares still do not cross the edge of a 1-degree map tile. Results: one compact .npz per map square in data/out/search_v3/.
Run from the project folder:  modal run pipeline/modal_scan_v3.py      (resumable: tiles already scanned are skipped)"""
import json, os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-scan-v3")
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
    if r.status_code != 200: return name, None, 0            # square is open sea or not published
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
    rows = []; hist = []
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
        pos = lambda n: [int(round(k * NW / 4)) for k in range(4 * n) if int(round(k * NW / 4)) + NW <= n * NW]      # every 2.5 km; includes the old 10 km grid
        for r0 in pos(ny):
            for c0 in pos(nx):
                d = dst[r0:r0+NW, c0:c0+NW]
                if np.isfinite(d).mean() < 0.98: continue
                x = (-W / 2 + c0 + NW / 2) * RES; y = (H / 2 - r0 - NW / 2) * RES; lon, lat = tf.transform(x, y)
                i, j = min(int((90 - lat) / 0.05), 3599), min(int((lon + 180) / 0.05), 7199)
                if not nomask and not g["bare"][i, j]: continue
                d = np.where(np.isfinite(d), d, np.nanmean(d)).astype("float64"); f, _ = features(d, RES)
                if f["relief_m"] < 2: continue
                hist.append(np.round(np.array(f["slope_hist"]) * 10000).astype("uint16"))
                tv = lambda k: (None if not np.isfinite(g[k][i, j]) else float(g[k][i, j]))
                nan = lambda v: np.nan if v is None else v
                rows.append([lat, lon, f["tri_p50"], f["tri_p90"], f["relief_m"], f["slope_p50"], nan(tv("ndvi")), nan(tv("day_max")), nan(tv("night_min")), s["dark_longest_h"], s["lowsun_share"],
                             f["hurst"], f["slope320_p50"], float(nomask), f["slope_p10"], f["slope_p90"], f["slope320_p90"], f["rms_80"], f["rms_1280"], float(r0 % NW == 0 and c0 % NW == 0)])
    buf = io.BytesIO(); np.savez_compressed(buf, s=np.array(rows, "float32").reshape(-1, 20), hist=np.array(hist, "uint16").reshape(-1, 46)); return name, buf.getvalue(), len(rows)

@app.local_entrypoint()
def main(limit: int = 0):
    out = os.path.join(ROOT, "data", "out", "search_v3"); os.makedirs(out, exist_ok=True)
    names = [l.strip() for l in open(os.path.join(ROOT, "data", "tiles_v2.txt")) if l.strip()]
    todo = [n for n in names if not os.path.exists(os.path.join(out, n.split()[0] + ".npz"))]
    if limit: todo = todo[:limit]
    print(f"{len(names)} squares listed, {len(todo)} to scan")
    done = wins = miss = 0
    for res in scan_tile.map(todo, return_exceptions=True, order_outputs=False):
        if isinstance(res, Exception): print("  failed:", str(res)[:100]); continue
        name, blob, n = res
        if blob is None: miss += 1; blob = b""
        open(os.path.join(out, name + ".npz"), "wb").write(blob); done += 1; wins += n
        if done % 100 == 0: print(f"  {done}/{len(todo)} squares, {wins} windows")
    print(f"Done: {done} squares scanned ({miss} had no data), {wins} new windows")
