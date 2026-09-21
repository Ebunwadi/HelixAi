from helix_api.app import create_app

app = create_app()


def main() -> None:
    """Run the API without development-only auto reload."""
    import uvicorn

    uvicorn.run("helix_api.main:app", host="0.0.0.0", port=8000)
