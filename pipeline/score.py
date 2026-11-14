"""Analog Figure of Merit (AFoM). Every factor score is 0..1 (1 = same as the lunar spot).
Distribution scores follow NASA's lunar simulant Figure of Merit (Schrader et al. 2009): the fraction that is the same.
Weights and thresholds below are TEAM-SET (not NASA values); each has a real-use reason in docs/DECISIONS.md."""
import json
import numpy as np
def fom_hist(p, q): return 1 - 0.5 * float(np.abs(np.array(p) - np.array(q)).sum())
def fom_ratio(a, b): return 1 - abs(a - b) / max(a, b, 1e-9)
def clip(v): return float(min(max(v, 0.0), 1.0))
CLS = ["share_lt5", "share_5_10", "share_10_20", "share_gt20"]   # NASA mobility figures: 10 and 20 degrees
T_RANGE = 200.0      # K, normaliser for temperature differences
DARK_TARGET_H = 120  # NASA Moon Base User's Guide 2026: survive 120+ hours of darkness
FACTORS = {"slope": "Slope match", "classes": "Slope classes", "rough": "Roughness", "bare": "Bare surface", "lowsun": "Low sun",
           "dark": "Long darkness", "t_peak": "Peak temperature", "t_cold": "Cold"}
PURPOSES = {
  "mobility": {"name": "Rover driving", "gate_bare": True, "w": {"slope": .35, "classes": .30, "rough": .35}},
  "shadow":   {"name": "Shadow work and crater access", "gate_bare": True, "w": {"classes": .35, "lowsun": .35, "t_cold": .30}},
  "darkness": {"name": "Power and darkness survival", "gate_bare": False, "w": {"dark": .45, "t_cold": .35, "lowsun": .20}},
}
def foms(e, m):
    nd = e.get("ndvi_max")
    return {"slope": fom_hist(e["slope_hist"], m["slope_hist"]),
            "classes": fom_hist([e[c] for c in CLS], [m[c] for c in CLS]),
            "rough": 0.5 * (fom_ratio(e["tri_p50"], m["tri_p50"]) + fom_ratio(e["tri_p90"], m["tri_p90"])),
            "bare": 1.0 if nd is None else clip(1 - (nd - 0.2) / 0.4),          # NDVI <= 0.2 bare, >= 0.6 fully vegetated; no data (ice/rock) = bare
            "lowsun": clip(e["lowsun_share"]),                                 # Moon: sun never above ~12 deg poleward of 80 S, so lunar value = 1
            "dark": clip(e["dark_longest_h"] / DARK_TARGET_H),
            "t_peak": clip(1 - abs(e["t_day_max"] - m["t_max"]) / T_RANGE) if e.get("t_day_max") else 0.0,
            "t_cold": clip(1 - abs(e["t_night_min"] - m["t_avg"]) / T_RANGE) if e.get("t_night_min") else 0.0}
def afom(f, purpose):
    p = PURPOSES[purpose]; s = sum(f[k] * w for k, w in p["w"].items())
    return s * f["bare"] if p["gate_bare"] else s

if __name__ == "__main__":
    moon = json.load(open("data/out/moon_profiles.json")); earth = json.load(open("data/out/earth_profiles.json"))
    res = {"factors": FACTORS, "purposes": PURPOSES, "targets": {}, "html": ""}
    for t in moon:
        T = {"name": t["name"], "purposes": {}}
        for pk, p in PURPOSES.items():
            rows = []
            for s in earth:
                f = foms(s["features"], t["features"])
                rows.append({"id": s["id"], "name": s["name"], "group": s["group"], "f": {k: round(v, 3) for k, v in f.items()}, "afom": round(afom(f, pk), 3)})
            rows.sort(key=lambda r: -r["afom"]); T["purposes"][pk] = rows
            cols = list(p["w"]) + (["bare"] if p["gate_bare"] else [])
            res["html"] += f'<h3>{t["name"]} · {p["name"]}</h3><table><tr><th>Earth site</th><th>Group</th>' + "".join(f"<th>{FACTORS[c]}</th>" for c in cols) + "<th>Score</th></tr>" + "".join(
                f'<tr><td>{i+1}. {r["name"]}</td><td>{r["group"]}</td>' + "".join(f'<td>{r["f"][c]:.2f}</td>' for c in cols) + f'<td><b>{r["afom"]:.2f}</b></td></tr>' for i, r in enumerate(rows)) + "</table>"
            print(f'{t["name"]:18s} {p["name"]:30s}', " | ".join(f'{r["name"].split(" (")[0][:16]} {r["afom"]:.2f}' for r in rows[:5]), " ... last:", rows[-1]["name"][:12], rows[-1]["afom"])
        res["targets"][t["id"]] = T
    json.dump(res, open("data/out/scores.json", "w"), indent=1)
