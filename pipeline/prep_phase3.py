"""One-time prep: cache Diviner polar table and MODIS annual grids as compact arrays."""
import glob, os, numpy as np, pandas as pd
from pyhdf.SD import SD
os.makedirs("data/cache", exist_ok=True)
if not os.path.exists("data/cache/diviner_south.npz"):
    df = pd.read_csv("data/diviner/dlre_prp_south.tab", usecols=[9, 10, 12, 13, 14], header=0, names=["lon", "lat", "tavg", "tmax", "ice"],
                     skipinitialspace=True, dtype="float32")
    np.savez_compressed("data/cache/diviner_south.npz", **{c: df[c].values for c in df})
    print("diviner rows", len(df), "lat range", df.lat.min(), df.lat.max(), "tavg", df.tavg.min(), df.tavg.max(), "tmax", df.tmax.min(), df.tmax.max())
if not os.path.exists("data/cache/modis.npz"):
    # running statistics, one month in memory at a time
    acc = {}
    def upd(k, a, fn):
        acc[k] = a.copy() if k not in acc else fn(acc[k], a)
    cnt = {}
    for f in sorted(glob.glob("data/modis/lst/*.hdf")):
        h = SD(f)
        for name, key in (("LST_Day_CMG", "day"), ("LST_Night_CMG", "night")):
            a = h.select(name)[:].astype("float32") * 0.02; a[a == 0] = np.nan
            upd(key + "_max", a, np.fmax); upd(key + "_min", a, np.fmin)
            upd(key + "_sum", np.nan_to_num(a), np.add); upd(key + "_n", np.isfinite(a).astype("float32"), np.add)
    for f in sorted(glob.glob("data/modis/ndvi/*.hdf")):
        v = SD(f).select("CMG 0.05 Deg Monthly NDVI")[:].astype("float32"); v[v < -2000] = np.nan; v *= 1e-4
        upd("ndvi_max", v, np.fmax)
    np.savez_compressed("data/cache/modis.npz", day_max=acc["day_max"], night_min=acc["night_min"],
                        day_mean=acc["day_sum"] / np.maximum(acc["day_n"], 1), night_mean=acc["night_sum"] / np.maximum(acc["night_n"], 1),
                        day_n=acc["day_n"], night_n=acc["night_n"], ndvi_max=acc["ndvi_max"])
    print("modis grids saved")
