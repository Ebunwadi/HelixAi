import hashlib
import math

from openai import APIError, AsyncOpenAI

from helix_api.core.errors import ModelProviderError


class MockEmbeddingGateway:
    """Deterministic local embedding implementation.

    It hashes tokens into a fixed-size vector. This is not intended to match the
    semantic quality of a trained embedding model; it exists so the complete RAG
    pipeline can run locally and in CI with no cloud dependency.
    """

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]


class AzureOpenAIEmbeddingGateway:
    """Generate embeddings with an Azure OpenAI v1 deployment."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        deployment: str,
        dimensions: int,
    ) -> None:
        self.deployment = deployment
        self.dimensions = dimensions
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/v1/",
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self.client.embeddings.create(
                model=self.deployment,
                input=texts,
                dimensions=self.dimensions,
            )
        except APIError as exc:
            raise ModelProviderError("Embedding generation failed") from exc

        # The API returns one vector per input in the same logical request.
        return [item.embedding for item in response.data]
