from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helix_api.api.router import api_router
from helix_api.core.config import get_settings
from helix_api.core.errors import register_exception_handlers
from helix_api.core.middleware import CorrelationIdMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="HelixAI API",
        version="0.2.0",
        description="HelixAI customer operations API.",
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    return app
