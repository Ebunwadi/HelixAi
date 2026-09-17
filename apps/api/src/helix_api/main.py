from fastapi import FastAPI

app = FastAPI(
    title="HelixAI API",
    version="0.1.0",
    description="HelixAI customer operations API.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run("helix_api.main:app", host="0.0.0.0", port=8000, reload=True)


def main() -> None:
    run()
