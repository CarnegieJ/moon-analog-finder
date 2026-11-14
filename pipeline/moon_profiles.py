"""Phase 1: lunar reference profiles for Artemis III candidate regions (approximate centres)."""
import json, os, sys
import numpy as np, rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer, CRS
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from terrain import features, SLOPE_BINS

M = "data/moon/"
WIN_KM = 10.0  # 5 km radius: NASA mobility paper gives traverse ranges up to 5,000 m
# Centres are APPROXIMATE (from feature locations, not NASA region boundaries). UNVERIFIED: replace with cited coordinates.
TARGETS = [
    {"id": "haworth", "name": "Haworth", "lat": -87.45, "lon": -5.0, "note": "approx. crater centre"},
    {"id": "malapert", "name": "Malapert Massif", "lat": -86.0, "lon": 0.0, "note": "approx. massif summit area"},
    {"id": "degerlache", "name": "de Gerlache Rim 2", "lat": -88.7, "lon": -68.0, "note": "approx. rim of de Gerlache crater"},
]
os.makedirs("data/out", exist_ok=True); os.makedirs("workspace/img", exist_ok=True)

dem = rasterio.open(M + "LDEM_80S_80MPP_ADJ.TIF"); slp = rasterio.open(M + "LDSM_80S_80MPP_ADJ.TIF")
psr = rasterio.open(M + "LPSR_80S_20MPP_ADJ.TIF"); ill = rasterio.open(M + "AVGVISIB_75S_120M_201608.TIF")
geo = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
tf = Transformer.from_crs(geo, dem.crs, always_xy=True)

def read(ds, x, y, half):
    w = from_bounds(x-half, y-half, x+half, y+half, ds.transform)
    a = ds.read(1, window=w).astype("float64")
    if ds.nodata is not None and not np.isnan(ds.nodata): a[a == ds.nodata] = np.nan
    return a * (ds.scales[0] or 1.0)

out = []
for t in TARGETS:
    x, y = tf.transform(t["lon"], t["lat"]); half = WIN_KM * 500
    d = read(dem, x, y, half); f, s_own = features(d, 80.0)
    s_nasa = read(slp, x, y, half); p = read(psr, x, y, half); i = read(ill, x, y, half)
    f.update({"nasa_slope_p50": float(np.nanpercentile(s_nasa, 50)), "nasa_slope_p90": float(np.nanpercentile(s_nasa, 90)),
              "psr_share": float(np.nanmean(p > 0.5)), "illum_mean": float(np.nanmean(i)),
              "illum_p90": float(np.nanpercentile(i, 90)), "illum_max": float(np.nanmax(i)),
              "elev_min": float(np.nanmin(d)), "elev_max": float(np.nanmax(d))})
    t.update({"x": x, "y": y, "window_km": WIN_KM, "features": f}); out.append(t)
    fig, ax = plt.subplots(1, 4, figsize=(16, 4.4))
    for a, img, ttl, cm, vm in [(ax[0], d, "Elevation (m)", "gray", None), (ax[1], s_own, "Slope (deg)", "magma", 35),
                                (ax[2], i, "Average sunlight (fraction of time)", "inferno", 1), (ax[3], p, "Permanent shadow", "Blues", 1)]:
        im = a.imshow(img, cmap=cm, vmin=0 if vm else None, vmax=vm); a.set_title(ttl, fontsize=10); a.axis("off"); plt.colorbar(im, ax=a, fraction=0.046)
    fig.suptitle(f'{t["name"]} ({WIN_KM:.0f} km window, centre approx. {t["lat"]}, {t["lon"]})'); fig.tight_layout()
    fig.savefig(f'workspace/img/moon_{t["id"]}.png', dpi=90); plt.close(fig)
    print(t["name"], {k: round(v, 3) for k, v in f.items() if isinstance(v, float)})

# slope histogram comparison
fig, a = plt.subplots(figsize=(8, 4))
for t in out: a.plot(SLOPE_BINS[:-1] + .5, t["features"]["slope_hist"], label=t["name"], lw=2)
a.axvline(10, ls="--", c="gray"); a.axvline(20, ls="--", c="gray"); a.set_xlabel("Slope (degrees, 80 m baseline)"); a.set_ylabel("Share of area")
a.set_title("Slope distribution of lunar targets (dashed: NASA 10 and 20 degree mobility figures)"); a.legend(); fig.tight_layout()
fig.savefig("workspace/img/moon_slope_hist.png", dpi=90); plt.close(fig)

# overview map (decimated)
k = 8; S = slp.read(1, out_shape=(slp.height // k, slp.width // k))
fig, a = plt.subplots(figsize=(8, 8)); b = slp.bounds
a.imshow(S, cmap="magma", vmin=0, vmax=35, extent=[b.left/1000, b.right/1000, b.bottom/1000, b.top/1000])
for t in out:
    h = WIN_KM / 2; a.add_patch(plt.Rectangle((t["x"]/1000 - h, t["y"]/1000 - h), 2*h, 2*h, fill=False, ec="cyan", lw=1.5))
    a.text(t["x"]/1000 + h + 3, t["y"]/1000, t["name"], color="cyan", fontsize=9)
a.plot(0, 0, "w+"); a.set_xlim(-150, 150); a.set_ylim(-150, 150); a.set_title("Lunar south pole slope map (LOLA 80 m), target windows in cyan"); a.set_xlabel("km"); a.set_ylabel("km")
fig.tight_layout(); fig.savefig("workspace/img/moon_overview.png", dpi=90); plt.close(fig)
json.dump(out, open("data/out/moon_profiles.json", "w"), indent=1)
