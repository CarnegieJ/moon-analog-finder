"""Phase 3: add temperature, vegetation and sun/darkness numbers to Moon targets and Earth sites."""
import json, math, numpy as np
R_MOON = 1737.4
def sun_stats(lat, low_thresh):
    """Earth, from solar geometry (no data): max sun elevation, longest continuous darkness (h),
    share of daylight hours with the sun below low_thresh degrees."""
    phi = math.radians(lat); el = []
    for doy in range(365):
        dec = math.radians(-23.44 * math.cos(2 * math.pi * (doy + 10) / 365))
        for h in np.arange(0, 24, 0.25):
            ha = math.radians(15 * (h - 12))
            el.append(math.degrees(math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha))))
    el = np.array(el); up = el > 0
    run = best = 0
    for u in np.concatenate([up, up]):          # wrap the year
        run = 0 if u else run + 1; best = max(best, run)
    return {"sun_max_elev": float(el.max()), "dark_longest_h": float(min(best, len(el)) * 0.25),
            "lowsun_share": float(((el > 0) & (el < low_thresh)).sum() / max(up.sum(), 1))}

if __name__ == "__main__":
    dv = np.load("data/cache/diviner_south.npz"); md = np.load("data/cache/modis.npz")
    r = 2 * R_MOON * np.tan(np.radians(90 + dv["lat"]) / 2); dx = r * np.sin(np.radians(dv["lon"])); dy = r * np.cos(np.radians(dv["lon"]))
    moon = json.load(open("data/out/moon_profiles.json"))
    for t in moon:
        m = (np.abs(dx - t["x"] / 1000) <= t["window_km"] / 2) & (np.abs(dy - t["y"] / 1000) <= t["window_km"] / 2)
        ice = dv["ice"][m]; f = t["features"]
        f.update({"t_avg": float(np.median(dv["tavg"][m])), "t_max": float(np.median(dv["tmax"][m])), "t_max_p90": float(np.percentile(dv["tmax"][m], 90)),
                  "t_avg_min": float(dv["tavg"][m].min()), "ice_share": float((ice > -900).mean()),
                  "ice_depth_med": float(np.median(ice[ice > -900])) if (ice > -900).any() else None,
                  "sun_max_elev": 90 - abs(t["lat"]) + 1.54, "n_diviner": int(m.sum())})
        print(t["name"], {k: (round(v, 2) if isinstance(v, float) else v) for k, v in f.items() if k[:2] in ("t_", "ic", "su", "n_")})
    json.dump(moon, open("data/out/moon_profiles.json", "w"), indent=1)

    def cell(g, lat, lon):
        i, j = int((90 - lat) / 0.05), int((lon + 180) / 0.05)
        w = g[max(i-1, 0):i+2, max(j-1, 0):j+2]
        return float(np.nanmedian(w)) if np.isfinite(w).any() else None
    earth = json.load(open("data/out/earth_profiles.json"))
    LOW = 12.0   # sun never rises above about 11.5 degrees anywhere poleward of 80 S on the Moon
    for s in earth:
        f = s["features"]
        f.update({"t_day_max": cell(md["day_max"], s["lat"], s["lon"]), "t_night_min": cell(md["night_min"], s["lat"], s["lon"]),
                  "t_night_mean": cell(md["night_mean"], s["lat"], s["lon"]), "ndvi_max": cell(md["ndvi_max"], s["lat"], s["lon"])})
        f.update(sun_stats(s["lat"], LOW))
        print(f'{s["name"][:32]:32s} dayMax {f["t_day_max"]} nightMin {f["t_night_min"]} ndvi {f["ndvi_max"]} dark {f["dark_longest_h"]:.0f}h lowsun {f["lowsun_share"]:.2f}')
    json.dump(earth, open("data/out/earth_profiles.json", "w"), indent=1)

