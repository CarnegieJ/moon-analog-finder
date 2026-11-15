"""Accuracy test with thousands of cases: can the terrain fingerprint recognise the same terrain from different pixels?
Each 10 km lunar square is cut into a checkerboard of 2.5 km tiles. Fingerprint A is computed from the 8 'black' tiles and fingerprint B
from the 8 'white' tiles: same terrain, no shared pixels. For every square, its A is compared with the B of all squares.
A reliable fingerprint ranks its own B first. Squares do not overlap each other (10 km spacing).
Usage: python pipeline/identity_test.py compute | score"""
import sys, json, numpy as np
sys.path.insert(0, "pipeline"); from terrain import horn_slope, SLOPE_BINS
RES, NW, TS, LAGS = 80.0, 125, 31, (1, 2, 4, 8, 16)
rr, cc = np.mgrid[0:NW, 0:NW]; TID = np.where((rr < 4 * TS) & (cc < 4 * TS), (rr // TS) * 4 + cc // TS, -1); BLACK = ((rr // TS + cc // TS) % 2 == 0) & (TID >= 0); WHITE = (~BLACK) & (TID >= 0)
A3 = np.c_[cc.ravel(), rr.ravel(), np.ones(NW * NW)]; PINV = np.linalg.pinv(A3)
c4 = np.arange(31) * 4 + 2; CT = TID[np.ix_(c4, c4)]; CB = BLACK[np.ix_(c4, c4)]
def halves(d):
    """Fingerprints of the black and the white half of one 125 x 125 window. Returns two rows: 46 slope bins, hurst, slope_p50, slope320_p50, relief."""
    s = horn_slope(d, RES); dd = d - (A3 @ (PINV @ d.ravel())).reshape(NW, NW)
    n = 124; cz = d[:n, :n].reshape(31, 4, 31, 4).mean(axis=(1, 3)); s4 = horn_slope(cz, RES * 4); out = []
    for M, MC in ((BLACK, CB), (WHITE, ~CB & (CT >= 0))):
        h = np.histogram(np.clip(s[M], 0, 45.999), bins=SLOPE_BINS)[0]; v = []
        for l in LAGS:
            a = (dd[:, l:] - dd[:, :-l])[(TID[:, l:] == TID[:, :-l]) & M[:, l:]]; b = (dd[l:, :] - dd[:-l, :])[(TID[l:, :] == TID[:-l, :]) & M[l:, :]]
            v.append(np.sqrt((np.sum(a * a) + np.sum(b * b)) / (a.size + b.size)))
        H = np.polyfit(np.log(np.array(LAGS) * RES), np.log(np.maximum(v, 1e-6)), 1)[0]
        out.append(np.r_[h / h.sum(), H, np.median(s[M]), np.median(s4[MC]), np.percentile(d[M], 95) - np.percentile(d[M], 5)])
    return out
if sys.argv[1] == "compute":
    import rasterio
    dem = rasterio.open("data/moon/LDEM_80S_80MPP_ADJ.TIF").read(1).astype("float64"); n80 = dem.shape[0]; A, B, xy = [], [], []
    for kx in range(-29, 30):
        for ky in range(-29, 30):
            x, y = kx * 10000.0, ky * 10000.0
            if np.hypot(x, y) > 290000: continue
            c0, r0 = int((x - 5000 + 304000) / 80), int((304000 - (y + 5000)) / 80); d = dem[r0:r0+NW, c0:c0+NW]
            if d.shape != (NW, NW) or not np.isfinite(d).all(): continue
            a, b = halves(d); A.append(a); B.append(b); xy.append((x, y))
    np.savez("data/cache/identity_moon.npz", A=np.array(A, "float32"), B=np.array(B, "float32"), xy=np.array(xy)); print("squares", len(A))
else:
    z = np.load(sys.argv[2] if len(sys.argv) > 2 else "data/cache/identity_moon.npz"); A, B = z["A"], z["B"]; N = len(A); H_RANGE, RET_RANGE = 0.4, 0.5
    def parts(a, b):          # a: one fingerprint, b: all
        slope = 1 - 0.5 * np.abs(b[:, :46] - a[:46]).sum(1); hu = np.clip(1 - np.abs(b[:, 46] - a[46]) / H_RANGE, 0, 1)
        ret = np.clip(1 - np.abs(b[:, 48] / np.maximum(b[:, 47], 1e-6) - a[48] / max(a[47], 1e-6)) / RET_RANGE, 0, 1)
        rel = 1 - np.abs(b[:, 49] - a[49]) / np.maximum(np.maximum(b[:, 49], a[49]), 1e-9); return slope, hu, ret, rel
    V = {"current score (slope + roughness across scales)": lambda s, h, r, e: .5 * s + .25 * h + .25 * r, "slope chart only": lambda s, h, r, e: s, "scaling number only": lambda s, h, r, e: h,
         "roughness across scales only": lambda s, h, r, e: .5 * h + .5 * r, "relief only": lambda s, h, r, e: e, "current + relief": lambda s, h, r, e: (.5 * s + .25 * h + .25 * r) * 2 / 3 + e / 3,
         "slope chart + relief": lambda s, h, r, e: .5 * s + .5 * e, "slope + scaling + relief (thirds)": lambda s, h, r, e: (s + h + e) / 3, "all four equal": lambda s, h, r, e: (s + h + r + e) / 4}
    R = {k: {"rank": [], "self": [], "other": []} for k in V}
    for i in range(N):
        p = parts(A[i], B)
        for k, fn in V.items():
            sc = fn(*p); R[k]["rank"].append(int((sc > sc[i]).sum()) + 1); R[k]["self"].append(float(sc[i])); R[k]["other"].append(float((sc.sum() - sc[i]) / (N - 1)))
    out = {"squares": N, "chance_top1_pct": round(100 / N, 3), "variants": {}}
    print(f"{N} squares; by chance the true partner is ranked first {100/N:.2f}% of the time\n{'scoring':52s} first  top10  top1%  median rank  same-terrain score  other-terrain score")
    for k, v in R.items():
        r = np.array(v["rank"]); o = {"top1_pct": round(100 * float((r == 1).mean()), 1), "top10_pct": round(100 * float((r <= 10).mean()), 1), "top1pct_pct": round(100 * float((r <= N / 100).mean()), 1),
             "median_rank": float(np.median(r)), "same_terrain_score_mean": round(float(np.mean(v["self"])), 3), "same_terrain_score_p10": round(float(np.percentile(v["self"], 10)), 3), "other_terrain_score_mean": round(float(np.mean(v["other"])), 3)}
        out["variants"][k] = o; print(f"{k:52s} {o['top1_pct']:5.1f}  {o['top10_pct']:5.1f}  {o['top1pct_pct']:5.1f}  {o['median_rank']:11.0f}  {o['same_terrain_score_mean']:.3f} (p10 {o['same_terrain_score_p10']:.3f})   {o['other_terrain_score_mean']:.3f}")
    json.dump(out, open("data/out/identity_test.json", "w"), indent=1)
