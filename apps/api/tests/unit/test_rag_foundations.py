from uuid import uuid4

import pytest

from helix_api.rag.chunking import chunk_text
from helix_api.rag.embeddings import MockEmbeddingGateway
from helix_api.rag.search import LocalSearchIndex
from helix_api.rag.types import IndexedChunk


def test_chunk_text_creates_ordered_overlapping_chunks() -> None:
    text = " ".join(f"word-{index}" for index in range(250))

    chunks = chunk_text(text, chunk_size=240, overlap=40)

    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= 240 for chunk in chunks)


@pytest.mark.asyncio
async def test_local_vector_index_returns_tenant_scoped_match(tmp_path) -> None:
    embeddings = MockEmbeddingGateway(dimensions=32)
    index = LocalSearchIndex(tmp_path / "index.json")

    tenant_id = uuid4()
    other_tenant_id = uuid4()
    knowledge_base_id = uuid4()

    relevant_vector = (await embeddings.embed(["saml certificate rotation login"]))[0]
    unrelated_vector = (await embeddings.embed(["billing invoice payment"]))[0]

    relevant_id = uuid4()
    await index.index_chunks(
        [
            IndexedChunk(
                chunk_id=relevant_id,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=uuid4(),
                filename="sso.md",
                chunk_index=0,
                content="Check the SAML signing certificate when SSO login fails.",
                embedding=relevant_vector,
            ),
            IndexedChunk(
                chunk_id=uuid4(),
                tenant_id=other_tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=uuid4(),
                filename="private.md",
                chunk_index=0,
                content="A different tenant's private document.",
                embedding=relevant_vector,
            ),
            IndexedChunk(
                chunk_id=uuid4(),
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=uuid4(),
                filename="billing.md",
                chunk_index=0,
                content="Billing and invoice guidance.",
                embedding=unrelated_vector,
            ),
        ]
    )

    query_vector = (await embeddings.embed(["saml certificate login"]))[0]
    hits = await index.search(
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        query_embedding=query_vector,
        top_k=2,
    )

    assert hits
    assert hits[0].chunk_id == relevant_id
    assert all(hit.filename != "private.md" for hit in hits)
