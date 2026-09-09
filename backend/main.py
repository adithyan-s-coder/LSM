"""
main.py — Last-Safe-Moment Engine API entrypoint.

Run with (from inside backend/):
    uvicorn main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import logging

from database import Base, engine
import models  # noqa: F401  (ensures models are registered on Base before create_all)

from routers import auth, dashboard, assets, data, predictions, intervention, maintenance, alerts, analytics, simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("last_safe_moment")

app = FastAPI(
    title="Last-Safe-Moment Engine API",
    description="Predictive-maintenance decision-support API. "
                 "Don't just predict failure. Find the last safe moment to act.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")


# Never leak raw stack traces to the client (spec section 45).
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(data.router)
app.include_router(predictions.router)
app.include_router(intervention.router)
app.include_router(maintenance.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(simulation.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "last-safe-moment-engine"}


# Serve the plain HTML/CSS/JS frontend directly from FastAPI so the whole
# app can be run with a single `uvicorn` command during the demo.
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
