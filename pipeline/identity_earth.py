"""Second accuracy test: the same Earth place measured by two elevation datasets.
Fingerprint A comes from Copernicus 30 m data (local tiles, averaged to 80 m); fingerprint B is the library entry for the same square,
made from Copernicus 90 m data. Both describe the same ground. The gap between them is the error the data source adds to a score.
Writes data/cache/identity_earth.npz in the format read by identity_test.py score."""
import glob, numpy as np
from pyproj import Transformer, CRS
from scipy.spatial import cKDTree
S = np.load("data/cache/lib3/s.npy", mmap_mode="r"); Hh = np.load("data/cache/lib3/hist.npy", mmap_mode="r"); old = np.where(np.array(S[:, 19]) == 1)[0]
lat, lon = np.array(S[old, 0], "float64"), np.array(S[old, 1], "float64"); A, B = [], []
for f in sorted(glob.glob("data/cache/overlap/*.npz")):
    z = np.load(f); R = z["rows"]; H, W = z["shape"]; lat0, lon0 = float(z["lat0"]), float(z["lon0"])
    if not len(R): continue
    al = (R[:, 0] % 124 == 0) & (R[:, 1] % 124 == 0); R = R[al]                   # squares on the 10 km grid (within one or two pixels of the library's)
    if not len(R): continue
    tf = Transformer.from_crs(CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m"), "EPSG:4326", always_xy=True)
    lo, la = tf.transform((-W / 2 + R[:, 1] + 62.5) * 80.0, (H / 2 - R[:, 0] - 62.5) * 80.0)
    m = np.where((np.abs(lat - lat0) < 0.6) & (np.abs(lon - lon0) < 0.6 / max(np.cos(np.radians(lat0)), 0.05) + 0.6))[0]
    if not len(m): continue
    kx = np.cos(np.radians(lat0)); d, j = cKDTree(np.c_[lat[m], lon[m] * kx]).query(np.c_[la, np.array(lo) * kx]); ok = d < 0.004     # within about 450 m
    for r, jj in zip(R[ok], m[j[ok]]):
        g = old[jj]; A.append(np.r_[r[6:], r[2], r[3], r[4], r[5]]); B.append(np.r_[np.array(Hh[g], "float32") / 10000, S[g, 11], S[g, 5], S[g, 12], S[g, 4]])
A, B = np.array(A, "float32"), np.array(B, "float32"); keep = (A[:, 47] >= 1) & (B[:, 47] >= 1); np.savez("data/cache/identity_earth.npz", A=A[keep], B=B[keep])
print("matched squares", len(A), "after dropping near-flat ones", int(keep.sum()), "| median slope 30 m vs 90 m data:", round(float(np.median(A[keep, 47])), 2), round(float(np.median(B[keep, 47])), 2), "| scaling number:", round(float(np.median(A[keep, 46])), 3), round(float(np.median(B[keep, 46])), 3))
