import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from helix_api.db.session import get_session_factory
from helix_api.main import app
from helix_api.modules.customers.models import Customer
from helix_api.modules.tenants.models import Membership, MembershipRole, MembershipStatus, Tenant
from helix_api.modules.users.models import User

pytestmark = pytest.mark.skipif(
    os.getenv("HELIX_RUN_DB_TESTS") != "1",
    reason="Database integration tests require HELIX_RUN_DB_TESTS=1",
)


@pytest.mark.asyncio
async def test_cross_tenant_customer_access_returns_404() -> None:
    factory = get_session_factory()
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    user_id = uuid4()
    customer_b_id = uuid4()
    subject = f"integration-{uuid4()}"

    async with factory() as session:
        session.add_all(
            [
                Tenant(id=tenant_a_id, name="Tenant A", slug=f"tenant-a-{uuid4()}"),
                Tenant(id=tenant_b_id, name="Tenant B", slug=f"tenant-b-{uuid4()}"),
                User(id=user_id, external_identity_id=subject, email="test@example.com"),
            ]
        )
        await session.flush()
        session.add(
            Membership(
                tenant_id=tenant_a_id,
                user_id=user_id,
                role=MembershipRole.OPERATOR,
                status=MembershipStatus.ACTIVE,
            )
        )
        session.add(Customer(id=customer_b_id, tenant_id=tenant_b_id, name="Private B Customer"))
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/customers/{customer_b_id}",
            headers={
                "X-Helix-Subject": subject,
                "X-Helix-Tenant-Id": str(tenant_a_id),
            },
        )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"

    async with factory() as session:
        await session.execute(delete(Customer).where(Customer.id == customer_b_id))
        await session.execute(delete(Membership).where(Membership.user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(Tenant).where(Tenant.id.in_([tenant_a_id, tenant_b_id])))
        await session.commit()
