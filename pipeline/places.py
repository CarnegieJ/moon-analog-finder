"""Place context for every Earth window: country (Natural Earth boundaries, via the world-atlas package) and the nearest town of
over 1,000 people in the same country with its distance (GeoNames cities1000, via the reverse_geocoder package)."""
import json, os, numpy as np, pandas as pd, shapely, shapely.affinity, pycountry, reverse_geocoder
from shapely.geometry import Polygon, MultiPolygon
from scipy.spatial import cKDTree
t = json.load(open("data/cache/countries-50m.json")); sc, tr = t["transform"]["scale"], t["transform"]["translate"]
arcs = []
for a in t["arcs"]:
    p = np.cumsum(np.array(a, "float64"), 0); arcs.append(np.c_[p[:, 0] * sc[0] + tr[0], p[:, 1] * sc[1] + tr[1]])
def ring(ids):
    pts = []
    for i in ids:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]; pts.extend(a if not pts else a[1:])
    return pts
def geom(g):
    polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]; out = []; out2 = []
    for p in polys:
        rs = [np.array(ring(r), "float64") for r in p]
        if len(rs[0]) < 4: continue
        if np.abs(np.diff(rs[0][:, 0])).max() > 180:          # ring crosses the 180 degree meridian (Russia, Fiji, Antarctica): unwrap it, then add a copy shifted back
            rs = [np.c_[np.where(r[:, 0] < 0, r[:, 0] + 360, r[:, 0]), r[:, 1]] for r in rs]; pg = shapely.make_valid(Polygon(rs[0], [r for r in rs[1:] if len(r) >= 4]))
            out2.append(pg); out2.append(shapely.affinity.translate(pg, xoff=-360)); continue
        out.append(Polygon(rs[0], [r for r in rs[1:] if len(r) >= 4]))
    return shapely.unary_union([shapely.make_valid(MultiPolygon(out))] + out2)
C = [(g["properties"]["name"], g.get("id"), geom(g)) for g in t["objects"]["countries"]["geometries"] if g.get("arcs")]
z = np.load("data/cache/library_v2.npz"); s = z["s"]; cols = list(z["cols"]); lat, lon = s[:, cols.index("lat")].astype("float64"), s[:, cols.index("lon")].astype("float64"); N = len(lat)
cidx = np.full(N, -1, "int32")
for k, (name, cid, g) in enumerate(C):
    x0, y0, x1, y1 = g.bounds; m = (cidx < 0) & (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
    if m.any():
        hit = shapely.contains_xy(g, lon[m], lat[m]); ii = np.where(m)[0][hit]; cidx[ii] = k
print("windows with a country:", int((cidx >= 0).sum()), "of", N)
# windows on coasts that fall just outside the simplified outline: nearest country within 0.3 degrees
miss = np.where(cidx < 0)[0]
for i in miss:
    p = shapely.Point(lon[i], lat[i]); d = [(g.distance(p), k) for k, (_, _, g) in enumerate(C) if g.bounds[0] - 0.5 <= lon[i] <= g.bounds[2] + 0.5 and g.bounds[1] - 0.5 <= lat[i] <= g.bounds[3] + 0.5]
    if d and min(d)[0] < 0.3: cidx[i] = min(d)[1]
ant = [k for k, c in enumerate(C) if c[0] == "Antarctica"]
if ant: cidx[(cidx < 0) & (lat < -60)] = ant[0]      # the Antarctic outline wraps the pole and cannot be tested as a flat polygon
print("after coast fix:", int((cidx >= 0).sum()))
# nearest town in the same country
rgf = os.path.join(os.path.dirname(reverse_geocoder.__file__), "rg_cities1000.csv"); towns = pd.read_csv(rgf)
def xyz(la, lo): la, lo = np.radians(la), np.radians(lo); return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
num2a2 = {c.numeric: c.alpha_2 for c in pycountry.countries}
town_names, tidx, tkm = [], np.full(N, -1, "int32"), np.zeros(N, "float32"); P = xyz(lat, lon)
for k, (name, cid, g) in enumerate(C):
    m = np.where(cidx == k)[0]
    if not len(m): continue
    a2 = num2a2.get(str(cid).zfill(3)) if cid is not None else None
    tw = towns[towns["cc"] == a2] if a2 else towns.iloc[0:0]
    if not len(tw): continue
    d, j = cKDTree(xyz(tw["lat"].values, tw["lon"].values)).query(P[m]); base = len(town_names); town_names += [str(n) for n in tw["name"].values]
    tidx[m] = base + j; tkm[m] = 2 * 6371 * np.arcsin(np.clip(d / 2, 0, 1))
# distance to the nearest international land border: arcs shared by two countries in the topology
from collections import Counter
use = Counter()
for g in t["objects"]["countries"]["geometries"]:
    if not g.get("arcs"): continue
    polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]; mine = set()
    for p in polys:
        for r in p:
            for i in r: mine.add(i if i >= 0 else ~i)
    for i in mine: use[i] += 1
bpts = []
for i, n in use.items():
    if n < 2: continue
    a = arcs[i]
    for q in range(len(a) - 1):                      # densify to roughly 2 km
        seg = max(1, int(np.hypot(*(a[q + 1] - a[q])) / 0.02)); bpts.append(np.linspace(a[q], a[q + 1], seg, endpoint=False))
bpts = np.vstack(bpts); bd, _ = cKDTree(xyz(bpts[:, 1], bpts[:, 0])).query(P); bkm = 2 * 6371 * np.arcsin(np.clip(bd / 2, 0, 1))
print("windows within 15 km of a land border:", int((bkm <= 15).sum()))
used = sorted(set(int(v) for v in tidx if v >= 0)); remap = {u: n for n, u in enumerate(used)}
out_t = np.array([remap.get(int(v), 65535) for v in tidx], "uint16"); names_c = [c[0] for c in C]
np.c_[np.where(cidx < 0, 65535, cidx).astype("uint16"), out_t, np.clip(np.round(tkm), 0, 65535).astype("uint16"), np.clip(np.round(bkm), 0, 65535).astype("uint16")].astype("uint16").tofile("app/data/earth_place.bin")
json.dump({"countries": names_c, "towns": [town_names[u] for u in used]}, open("app/data/places.json", "w"), ensure_ascii=False)
print("towns used:", len(used), "| no country:", int((cidx < 0).sum()), "| no town:", int((tidx < 0).sum()))
for la, lo in ((73.95, -25.18), (37.32, 73.11), (21.05, 16.45), (-24.32, -68.06), (70.23, -86.24), (-77.5, 162.29), (82.68, -33.5), (68.41, -69.62), (66.0, 172.0)):
    i = int(np.argmin((lat - la) ** 2 + (lon - lo) ** 2)); print(f"  {la},{lo}: {names_c[cidx[i]] if cidx[i] >= 0 else None} | nearest town {town_names[tidx[i]] if tidx[i] >= 0 else None} {tkm[i]:.0f} km | land border {bkm[i]:.0f} km")
