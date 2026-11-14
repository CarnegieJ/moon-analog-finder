"""Shared terrain features. Same code is used for Moon and Earth so numbers are comparable."""
import numpy as np

SLOPE_BINS = np.arange(0, 47, 1.0)  # 1-degree bins 0..45, last bin = 45+

def horn_slope(dem, res):
    """Slope in degrees (Horn 1981) from a projected DEM with square pixels of size res (m)."""
    z = np.pad(dem, 1, mode="edge")
    dzdx = ((z[:-2, 2:] + 2*z[1:-1, 2:] + z[2:, 2:]) - (z[:-2, :-2] + 2*z[1:-1, :-2] + z[2:, :-2])) / (8*res)
    dzdy = ((z[2:, :-2] + 2*z[2:, 1:-1] + z[2:, 2:]) - (z[:-2, :-2] + 2*z[:-2, 1:-1] + z[:-2, 2:])) / (8*res)
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy)))

def tri(dem):
    """Terrain ruggedness index (Riley 1999): root of summed squared diffs to 8 neighbours, metres."""
    z = np.pad(dem, 1, mode="edge")
    c = z[1:-1, 1:-1]
    s = np.zeros_like(c)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1: continue
            s += (z[dy:dy+c.shape[0], dx:dx+c.shape[1]] - c) ** 2
    return np.sqrt(s)

def features(dem, res):
    slope = horn_slope(dem, res)
    r = tri(dem)
    ok = np.isfinite(slope) & np.isfinite(r)
    s, r, d = slope[ok], r[ok], dem[np.isfinite(dem)]
    hist, _ = np.histogram(np.clip(s, 0, 45.999), bins=SLOPE_BINS)
    return {
        "slope_hist": (hist / hist.sum()).round(5).tolist(),
        "slope_p10": float(np.percentile(s, 10)), "slope_p50": float(np.percentile(s, 50)),
        "slope_p90": float(np.percentile(s, 90)), "slope_mean": float(s.mean()),
        "share_lt5": float((s < 5).mean()), "share_5_10": float(((s >= 5) & (s < 10)).mean()),
        "share_10_20": float(((s >= 10) & (s < 20)).mean()), "share_gt20": float((s >= 20).mean()),
        "tri_p50": float(np.percentile(r, 50)), "tri_p90": float(np.percentile(r, 90)),
        "relief_m": float(np.percentile(d, 95) - np.percentile(d, 5)),
        "n_pixels": int(ok.sum()), "res_m": res,
    }, slope
