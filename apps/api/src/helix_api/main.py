from fastapi import FastAPI

app = FastAPI(
    title="HelixAI API",
    version="0.1.0",
    description="HelixAI customer operations API.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    """Run the API without development-only auto reload."""
    import uvicorn

    uvicorn.run("helix_api.main:app", host="0.0.0.0", port=8000)
