"""Country of every window in the overlapping-square library, so the scoring service can filter by country. Writes data/cache/lib3/country.npy (uint8 index)
and country_names.json. Usage: python pipeline/places3.py START END  (run in parts), then python pipeline/places3.py merge"""
import sys, glob, json, numpy as np
sys.path.insert(0, "pipeline"); from placelib import Places
D = "data/cache/lib3/"
if sys.argv[1] == "merge":
    S = np.load(D + "s.npy", mmap_mode="r"); out = np.full(len(S), 255, "uint8")
    for f in glob.glob(D + "country_part_*.npy"):
        a = int(f.split("_")[-1][:-4]); v = np.load(f); out[a:a + len(v)] = v
    names = json.load(open(D + "country_names.json")); np.save(D + "country.npy", out); print("no country:", int((out == 255).sum()), "| countries present:", len(np.unique(out)) - 1)
else:
    a, b = int(sys.argv[1]), int(sys.argv[2]); S = np.load(D + "s.npy", mmap_mode="r"); P = Places("data/cache/countries-50m.json")
    c = P.country_index(np.array(S[a:b, 0]), np.array(S[a:b, 1])); assert len(P.C) < 255
    np.save(D + f"country_part_{a}.npy", np.where(c < 0, 255, c).astype("uint8")); json.dump([x[0] for x in P.C], open(D + "country_names.json", "w")); print(a, b, "no country", int((c < 0).sum()))
