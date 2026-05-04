from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.api.routes import router as etc_router

_ROOT = Path(__file__).resolve().parents[2]
_FIGURES = _ROOT / "outputs" / "thesis_figures"
_PROJECT_MATERIALS = _ROOT / "project_materials"
_FRONTEND_DIST = _ROOT / "web" / "app" / "dist"

origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app = FastAPI(
    title="MKID-IFTS Web ETC",
    description="Analytical exposure-time calculator for the mkid-ifts-sim package.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(etc_router)

if _FIGURES.is_dir():
    app.mount("/figures", StaticFiles(directory=str(_FIGURES)), name="figures")

if _PROJECT_MATERIALS.is_dir():
    app.mount("/project-materials", StaticFiles(directory=str(_PROJECT_MATERIALS)), name="project_materials")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
