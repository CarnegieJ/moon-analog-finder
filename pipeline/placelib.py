"""Place context for any list of points: country (Natural Earth 1:50m outlines from the world-atlas package), nearest town of over
1,000 people in the same country (GeoNames cities1000 via the reverse_geocoder package) and distance to the nearest land border.
Same logic as places.py, as a reusable class for the scoring service."""
import json, os, numpy as np
class Places:
    def __init__(self, countries_json):
        import shapely, shapely.affinity, pandas as pd, pycountry, reverse_geocoder
        from shapely.geometry import Polygon, MultiPolygon
        from scipy.spatial import cKDTree
        from collections import Counter
        self.shapely, self.cKDTree = shapely, cKDTree
        t = json.load(open(countries_json)); sc, tr = t["transform"]["scale"], t["transform"]["translate"]; arcs = []
        for a in t["arcs"]:
            p = np.cumsum(np.array(a, "float64"), 0); arcs.append(np.c_[p[:, 0] * sc[0] + tr[0], p[:, 1] * sc[1] + tr[1]])
        def ring(ids):
            pts = []
            for i in ids:
                a = arcs[i] if i >= 0 else arcs[~i][::-1]; pts.extend(a if not pts else a[1:])
            return np.array(pts, "float64")
        def geom(g):
            polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]; out, out2 = [], []
            for p in polys:
                rs = [ring(r) for r in p]
                if len(rs[0]) < 4: continue
                if np.abs(np.diff(rs[0][:, 0])).max() > 180:      # ring crosses the 180 degree meridian: unwrap it, then add a copy shifted back
                    rs = [np.c_[np.where(r[:, 0] < 0, r[:, 0] + 360, r[:, 0]), r[:, 1]] for r in rs]; pg = shapely.make_valid(Polygon(rs[0], [r for r in rs[1:] if len(r) >= 4]))
                    out2 += [pg, shapely.affinity.translate(pg, xoff=-360)]; continue
                out.append(Polygon(rs[0], [r for r in rs[1:] if len(r) >= 4]))
            return shapely.unary_union([shapely.make_valid(MultiPolygon(out))] + out2)
        G = [g for g in t["objects"]["countries"]["geometries"] if g.get("arcs")]
        self.C = [(g["properties"]["name"], g.get("id"), geom(g)) for g in G]; self.ant = [k for k, c in enumerate(self.C) if c[0] == "Antarctica"]
        num2a2 = {c.numeric: c.alpha_2 for c in pycountry.countries}; towns = pd.read_csv(os.path.join(os.path.dirname(reverse_geocoder.__file__), "rg_cities1000.csv")); self.towns = {}
        for k, (name, cid, g) in enumerate(self.C):
            a2 = num2a2.get(str(cid).zfill(3)) if cid is not None else None; tw = towns[towns["cc"] == a2] if a2 else None
            if tw is not None and len(tw): self.towns[k] = (cKDTree(self.xyz(tw["lat"].values, tw["lon"].values)), [str(n) for n in tw["name"].values])
        use = Counter()
        for g in G:
            polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]; mine = set()
            for p in polys:
                for r in p:
                    for i in r: mine.add(i if i >= 0 else ~i)
            for i in mine: use[i] += 1
        bp = []
        for i, n in use.items():
            if n < 2: continue
            a = arcs[i]
            for q in range(len(a) - 1): bp.append(np.linspace(a[q], a[q + 1], max(1, int(np.hypot(*(a[q + 1] - a[q])) / 0.02)), endpoint=False))
        bp = np.vstack(bp); self.border = cKDTree(self.xyz(bp[:, 1], bp[:, 0]))
    @staticmethod
    def xyz(la, lo): la, lo = np.radians(np.asarray(la, "float64")), np.radians(np.asarray(lo, "float64")); return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    def country_index(self, lat, lon, coast=True):
        """Country index per point (-1 = none). Vectorised, for whole libraries."""
        sh = self.shapely; lat, lon = np.asarray(lat, "float64"), np.asarray(lon, "float64"); cidx = np.full(len(lat), -1, int)
        for k, (_, _, g) in enumerate(self.C):
            x0, y0, x1, y1 = g.bounds; m = (cidx < 0) & (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
            if m.any(): cidx[np.where(m)[0][sh.contains_xy(g, lon[m], lat[m])]] = k
        if coast:
            for i in np.where(cidx < 0)[0]:       # coast points just outside the simplified outline: nearest country within 0.3 degrees
                p = sh.Point(lon[i], lat[i]); d = [(g.distance(p), k) for k, (_, _, g) in enumerate(self.C) if g.bounds[0] - 0.5 <= lon[i] <= g.bounds[2] + 0.5 and g.bounds[1] - 0.5 <= lat[i] <= g.bounds[3] + 0.5]
                if d and min(d)[0] < 0.3: cidx[i] = min(d)[1]
        if self.ant: cidx[(cidx < 0) & (lat < -60)] = self.ant[0]
        return cidx
    def lookup(self, lat, lon):
        """Returns per point: country name or None, town name or None, town distance km, border distance km."""
        sh = self.shapely; lat, lon = np.asarray(lat, "float64"), np.asarray(lon, "float64"); N = len(lat); cidx = np.full(N, -1, int)
        for k, (_, _, g) in enumerate(self.C):
            x0, y0, x1, y1 = g.bounds; m = (cidx < 0) & (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
            if m.any(): cidx[np.where(m)[0][sh.contains_xy(g, lon[m], lat[m])]] = k
        for i in np.where(cidx < 0)[0]:           # coast points just outside the simplified outline: nearest country within 0.3 degrees
            p = sh.Point(lon[i], lat[i]); d = [(g.distance(p), k) for k, (_, _, g) in enumerate(self.C) if g.bounds[0] - 0.5 <= lon[i] <= g.bounds[2] + 0.5 and g.bounds[1] - 0.5 <= lat[i] <= g.bounds[3] + 0.5]
            if d and min(d)[0] < 0.3: cidx[i] = min(d)[1]
        if self.ant: cidx[(cidx < 0) & (lat < -60)] = self.ant[0]
        P = self.xyz(lat, lon); km = lambda d: 2 * 6371 * np.arcsin(np.clip(d / 2, 0, 1)); country, town, tkm = [], [], []
        for i in range(N):
            k = cidx[i]; country.append(self.C[k][0] if k >= 0 else None)
            if k in self.towns: d, j = self.towns[k][0].query(P[i]); town.append(self.towns[k][1][j]); tkm.append(float(km(d)))
            else: town.append(None); tkm.append(0.0)
        bd, _ = self.border.query(P); return country, town, tkm, [float(v) for v in km(bd)]
