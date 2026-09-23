from helix_api.app import create_app
from helix_api.core.config import get_settings

# Uvicorn imports this ASGI application when we run "helix_api.main:app".
app = create_app()


def main() -> None:
    """Run the API without development-only auto reload."""
    import uvicorn

    settings = get_settings()

    # Read host/port from configuration so local and deployed environments can
    # choose their own network settings without changing application code.
    uvicorn.run(
        "helix_api.main:app",
        host=settings.helix_api_host,
        port=settings.helix_api_port,
    )
