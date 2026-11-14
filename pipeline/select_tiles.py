"""Choose 1x1 degree Earth tiles for the wider search: bare, snow-free land, spread across the globe, all polar deserts included.
Uses only NASA MODIS data already on disk (vegetation index, red reflectance, land fraction)."""
import glob, os, json, numpy as np
from pyhdf.SD import SD
rng = np.random.default_rng(42)
c = "data/cache/landmask.npz"
if not os.path.exists(c):
    land = SD(sorted(glob.glob("data/modis/lst/*.hdf"))[0]).select("Percent_land_in_grid")[:].astype("float32")
    red_min = None
    for f in sorted(glob.glob("data/modis/ndvi/*.hdf")):
        r = SD(f).select("CMG 0.05 Deg Monthly red reflectance")[:].astype("float32"); r[r < 0] = np.nan; r *= 1e-4
        red_min = r if red_min is None else np.fmin(red_min, r)
    np.savez_compressed(c, land=land, red_min=red_min)
m = np.load(c); md = np.load("data/cache/modis.npz")
nd = md["ndvi_max"]
bare = (m["land"] >= 90) & np.isfinite(nd) & (nd <= 0.20) & (m["red_min"] < 0.40)      # bare ground, not permanent snow or ice
print("bare cells:", int(bare.sum()), "of land cells", int((m["land"] >= 90).sum()))
# fraction of bare cells per 1-degree tile (20x20 cells)
frac = bare.reshape(180, 20, 360, 20).mean(axis=(1, 3))          # row 0 = 89..90 N
tiles = []
for i in range(180):
    for j in range(360):
        if frac[i, j] >= 0.5: tiles.append((89 - i, j - 180, float(frac[i, j])))
print("tiles with >= 50% bare land:", len(tiles))
polar = [t for t in tiles if abs(t[0]) >= 66]
rest = [t for t in tiles if abs(t[0]) < 66]
# spread: at most K tiles per 10x10 degree block
K, blocks, pick = 6, {}, []
for t in rest: blocks.setdefault((t[0] // 10, t[1] // 10), []).append(t)
for b, ts in blocks.items():
    idx = rng.permutation(len(ts))[:K]; pick += [ts[k] for k in idx]
sel = polar + pick
json.dump([{"lat": a, "lon": b, "bare": round(f, 2)} for a, b, f in sel], open("data/tiles_search.json", "w"))
name = lambda la, lo: f"Copernicus_DSM_COG_30_{'N' if la>=0 else 'S'}{abs(la):02d}_00_{'E' if lo>=0 else 'W'}{abs(lo):03d}_00_DEM"
open("data/tiles_search.txt", "w").write("\n".join(name(a, b) for a, b, _ in sel))
print("selected:", len(sel), "(polar", len(polar), ", elsewhere", len(pick), "from", len(blocks), "blocks)")
import collections
print("by latitude band:", sorted(collections.Counter((a // 20) * 20 for a, _, _ in sel).items()))
