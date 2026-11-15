"""Vectorised Analog Figure of Merit over the whole Earth library. Same maths as score.py."""
import numpy as np
T_RANGE, DARK_H = 200.0, 120.0
H_RANGE, RET_RANGE = 0.4, 0.5   # team-set normalisers for the scaling number and for slope retention (slope at 320 m / slope at 80 m)
W = {"mobility": {"slope": .50, "scale": .50}, "shadow": {"classes": .35, "lowsun": .35, "t_cold": .30}, "darkness": {"dark": .45, "t_cold": .35, "lowsun": .20}}
GATE = {"mobility": True, "shadow": True, "darkness": False}
def classes(h): return np.stack([h[..., :5].sum(-1), h[..., 5:10].sum(-1), h[..., 10:20].sum(-1), h[..., 20:].sum(-1)], -1)
def load():
    z = np.load("data/cache/library_v2.npz"); s = z["s"]; c = {k: s[:, i] for i, k in enumerate(z["cols"])}; c["hist"] = z["hist"]; c["cls"] = classes(z["hist"]); return c
def foms(L, m):
    """m: lunar spot dict with slope_hist, tri_p50, tri_p90, t_avg, t_max."""
    mh = np.array(m["slope_hist"], "float32"); mc = classes(mh)
    rat = lambda a, b: 1 - np.abs(a - b) / np.maximum(np.maximum(a, b), 1e-9)
    nd = L["ndvi"]
    return {"slope": 1 - 0.5 * np.abs(L["hist"] - mh).sum(1), "classes": 1 - 0.5 * np.abs(L["cls"] - mc).sum(1),
            "rough": 0.5 * (rat(L["tri_p50"], m["tri_p50"]) + rat(L["tri_p90"], m["tri_p90"])),
            "scale": 0.5 * (np.clip(1 - np.abs(L["hurst"] - m["hurst"]) / H_RANGE, 0, 1)
                            + np.clip(1 - np.abs(L["slope320_p50"] / np.maximum(L["slope_p50"], 1e-6) - m["slope320_p50"] / max(m["slope_p50"], 1e-6)) / RET_RANGE, 0, 1)),
            "bare": np.where(np.isnan(nd), 1.0, np.clip(1 - (nd - 0.2) / 0.4, 0, 1)),
            "reliable": (L["slope_p50"] >= 1.0).astype("float32"),   # near-flat Earth windows: radar noise is comparable to relief
            "lowsun": np.clip(L["lowsun"], 0, 1),
            "dark": np.clip(L["dark_h"] / DARK_H, 0, 1),
            "t_peak": np.nan_to_num(np.clip(1 - np.abs(L["t_day_max"] - m["t_max"]) / T_RANGE, 0, 1)),
            "t_cold": np.nan_to_num(np.clip(1 - np.abs(L["t_night_min"] - m["t_avg"]) / T_RANGE, 0, 1))}
def afom(f, p):
    s = sum(f[k] * w for k, w in W[p].items()); return s * f["bare"] * f["reliable"] if GATE[p] else s
if __name__ == "__main__":
    import json
    L = load(); moon = json.load(open("data/out/moon_profiles.json")); names = {"mobility": "Rover driving", "shadow": "Shadow work", "darkness": "Darkness survival"}
    for t in moon:
        f = foms(L, t["features"])
        for p in W:
            a = afom(f, p); o = np.argsort(-a); seen, top = set(), []
            for i in o:
                k = (int(np.floor(L["lat"][i] / 2)), int(np.floor(L["lon"][i] / 2)))       # one per 2-degree square
                if k in seen: continue
                seen.add(k); top.append(i)
                if len(top) == 6: break
            print(f'{t["name"]:18s} {names[p]:18s} >0.8: {int((a > .8).sum()):6d} | ' + "  ".join(f'{a[i]:.2f}@({L["lat"][i]:.1f},{L["lon"][i]:.1f})' for i in top))
