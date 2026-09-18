"""Application entry point.

Assembles the storefront, the staff console and the public API into one ASGI
app. Run with:

    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import settings
from apps.admin.routes import router as admin_router
from apps.api.routes import router as api_router
from apps.storefront.routes import router as storefront_router
from data import db

app = FastAPI(title="LocalBooks", version="1.4.0")

app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

app.include_router(storefront_router)
app.include_router(admin_router)
app.include_router(api_router)


@app.on_event("startup")
def ensure_schema() -> None:
    db.init_schema()


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok", "checkout": "v2" if settings.FEATURE_NEW_CHECKOUT else "v1"}
