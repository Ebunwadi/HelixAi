import pytest_asyncio

from helix_api.db.session import dispose_engine


@pytest_asyncio.fixture(autouse=True)
async def dispose_shared_engine_after_test():
    """Keep pooled asyncpg connections from leaking across pytest event loops."""
    yield
    await dispose_engine()
