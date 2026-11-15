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

def hurst(dem, res, lags=(1, 2, 4, 8, 16)):
    """Hurst exponent: how fast height differences grow with distance (Rosenburg et al. 2011 use the same idea on LOLA data).
    Window is detrended with a plane; RMS height difference is measured at each lag in both grid directions;
    H is the slope of log(RMS difference) against log(distance). Lags here span 80 m to 1.28 km at 80 m pixels."""
    n, m = dem.shape; yy, xx = np.mgrid[0:n, 0:m]
    A = np.c_[xx.ravel(), yy.ravel(), np.ones(n * m)]; coef, *_ = np.linalg.lstsq(A, dem.ravel(), rcond=None)
    d = dem - (A @ coef).reshape(n, m); v = []
    for l in lags:
        a = d[:, l:] - d[:, :-l]; b = d[l:, :] - d[:-l, :]
        v.append(np.sqrt((np.sum(a * a) + np.sum(b * b)) / (a.size + b.size)))
    v = np.maximum(np.array(v), 1e-6); x = np.log(np.array(lags) * res)
    return float(np.polyfit(x, np.log(v), 1)[0]), [float(q) for q in v]

def coarse_slope(dem, res, k=4):
    """Median slope after averaging the DEM into k x k blocks (baseline k * res, e.g. 320 m)."""
    n = (dem.shape[0] // k) * k; c = dem[:n, :n].reshape(n // k, k, n // k, k).mean(axis=(1, 3))
    s = horn_slope(c, res * k); return float(np.median(s)), float(np.percentile(s, 90))

def features(dem, res):
    slope = horn_slope(dem, res)
    r = tri(dem)
    ok = np.isfinite(slope) & np.isfinite(r)
    s, r, d = slope[ok], r[ok], dem[np.isfinite(dem)]
    hist, _ = np.histogram(np.clip(s, 0, 45.999), bins=SLOPE_BINS)
    H, rms = hurst(dem, res); s320, s320_90 = coarse_slope(dem, res)
    return {
        "hurst": H, "rms_80": rms[0], "rms_1280": rms[-1], "slope320_p50": s320, "slope320_p90": s320_90,
        "slope_hist": (hist / hist.sum()).round(5).tolist(),
        "slope_p10": float(np.percentile(s, 10)), "slope_p50": float(np.percentile(s, 50)),
        "slope_p90": float(np.percentile(s, 90)), "slope_mean": float(s.mean()),
        "share_lt5": float((s < 5).mean()), "share_5_10": float(((s >= 5) & (s < 10)).mean()),
        "share_10_20": float(((s >= 10) & (s < 20)).mean()), "share_gt20": float((s >= 20).mean()),
        "tri_p50": float(np.percentile(r, 50)), "tri_p90": float(np.percentile(r, 90)),
        "relief_m": float(np.percentile(d, 95) - np.percentile(d, 5)),
        "n_pixels": int(ok.sum()), "res_m": res,
    }, slope
