from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import ocr, templates, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="SnapSheet",
        description="拍表 - 酒店手写表单OCR识别与Excel转换服务",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router, tags=["health"])
    app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
    app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])

    # Ensure upload/output/templates dirs exist
    from app.config import settings
    os.makedirs(settings.uploads_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    os.makedirs(settings.templates_dir, exist_ok=True)

    # Serve static frontend
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
