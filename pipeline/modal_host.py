"""Hosts the Moon Analog Finder on Modal at a public URL: the static app plus the scoring service over the full overlapping-square library.
The library (about 650 MB) lives in the Modal Volume "moon-analogs-lib3"; upload it once with scripts\\upload_library.ps1.
Deploy from the project folder:  modal deploy pipeline/modal_host.py     (re-run after any change to app/ or the scoring code)
Test copy first: set MAF_APP=moon-analog-finder-staging before deploying; it shares the library volume and gets its own URL."""
import os
import modal

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
app = modal.App(os.environ.get("MAF_APP", "moon-analog-finder"))   # MAF_APP=moon-analog-finder-staging deploys a test copy at its own URL
vol = modal.Volume.from_name("moon-analogs-lib3", create_if_missing=True)
image = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi[standard]", "numpy", "scipy", "shapely", "pandas", "pycountry", "reverse_geocoder")
if modal.is_local():
    image = (image.add_local_dir(os.path.join(ROOT, "app"), "/root/site")
                  .add_local_file(os.path.join(HERE, "score_service.py"), "/root/score_service.py")
                  .add_local_file(os.path.join(HERE, "placelib.py"), "/root/placelib.py")
                  .add_local_file(os.path.join(HERE, "known_sites.csv"), "/root/known_sites.csv")
                  .add_local_file(os.path.join(ROOT, "data", "cache", "countries-50m.json"), "/root/countries-50m.json"))

# Keep one container (and the loaded library) running so nobody waits for a cold start. Costs money while deployed:
# on by default for the public app, off for test copies; override with MAF_MIN=0 or MAF_MIN=1 when deploying.
MIN = int(os.environ.get("MAF_MIN", "1" if app.name == "moon-analog-finder" else "0"))
@app.function(image=image, scaledown_window=900, min_containers=MIN, max_containers=2, memory=8192, cpu=4, volumes={"/library": vol})
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def web():
    import sys, threading
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.staticfiles import StaticFiles
    sys.path.insert(0, "/root")
    state = {"lib": None, "err": None}; ready = threading.Event()
    def load():                                    # the pages are served at once; the library loads in the background
        try:
            from score_service import Library
            from placelib import Places
            state["lib"] = Library("/library", "/root/known_sites.csv", Places("/root/countries-50m.json"), keep_float=True)
        except Exception as e: state["err"] = repr(e)
        ready.set()
    threading.Thread(target=load, daemon=True).start()
    api = FastAPI()
    api.add_middleware(GZipMiddleware, minimum_size=1000)
    @api.middleware("http")
    async def fresh_pages(request, call_next):
        # Files in the container all carry the same 1970 timestamp, so the default caching headers made browsers keep an old page
        # after a deploy. Pages, scripts and styles are therefore never cached and never answered with "not modified".
        p = request.url.path; page = p.endswith((".html", ".js", ".css", "/")) or p == ""
        if page: request.scope["headers"] = [(k, v) for k, v in request.scope["headers"] if k not in (b"if-none-match", b"if-modified-since")]
        resp = await call_next(request)
        if page:
            resp.headers["Cache-Control"] = "no-store"
            for h in ("etag", "last-modified"):
                if h in resp.headers: del resp.headers[h]
        return resp
    @api.get("/api/status")
    def status():
        return {"ready": ready.is_set() and state["lib"] is not None, "error": state["err"], "windows": state["lib"].N if state["lib"] else None, "countries": state["lib"].cpresent if state["lib"] else []}
    @api.post("/api/score")
    def score(req: dict):                          # plain function: runs in a worker thread, so the pages stay responsive
        if not ready.wait(timeout=120) or state["lib"] is None: return JSONResponse({"error": state["err"] or "library still loading"}, status_code=503)
        m = req.get("moon") or {}; w = req.get("w") or {}
        ok = isinstance(m.get("hist"), list) and len(m["hist"]) == 46 and all(k in ("slope", "classes", "scale", "lowsun", "dark", "t_cold", "t_peak", "frozen") for k in w) and len(w) > 0
        if not ok: return JSONResponse({"error": "bad request"}, status_code=400)
        try:
            m = {"hist": [float(v) for v in m["hist"]], "hurst": float(m["hurst"]), "ret": float(m["ret"]), "t_avg": m.get("t_avg"), "t_max": m.get("t_max"), "ice": float(m.get("ice") or 0)}
            flt = req.get("flt") if isinstance(req.get("flt"), dict) else None
            return state["lib"].score(m, {k: float(v) for k, v in w.items()}, req.get("gate"), flt=flt)
        except Exception as e: return JSONResponse({"error": repr(e)[:200]}, status_code=500)
    api.mount("/", StaticFiles(directory="/root/site", html=True), name="site")
    return api
