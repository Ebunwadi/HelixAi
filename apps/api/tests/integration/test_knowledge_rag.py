import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from helix_api.db.session import get_session_factory
from helix_api.main import app
from helix_api.modules.knowledge.models import Document, DocumentChunk, KnowledgeBase
from helix_api.modules.tenants.models import Membership, MembershipRole, MembershipStatus, Tenant
from helix_api.modules.users.models import User

pytestmark = pytest.mark.skipif(
    os.getenv("HELIX_RUN_DB_TESTS") != "1",
    reason="Database integration tests require HELIX_RUN_DB_TESTS=1",
)


@pytest.mark.asyncio
async def test_upload_retrieve_and_answer_from_tenant_knowledge() -> None:
    factory = get_session_factory()
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    user_id = uuid4()
    subject = f"rag-{uuid4()}"

    async with factory() as session:
        tenant = Tenant(id=tenant_id, name="RAG Tenant", slug=f"rag-{uuid4()}")
        other_tenant = Tenant(
            id=other_tenant_id,
            name="Other Tenant",
            slug=f"other-{uuid4()}",
        )
        user = User(
            id=user_id,
            external_identity_id=subject,
            email="rag@example.com",
        )
        session.add_all([tenant, other_tenant, user])
        await session.flush()

        session.add(
            Membership(
                tenant_id=tenant_id,
                user_id=user_id,
                role=MembershipRole.OPERATOR,
                status=MembershipStatus.ACTIVE,
            )
        )
        private_kb = KnowledgeBase(
            tenant_id=other_tenant_id,
            name=f"Private {uuid4()}",
        )
        session.add(private_kb)
        await session.commit()
        private_kb_id = private_kb.id

    headers = {
        "X-Helix-Subject": subject,
        "X-Helix-Tenant-Id": str(tenant_id),
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/knowledge-bases",
            headers=headers,
            json={"name": f"Support {uuid4()}"},
        )
        assert created.status_code == 201
        knowledge_base_id = created.json()["id"]

        source = (
            "Acme SSO troubleshooting. When users cannot sign in through SAML, "
            "check whether the signing certificate has expired. Replace the expired "
            "certificate in the identity provider and application configuration, "
            "then retest login."
        )
        uploaded = await client.post(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            files={"file": ("acme-sso.md", source, "text/markdown")},
        )
        assert uploaded.status_code == 201
        uploaded_body = uploaded.json()
        assert uploaded_body["status"] == "indexed"
        assert uploaded_body["chunk_count"] >= 1

        search = await client.post(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/search",
            headers=headers,
            json={"query": "What should we check when SAML login fails?"},
        )
        assert search.status_code == 200
        citations = search.json()["citations"]
        assert citations
        assert citations[0]["filename"] == "acme-sso.md"

        answer = await client.post(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/answer",
            headers=headers,
            json={"question": "What should we check when Acme SSO login fails?"},
        )
        assert answer.status_code == 200
        assert answer.json()["citations"]
        assert answer.json()["model"]["model"] == "helix-mock-v1"

        # A valid identity cannot escape its tenant by guessing a knowledge-base ID.
        cross_tenant = await client.get(
            f"/api/v1/knowledge-bases/{private_kb_id}/documents",
            headers=headers,
        )
        assert cross_tenant.status_code == 404

    async with factory() as session:
        await session.execute(delete(DocumentChunk).where(DocumentChunk.tenant_id == tenant_id))
        await session.execute(delete(Document).where(Document.tenant_id == tenant_id))
        await session.execute(delete(KnowledgeBase).where(KnowledgeBase.tenant_id == tenant_id))
        await session.execute(
            delete(KnowledgeBase).where(KnowledgeBase.tenant_id == other_tenant_id)
        )
        await session.execute(delete(Membership).where(Membership.user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(Tenant).where(Tenant.id.in_([tenant_id, other_tenant_id])))
        await session.commit()
