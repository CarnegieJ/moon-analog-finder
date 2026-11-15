"""Sun-angle shadow simulation and its check against NASA's own lunar illumination products.
For each cell of a 10 km window, find the horizon in 16 directions by marching outwards up to 150 km over the 200 m lunar DEM,
allowing for the curvature of the Moon. A cell is in shadow when the Sun is below its horizon."""
import json, numpy as np
R_MOON, RES, NAZ = 1737400.0, 200.0, 16
STEPS = np.unique(np.round(np.concatenate([np.arange(1, 40), np.geomspace(40, 750, 45)])).astype(int))    # 0.2 km to 150 km
def horizons(D, r0, c0, n=51, radius=R_MOON):
    """tan(horizon elevation) for an n x n block whose top-left cell is (r0, c0); shape (NAZ, n, n)."""
    N = D.shape[0]; rr, cc = np.mgrid[r0:r0+n, c0:c0+n]; h0 = D[rr, cc]; out = np.full((NAZ, n, n), -9.0)
    for a in range(NAZ):
        az = 2 * np.pi * a / NAZ; dc, dr = np.sin(az), -np.cos(az)
        for s in STEPS:
            r = np.rint(rr + dr * s).astype(int); c = np.rint(cc + dc * s).astype(int); ok = (r >= 0) & (r < N) & (c >= 0) & (c < N)
            if not ok.any(): break
            dist = s * RES; t = (D[np.clip(r, 0, N-1), np.clip(c, 0, N-1)] - h0 - dist * dist / (2 * radius)) / dist
            out[a] = np.maximum(out[a], np.where(ok, t, -9.0))
    return out
if __name__ == "__main__":
    # Check: simulate a full year of sun positions (24 x 7.5 degree hour angles, 7 solar latitudes within +-1.54 degrees) and compare with
    # NASA's average-sunlight map (PGDA product 69) and permanent-shadow map (PGDA product 90) for 3 named and 60 random spots.
    D = np.fromfile("app/data/moon_dem200.bin", "int16").reshape(3040, 3040).astype("float64")
    grid = json.load(open("data/out/moon_grid.json")); rng = np.random.default_rng(2); named = list(json.load(open("data/out/moon_profiles.json")))
    pick = [g for g in grid if abs(g["x"]) < 200000 and abs(g["y"]) < 200000]; pick = [pick[i] for i in rng.choice(len(pick), 60, replace=False)]
    hs = np.radians(np.arange(0, 360, 7.5)); ds = np.radians(np.linspace(-1.54, 1.54, 7)); rows = []
    for g in named + pick:
        x, y = g["x"], g["y"]; f = g.get("features", g); phi = np.radians(g["lat"])
        H = horizons(D, int((304000 - y) / RES) - 25, int((x + 304000) / RES) - 25); azn = np.arctan2(x, y); lit = 0; never = np.ones(H.shape[1:], bool)
        for h in hs:
            a = int(np.rint(((azn + h) % (2 * np.pi)) / (2 * np.pi / NAZ))) % NAZ
            for d in ds:
                e = np.arcsin(np.sin(phi) * np.sin(d) + np.cos(phi) * np.cos(d) * np.cos(h)); up = np.tan(e) > H[a]; lit += up.mean(); never &= ~up
        rows.append((g.get("name", ""), g["lat"], f["illum_mean"], lit / (len(hs) * len(ds)), f["psr_share"], never.mean()))
    for r in rows[:3]: print(f"{r[0]:18s} lat {r[1]:.1f}: NASA sunlit share {r[2]:.2f} vs simulated {r[3]:.2f} | NASA permanent shadow {r[4]:.2f} vs simulated {r[5]:.2f}")
    a = np.array([[r[2], r[3], r[4], r[5]] for r in rows]); out = {"spots": len(rows), "sunlit_corr": float(np.corrcoef(a[:,0], a[:,1])[0,1]), "sunlit_mean_abs_diff": float(np.abs(a[:,0]-a[:,1]).mean()),
        "shadow_corr": float(np.corrcoef(a[:,2], a[:,3])[0,1]), "shadow_mean_abs_diff": float(np.abs(a[:,2]-a[:,3]).mean()), "sunlit_max_abs_diff": float(np.abs(a[:,0]-a[:,1]).max()), "shadow_max_abs_diff": float(np.abs(a[:,2]-a[:,3]).max())}
    print(out); json.dump(out, open("data/out/shadow_check.json", "w"), indent=1)
