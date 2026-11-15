"""Scoring over the full overlapping-square library (3.8 million windows). Used by the Modal web service and testable locally.
Same factor maths as lib_score.py and app/app.js. A request gives the lunar spot's fingerprint and the purpose weights; the answer holds
the best window per 2-degree region, the known analog sites, counts by terrain level and a placement error per returned site."""
import base64, csv, numpy as np
T_RANGE, DARK_H, H_RANGE, RET_RANGE = 200.0, 120.0, 0.4, 0.5
STRONG, POSSIBLE = 0.87, 0.80                               # terrain levels from the identity test (docs/BENCHMARK.md)
ECOLS = ["lat", "lon", "ndvi", "t_day_max", "t_night_min", "dark_h", "lowsun", "slope_p50", "relief", "hurst", "slope320_p50", "nomask", "pzi", "alt"]
b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
class Library:
    def __init__(self, d, known_csv, places=None, keep_float=False):
        from scipy.spatial import cKDTree
        s = np.load(d + "/s.npy"); cols = open(d + "/cols.txt").read().split(); self.c = {k: np.ascontiguousarray(s[:, i]) for i, k in enumerate(cols)}; del s
        self.c["pzi"] = np.load(d + "/pzi.npy"); self.c["alt"] = np.load(d + "/alt.npy") if __import__("os").path.exists(d + "/alt.npy") else np.full(len(self.c["lat"]), np.nan, "float32"); self.country = np.load(d + "/country.npy"); self.cnames = __import__("json").load(open(d + "/country_names.json")); self.cpresent = [self.cnames[k] for k in np.unique(self.country) if k < 255]; self.h16 = np.load(d + "/hist.npy"); self.N = len(self.h16); c = self.c
        self.hf = (self.h16.astype("float32") / 10000) if keep_float else None
        cls = np.zeros((self.N, 4), "float32")
        for a in range(0, self.N, 400000):
            h = self.h16[a:a + 400000].astype("float32") / 10000; cls[a:a + 400000] = np.stack([h[:, :5].sum(1), h[:, 5:10].sum(1), h[:, 10:20].sum(1), h[:, 20:].sum(1)], 1)
        self.cls = cls; self.ret = c["slope320_p50"] / np.maximum(c["slope_p50"], 1e-6)
        self.bare = np.where(np.isnan(c["ndvi"]), 1.0, np.clip(1 - (c["ndvi"] - 0.2) / 0.4, 0, 1)).astype("float32"); self.reliable = (c["slope_p50"] >= 1.0).astype("float32")
        self.cell = (np.floor(c["lat"] / 2).astype("int32") + 45) * 180 + (np.floor(c["lon"] / 2).astype("int32") + 90)
        la, lo = np.radians(c["lat"].astype("float64")), np.radians(c["lon"].astype("float64")); self.P = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)].astype("float32"); self.tree = cKDTree(self.P)
        self.known = [r for r in csv.DictReader(open(known_csv)) if r["status"].startswith("verified")]; self.kidx = []
        for k in self.known:
            kla, klo = float(k["lat"]), float(k["lon"]); self.kidx.append(np.where((np.abs(c["lat"] - kla) < 0.3) & (np.abs(c["lon"] - klo) * np.cos(np.radians(kla)) < 0.3))[0])
        self.places = places
    def factors(self, m):
        c = self.c; mh = np.array(m["hist"], "float32"); slope = np.empty(self.N, "float32")
        for a in range(0, self.N, 400000):
            h = self.hf[a:a + 400000] if self.hf is not None else self.h16[a:a + 400000].astype("float32") / 10000; slope[a:a + 400000] = 1 - 0.5 * np.abs(h - mh).sum(1)
        mc = np.array([mh[:5].sum(), mh[5:10].sum(), mh[10:20].sum(), mh[20:].sum()], "float32"); pz = np.nan_to_num(self.c["pzi"]); ice = float(m.get("ice") or 0)
        nz = lambda v: np.nan_to_num(np.clip(v, 0, 1))
        return {"slope": np.clip(slope, 0, 1), "classes": np.clip(1 - 0.5 * np.abs(self.cls - mc).sum(1), 0, 1),
                "scale": 0.5 * (np.clip(1 - np.abs(c["hurst"] - m["hurst"]) / H_RANGE, 0, 1) + np.clip(1 - np.abs(self.ret - m["ret"]) / RET_RANGE, 0, 1)),
                "lowsun": np.clip(c["lowsun"], 0, 1), "dark": np.clip(c["dark_h"] / DARK_H, 0, 1),
                "t_cold": nz(1 - np.abs(c["t_night_min"] - m["t_avg"]) / T_RANGE) if m.get("t_avg") is not None else np.zeros(self.N, "float32"),
                "t_peak": nz(1 - np.abs(c["t_day_max"] - m["t_max"]) / T_RANGE) if m.get("t_max") is not None else np.zeros(self.N, "float32"),
                "frozen": (np.minimum(pz, ice) / np.maximum(np.maximum(pz, ice), 1e-9)).astype("float32")}
    def dist_km(self, la, lo):
        a, b = np.radians(self.c["lat"]), np.radians(la); return 6371 * 2 * np.arcsin(np.sqrt(np.sin((a - b) / 2) ** 2 + np.cos(a) * np.cos(b) * np.sin(np.radians(self.c["lon"] - lo) / 2) ** 2))
    def score(self, m, w, gate, top_regions=300, flt=None):
        """flt (all optional): {"countries": [names], "near": [lat, lon, km], "max_alt": metres, "probe": [lat, lon]}. The search is limited to the countries and/or the circle;
        the probe is one Earth place the user wants scored, returned whether or not it ranks."""
        flt = flt or {}; mask = None
        if flt.get("countries"): ids = [self.cnames.index(n) for n in flt["countries"] if n in self.cnames]; mask = np.isin(self.country, ids)
        if flt.get("near"): la, lo, r = [float(v) for v in flt["near"]]; nm = self.dist_km(la, lo) <= r; mask = nm if mask is None else (mask & nm)
        if flt.get("max_alt") is not None: am = ~(self.c["alt"] > float(flt["max_alt"])); mask = am if mask is None else (mask & am)      # squares with no altitude are kept
        f = self.factors(m); a = np.zeros(self.N, "float32")
        for k, v in w.items(): a += f[k] * float(v)
        terr = (0.5 * f["slope"] + 0.5 * f["scale"]) * self.bare * self.reliable
        if gate == "bare": a *= self.bare
        elif gate: a *= self.bare * self.reliable
        full = a
        if mask is not None:
            if not mask.any(): return {"k": 0, "stats": {"n": 0}, "empty": "No library squares inside this search area."}
            a = np.where(mask, a, -1).astype("float32")
        best = float(a.max()); ties = int((a >= best - 0.01).sum())
        stats = {"n": int(self.N if mask is None else mask.sum()), "filtered": mask is not None, "best": best, "strong": int((a >= STRONG).sum()), "possible": int(((a >= POSSIBLE) & (a < STRONG)).sum()), "ties": ties}
        if ties > 50: cand = np.where(a >= best - 0.01)[0]; cand = cand[np.argsort(-terr[cand])]          # a large tie: order the tied sites by terrain likeness
        else: cand = np.argpartition(-a, min(400000, self.N - 1))[:400000]; cand = cand[np.argsort(-a[cand])]
        _, first = np.unique(self.cell[cand], return_index=True); top = cand[np.sort(first)][:top_regions]; top = top[a[top] >= 0]
        a = full; kn = [int(ix[np.argmax(a[ix])]) if len(ix) else -1 for ix in self.kidx]; sel = list(top) + [k for k in kn if k >= 0 and k not in set(top.tolist())]; probe = None
        if flt.get("probe"):                       # the library square whose centre is nearest to the place asked about
            pla, plo = [float(v) for v in flt["probe"]]; d = self.dist_km(pla, plo); g = int(d.argmin()); probe = {"km": float(d[g]), "g": g if d[g] <= 6 else -1}
            if probe["g"] >= 0 and probe["g"] not in sel: sel.append(probe["g"])
        sel = np.array(sel); pos = {int(g): i for i, g in enumerate(sel)}
        # placement error: how much the score changes among the overlapping squares within 3.7 km of each returned site
        nb = self.tree.query_ball_point(self.P[sel], 2 * np.sin(3.7 / 6371 / 2)); spread = np.array([float(np.abs(a[x] - a[i]).sum() / max(len(x) - 1, 1)) for x, i in zip(nb, sel)], "float32"); nnb = [len(x) - 1 for x in nb]
        c = self.c; meta = np.stack([c[k][sel] for k in ECOLS], 1).astype("float32"); hist = self.h16[sel]
        out = {"stats": stats, "n_top": int(len(top)), "k": int(len(sel)), "cols": ECOLS, "meta": b64(meta), "hist": b64(hist), "hist_scale": 10000, "scores": b64(a[sel]), "terr": b64(terr[sel]), "spread": b64(spread), "neighbours": nnb,
               "known": [{"name": k["name"], "idx": pos.get(g, -1)} for k, g in zip(self.known, kn)],
               "probe": None if probe is None else {"idx": pos.get(probe["g"], -1), "km": round(probe["km"], 1)}}
        if self.places is not None:
            co, tw, tkm, bkm = self.places.lookup(c["lat"][sel], c["lon"][sel]); cn = sorted({x for x in co if x}); tn = sorted({x for x in tw if x}); ci = {x: i for i, x in enumerate(cn)}; ti = {x: i for i, x in enumerate(tn)}
            pl = np.array([[ci.get(a_, 65535), ti.get(b_, 65535), min(round(k_), 65535), min(round(d_), 65535)] for a_, b_, k_, d_ in zip(co, tw, tkm, bkm)], "uint16")
            out["place"] = b64(pl); out["place_names"] = {"countries": cn, "towns": tn}
        return out
if __name__ == "__main__":
    import json, sys, time
    sys.path.insert(0, "pipeline"); from placelib import Places
    t = time.time(); L = Library("data/cache/lib3", "pipeline/known_sites.csv", Places("data/cache/countries-50m.json")); print("loaded", L.N, round(time.time() - t), "s")
    for t_ in json.load(open("data/out/moon_profiles.json")):
        f = t_["features"]; m = {"hist": f["slope_hist"], "hurst": f["hurst"], "ret": f["slope320_p50"] / max(f["slope_p50"], 1e-6), "t_avg": f.get("t_avg"), "t_max": f.get("t_max"), "ice": f.get("ice_share")}
        t = time.time(); r = L.score(m, {"slope": .5, "scale": .5}, True); k = r["k"]; sc = np.frombuffer(base64.b64decode(r["scores"]), "float32"); sp = np.frombuffer(base64.b64decode(r["spread"]), "float32")
        meta = np.frombuffer(base64.b64decode(r["meta"]), "float32").reshape(k, -1); pl = np.frombuffer(base64.b64decode(r["place"]), "uint16").reshape(k, 4)
        print(t_["name"], r["stats"], round(time.time() - t, 1), "s | top:", [(round(float(meta[i, 0]), 2), round(float(meta[i, 1]), 2), r["place_names"]["countries"][pl[i, 0]] if pl[i, 0] < 65535 else None, round(float(sc[i]), 3), "+-", round(float(sp[i]), 3)) for i in range(4)], "| json MB", round(len(json.dumps(r)) / 1e6, 2))
