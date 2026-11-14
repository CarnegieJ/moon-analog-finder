"""Hosts the Moon Analog Finder (the static app folder) on Modal at a public URL.
Deploy from the project folder:  modal deploy pipeline/modal_host.py     (re-run after any change to app/)"""
import os
import modal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = modal.App("moon-analog-finder")
image = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi[standard]")
if modal.is_local():
    image = image.add_local_dir(os.path.join(ROOT, "app"), "/root/site")

@app.function(image=image, scaledown_window=600, max_containers=2)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def web():
    from fastapi import FastAPI
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.staticfiles import StaticFiles
    api = FastAPI()
    api.add_middleware(GZipMiddleware, minimum_size=1000)
    api.mount("/", StaticFiles(directory="/root/site", html=True), name="site")
    return api
