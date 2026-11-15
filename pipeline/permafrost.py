"""Sample the Global Permafrost Zonation Index (Gruber 2012, 30 arc-seconds, 60 S to 90 N) at every Earth library window.
Value per window = mean of a 5 x 5 grid of points across the 10 km window. The 0.01 'fringe of uncertainty' counts as 0. South of 60 S = no data."""
import numpy as np, sys, time
NC, NR, CS = 43200, 18000, 1 / 120
P = np.memmap("data/geo/PZI.flt", dtype="<f4", mode="r", shape=(NR, NC))
LIB3 = len(sys.argv) > 3 and sys.argv[3] == "lib3"      # third argument "lib3": sample the overlapping-square library instead
if LIB3: s = np.load("data/cache/lib3/s.npy", mmap_mode="r"); lat = np.array(s[:, 0], "float64"); lon = np.array(s[:, 1], "float64")
else: z = np.load("data/cache/library_v2.npz"); cols = list(z["cols"]); s = z["s"]; lat = s[:, cols.index("lat")].astype("float64"); lon = s[:, cols.index("lon")].astype("float64")
off = np.linspace(-4, 4, 5) / 111.32; out = np.full(len(lat), np.nan, "float32"); order = np.argsort(-lat); t0 = time.time()
lo, hi = int(sys.argv[1]), int(sys.argv[2]); part = order[lo:hi]
for i0 in range(0, len(part), 4000):
    idx = part[i0:i0 + 4000]; la = lat[idx][:, None, None] + off[None, :, None]; lo_ = lon[idx][:, None, None] + off[None, None, :] / np.cos(np.radians(lat[idx]))[:, None, None]
    r = np.floor((90 - la) / CS).astype(int) + np.zeros_like(lo_, int); c = (np.floor((lo_ + 180) / CS).astype(int) % NC) + np.zeros_like(r)
    ok = (r >= 0) & (r < NR); r0, r1 = max(0, r.min()), min(NR - 1, r.max()); blk = np.asarray(P[r0:r1 + 1]) if r1 >= r0 else None
    v = np.where(ok, blk[np.clip(r, r0, r1) - r0, c] if blk is not None else np.nan, np.nan); v = np.where(v < -100, np.nan, v); v = np.where(v < 0.05, 0.0 * v, v)
    out[idx] = np.nanmean(v.reshape(len(idx), -1), 1) if blk is not None else np.nan
np.save(f"data/cache/{'lib3/pzi_part_' if LIB3 else 'pzi_'}{lo}.npy", np.stack([part.astype("float64"), out[part]])); print(lo, hi, round(time.time() - t0), "s", np.nanmean(out[part]))
