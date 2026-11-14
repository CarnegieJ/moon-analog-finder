"""Rebuilds workspace/data.js from pipeline outputs + workspace/notes.json. Run after every step."""
import json, os, datetime
d = {"updated": datetime.datetime.now().strftime("%a %b %d, %H:%M UTC"), "notes": json.load(open("workspace/notes.json"))}
for k, p in [("moon", "data/out/moon_profiles.json"), ("earth", "data/out/earth_profiles.json"), ("scores", "data/out/scores.json")]:
    d[k] = json.load(open(p)) if os.path.exists(p) else None
open("workspace/data.js", "w").write("window.WS = " + json.dumps(d) + ";")
print("workspace/data.js written")
