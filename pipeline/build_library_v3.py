"""Collect the overlapping-square scan (version 3 plus tile-edge supplement) into plain arrays in data/cache/lib3/.
Usage: python pipeline/build_library_v3.py main|edges|merge     (three short steps, each safe to re-run)"""
import glob, os, sys, numpy as np
COLS = ["lat", "lon", "tri_p50", "tri_p90", "relief", "slope_p50", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun", "hurst", "slope320_p50", "nomask",
        "slope_p10", "slope_p90", "slope320_p90", "rms_80", "rms_1280", "on_old_grid"]
D = "data/cache/lib3/"; os.makedirs(D, exist_ok=True); step = sys.argv[1]
if step in ("main", "edges"):
    S, H = [], []
    for f in sorted(glob.glob(f"data/out/{'search_v3' if step == 'main' else 'search_v3_edges'}/*.npz")):
        if os.path.getsize(f) == 0: continue
        z = np.load(f)
        if len(z["s"]): S.append(z["s"]); H.append(z["hist"])
    np.save(D + f"s_{step}.npy", np.concatenate(S)); np.save(D + f"hist_{step}.npy", np.concatenate(H)); print(step, sum(len(x) for x in S))
else:
    a, b = np.load(D + "s_main.npy"), np.load(D + "s_edges.npy"); np.save(D + "s.npy", np.concatenate([a, b]))
    np.save(D + "hist.npy", np.concatenate([np.load(D + "hist_main.npy"), np.load(D + "hist_edges.npy")])); np.save(D + "edge.npy", np.r_[np.zeros(len(a), "uint8"), np.ones(len(b), "uint8")])
    open(D + "cols.txt", "w").write("\n".join(COLS)); print("windows:", len(a) + len(b), "| inside tiles:", len(a), "| crossing tile edges:", len(b), "| on the old 10 km grid:", int(a[:, 19].sum()))
