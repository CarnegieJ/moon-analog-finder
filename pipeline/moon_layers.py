"""Map layers for the app's south-pole map: 1520 x 1520 px PNGs covering +/-304 km (400 m per pixel)."""
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.cm as cm
M, N, OUT = "data/moon/", 1520, "app/layers/"
def rd(name, avg=True, crop=False):
    ds = rasterio.open(M + name); w = from_bounds(-304000, -304000, 304000, 304000, ds.transform) if crop else None
    return ds.read(1, window=w, out_shape=(N, N), resampling=Resampling.average if avg else Resampling.bilinear).astype("float32")
dem = rd("LDEM_80S_80MPP_ADJ.TIF"); res = 400.0
gy, gx = np.gradient(dem, res); az, alt = np.radians(315), np.radians(35)
slope = np.pi/2 - np.arctan(np.hypot(gx, gy) * 3); aspect = np.arctan2(-gx, gy)       # x3 vertical stretch for readability
hs = np.clip(np.sin(alt)*np.sin(slope) + np.cos(alt)*np.cos(slope)*np.cos(az - aspect), 0, 1)
plt.imsave(OUT + "base.png", hs, cmap="gray", vmin=0, vmax=1)
def save(name, a, cmap, vmin, vmax, alpha=0.8, mask=None):
    rgba = cm.get_cmap(cmap)(np.clip((a - vmin) / (vmax - vmin), 0, 1)); rgba[..., 3] = alpha
    bad = ~np.isfinite(a) if mask is None else mask; rgba[bad, 3] = 0
    plt.imsave(OUT + name, rgba)
save("slope.png", rd("LDSM_80S_80MPP_ADJ.TIF"), "magma", 0, 35)
ill = rd("AVGVISIB_75S_120M_201608.TIF", crop=True) * 4e-5; ill[ill < 0] = np.nan
save("sunlight.png", ill, "inferno", 0, 0.6)
psr = rd("LPSR_80S_20MPP_ADJ.TIF")
save("shadow.png", psr, "Blues", -0.5, 1.2, alpha=0.75, mask=~(psr > 0.3))
dv = np.load("data/cache/diviner_south.npz"); R = 1737400.0
rr = 2*R*np.tan(np.radians(90 + dv["lat"])/2); x = rr*np.sin(np.radians(dv["lon"])); y = rr*np.cos(np.radians(dv["lon"]))
e = np.linspace(-304000, 304000, 305)                                                   # 2 km bins
c = np.histogram2d(y, x, bins=[e, e])[0]; t = np.histogram2d(y, x, bins=[e, e], weights=dv["tmax"])[0] / np.maximum(c, 1); t[c == 0] = np.nan
t = np.kron(t[::-1], np.ones((5, 5)))[:N, :N]                                            # row 0 = top (north on map = +y)
save("temperature.png", t, "turbo", 40, 320)
print("layers written")
