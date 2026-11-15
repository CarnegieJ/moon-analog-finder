"""Altitude of every window in the overlapping-square library: mean ground elevation over roughly the 10 km square, read from the
1 km tile averages made by modal_elev.py. Writes data/cache/lib3/alt.npy (metres, NaN where the tile is missing)."""
import os, numpy as np
S = np.load("data/cache/lib3/s.npy", mmap_mode="r"); lat = np.array(S[:, 0], "float64"); lon = np.array(S[:, 1], "float64"); N = len(lat); out = np.full(N, np.nan, "float32")
tla, tlo = np.floor(lat).astype(int), np.floor(lon).astype(int); key = (tla + 90) * 360 + (tlo + 180); order = np.argsort(key, kind="stable"); ks = key[order]; cuts = np.flatnonzero(np.diff(ks)) + 1
miss = 0
for idx in np.split(order, cuts):
    la, lo = int(tla[idx[0]]), int(tlo[idx[0]]); f = f"data/out/elev/Copernicus_DSM_COG_30_{'N' if la >= 0 else 'S'}{abs(la):02d}_00_{'E' if lo >= 0 else 'W'}{abs(lo):03d}_00_DEM.npy"
    if not os.path.exists(f) or os.path.getsize(f) == 0: miss += len(idx); continue
    a = np.load(f).astype("float64"); c = np.cumsum(np.cumsum(np.pad(a, ((1, 0), (1, 0))), 0), 1)            # summed-area table for fast box means
    r = np.clip(((la + 1 - lat[idx]) * 120).astype(int), 0, 119); q = np.clip(((lon[idx] - lo) * 120).astype(int), 0, 119)
    hr = 5; hc = np.clip(np.round(5 / np.maximum(np.cos(np.radians(lat[idx])), 0.05)).astype(int), 1, 60)             # about 5 km each side
    r0, r1 = np.clip(r - hr, 0, 120), np.clip(r + hr + 1, 0, 120); c0, c1 = np.clip(q - hc, 0, 120), np.clip(q + hc + 1, 0, 120)
    out[idx] = (c[r1, c1] - c[r0, c1] - c[r1, c0] + c[r0, c0]) / ((r1 - r0) * (c1 - c0))
np.save("data/cache/lib3/alt.npy", out); print("windows", N, "| without altitude", int(np.isnan(out).sum()), "| above 3500 m", int((out > 3500).sum()), "| median", float(np.nanmedian(out)))
def near(la, lo): i = int(np.argmin((lat - la) ** 2 + ((lon - lo) * np.cos(np.radians(la))) ** 2)); return round(float(out[i]))
for nm, la, lo, tile in (("Argentina top Malapert match", -28.02, -68.75, 5700), ("Mauna Kea candidate", 19.84, -155.52, 3050), ("Baffin candidate", 64.30, -66.14, 730), ("N Greenland candidate", 82.66, -33.50, 690), ("Algeria", 24.66, -4.01, 280)):
    print(f"  {nm}: library altitude {near(la, lo)} m, display tiles said {tile} m")
