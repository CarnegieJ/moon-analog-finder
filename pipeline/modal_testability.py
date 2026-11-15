"""Overnight job: for every lunar spot (11,221), score the whole Earth library and record how well Earth can stand in for it.
Output: data/out/testability.json, one row per lunar spot and purpose: best Earth score, how many Earth windows reach 0.7 and 0.8,
and where the best one is. Pure arithmetic on files already built; no downloads.
Run from the project folder:  modal run pipeline/modal_testability.py"""
import json, os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App("moon-analogs-testability")
image = modal.Image.debian_slim(python_version="3.11").pip_install("numpy")
if modal.is_local():
    image = (image.add_local_file(os.path.join(HERE, "lib_score.py"), "/root/lib_score.py")
                  .add_local_file(os.path.join(ROOT, "data", "cache", "library_v2.npz"), "/root/data/cache/library_v2.npz")
                  .add_local_file(os.path.join(ROOT, "data", "out", "moon_grid.json"), "/root/data/out/moon_grid.json"))
_S = None

def score_chunk(idx, root="."):
    """Shared by the cloud worker and the local test."""
    import sys, numpy as np
    global _S
    if _S is None:
        os.chdir(root); sys.path.insert(0, root if root != "." else os.path.dirname(os.path.abspath(__file__)))
        import lib_score as ls
        _S = (ls, ls.load(), json.load(open("data/out/moon_grid.json")))
    ls, L, grid = _S; out = []
    for i in idx:
        g = grid[i]
        if g.get("t_avg") is None: g = dict(g, t_avg=float("nan"), t_max=float("nan"))
        f = ls.foms(L, g); row = {"i": i, "x": g["x"], "y": g["y"]}
        for p in ls.W:
            a = np.nan_to_num(ls.afom(f, p)); j = int(np.argmax(a))
            row[p] = {"best": round(float(a[j]), 3), "n07": int((a >= 0.7).sum()), "n08": int((a >= 0.8).sum()), "lat": round(float(L["lat"][j]), 2), "lon": round(float(L["lon"][j]), 2)}
        out.append(row)
    return out

@app.function(image=image, timeout=1800, retries=2, max_containers=40, memory=4096)
def worker(idx: list):
    return score_chunk(idx, "/root")

@app.local_entrypoint()
def main():
    n = len(json.load(open(os.path.join(ROOT, "data", "out", "moon_grid.json"))))
    chunks = [list(range(s, min(s + 100, n))) for s in range(0, n, 100)]
    print(f"{n} lunar spots in {len(chunks)} chunks")
    rows, done = [], 0
    for res in worker.map(chunks, return_exceptions=True, order_outputs=False):
        if isinstance(res, Exception): print("  failed chunk:", str(res)[:120]); continue
        rows += res; done += 1
        if done % 20 == 0: print(f"  {done}/{len(chunks)} chunks")
    rows.sort(key=lambda r: r["i"])
    json.dump(rows, open(os.path.join(ROOT, "data", "out", "testability.json"), "w"))
    print(f"Done: {len(rows)} of {n} lunar spots scored. Saved data/out/testability.json")
