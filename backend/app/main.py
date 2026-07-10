from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.api.errors import AppError, app_error_handler, validation_error_handler
from app.api.router import api_router
from app.config import get_settings
from app.observability.logging import configure_logging
from app.observability.middleware import request_id_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Contract Intelligence Agent",
        version="0.1.0",
        description="Clause-aware contract ingestion and analysis API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.include_router(api_router)
    return app


app = create_app()
