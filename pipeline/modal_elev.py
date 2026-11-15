"""Mean ground elevation for every map square, so the library can carry altitude and the search can exclude sites that are too high.
Each worker downloads one Copernicus 90 m tile and returns it averaged down to 120 x 120 cells (about 1 km). Results: data/out/elev/NAME.npy.
Run from the project folder:  modal run pipeline/modal_elev.py      (resumable)"""
import os
import modal
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-elev")
image = modal.Image.debian_slim(python_version="3.11").pip_install("numpy", "rasterio", "requests")

@app.function(image=image, timeout=300, retries=2, max_containers=60)
def tile_elev(name: str):
    import io, numpy as np, requests
    from rasterio.io import MemoryFile
    from rasterio.enums import Resampling
    r = requests.get(f"https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif", timeout=120)
    if r.status_code != 200: return name, None
    with MemoryFile(r.content) as mf, mf.open() as ds:
        a = ds.read(1, out_shape=(120, 120), resampling=Resampling.average).astype("float32")
    buf = io.BytesIO(); np.save(buf, a.astype("float16")); return name, buf.getvalue()

@app.local_entrypoint()
def main(limit: int = 0):
    out = os.path.join(ROOT, "data", "out", "elev"); os.makedirs(out, exist_ok=True)
    names = sorted({l.split()[0] for l in open(os.path.join(ROOT, "data", "tiles_v2.txt")) if l.strip()})
    # neighbours to the east, south and south-east too: squares that cross a tile edge have their centre there
    def nb(n, dla, dlo):
        p = n.split("_"); la = int(p[4][1:]) * (1 if p[4][0] == "N" else -1) + dla; lo = (int(p[6][1:]) * (1 if p[6][0] == "E" else -1) + dlo + 180) % 360 - 180
        return f"Copernicus_DSM_COG_30_{'N' if la >= 0 else 'S'}{abs(la):02d}_00_{'E' if lo >= 0 else 'W'}{abs(lo):03d}_00_DEM"
    names = sorted(set(names) | {nb(n, a, b) for n in names for a, b in ((0, 1), (-1, 0), (-1, 1))})
    todo = [n for n in names if not os.path.exists(os.path.join(out, n + ".npy"))]
    if limit: todo = todo[:limit]
    print(f"{len(names)} tiles listed, {len(todo)} to fetch"); done = miss = 0
    for res in tile_elev.map(todo, return_exceptions=True, order_outputs=False):
        if isinstance(res, Exception): print("  failed:", str(res)[:100]); continue
        name, blob = res
        if blob is None: miss += 1; blob = b""
        open(os.path.join(out, name + ".npy"), "wb").write(blob); done += 1
        if done % 500 == 0: print(f"  {done}/{len(todo)}")
    print(f"Done: {done} tiles ({miss} are open sea or not published)")
