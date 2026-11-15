"""Supplement to scan version 3: squares that cross the edge of a 1-degree map tile.
Version 3 places 10 km squares every 2.5 km inside each tile. This run adds the squares that start in a tile and reach into its east,
south or south-east neighbour, so a match lying across a tile edge is not missed. Results: data/out/search_v3_edges/.
Run from the project folder:  modal run pipeline/modal_scan_v3_edges.py      (resumable)"""
import json, os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-scan-v3-edges")
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
        W, H = nx * NW, ny * NW; WE, HE = W + NW, H + NW; dst = np.full((HE, WE), np.nan, "float32"); T = from_origin(-W * RES / 2, H * RES / 2, RES, RES)   # same grid as version 3, extended 10 km east and south
        reproject(a, dst, src_transform=ds.transform, src_crs=ds.crs, dst_transform=T, dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
        la, lo = int(round(b.bottom)), int(round(b.left))
        def nb(la2, lo2):
            lo2 = (lo2 + 180) % 360 - 180
            return f"Copernicus_DSM_COG_30_{'N' if la2 >= 0 else 'S'}{abs(la2):02d}_00_{'E' if lo2 >= 0 else 'W'}{abs(lo2):03d}_00_DEM"
        for n2 in (nb(la, lo + 1), nb(la - 1, lo), nb(la - 1, lo + 1)):
            r2 = requests.get(f"https://copernicus-dem-90m.s3.amazonaws.com/{n2}/{n2}.tif", timeout=120)
            if r2.status_code != 200: continue
            with MemoryFile(r2.content) as mf2, mf2.open() as d2:
                tmp = np.full((HE, WE), np.nan, "float32")
                reproject(d2.read(1).astype("float32"), tmp, src_transform=d2.transform, src_crs=d2.crs, dst_transform=T, dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
                dst = np.where(np.isfinite(dst), dst, tmp)
        tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True); s = sun(round(lat0 * 2) / 2)
        pos = lambda n: [int(round(k * NW / 4)) for k in range(4 * n + 4) if int(round(k * NW / 4)) < n * NW]      # every 2.5 km, now allowed to run past the tile edge
        for r0 in pos(ny):
            for c0 in pos(nx):
                if r0 + NW <= H and c0 + NW <= W: continue          # fully inside the tile: already in version 3
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
    out = os.path.join(ROOT, "data", "out", "search_v3_edges"); os.makedirs(out, exist_ok=True)
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
