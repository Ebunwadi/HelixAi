import asyncio
from uuid import UUID

from sqlalchemy import select

from helix_api.core.config import get_settings
from helix_api.db.session import get_session_factory
from helix_api.modules.customers.models import Customer, CustomerStatus
from helix_api.modules.tenants.models import (
    Membership,
    MembershipRole,
    MembershipStatus,
    Tenant,
    TenantStatus,
)
from helix_api.modules.users.models import User

DEV_TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
DEV_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
DEV_SUBJECT = "dev-user"


async def bootstrap() -> None:
    settings = get_settings()
    if settings.helix_env != "local":
        raise RuntimeError("Dev bootstrap is only allowed when HELIX_ENV=local")

    factory = get_session_factory()
    async with factory() as session:
        tenant = await session.get(Tenant, DEV_TENANT_ID)
        if tenant is None:
            tenant = Tenant(
                id=DEV_TENANT_ID,
                name="HelixAI Demo Workspace",
                slug="helix-demo",
                status=TenantStatus.ACTIVE,
            )
            session.add(tenant)

        result = await session.execute(select(User).where(User.external_identity_id == DEV_SUBJECT))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=DEV_USER_ID,
                external_identity_id=DEV_SUBJECT,
                email="dev@helix.local",
                display_name="Helix Developer",
            )
            session.add(user)

        membership_result = await session.execute(
            select(Membership).where(
                Membership.tenant_id == DEV_TENANT_ID,
                Membership.user_id == DEV_USER_ID,
            )
        )
        if membership_result.scalar_one_or_none() is None:
            session.add(
                Membership(
                    tenant_id=DEV_TENANT_ID,
                    user_id=user.id,
                    role=MembershipRole.ADMIN,
                    status=MembershipStatus.ACTIVE,
                )
            )

        customer_result = await session.execute(
            select(Customer).where(Customer.tenant_id == DEV_TENANT_ID)
        )
        if not customer_result.scalars().first():
            session.add_all(
                [
                    Customer(
                        tenant_id=DEV_TENANT_ID,
                        external_ref="CRM-ACME",
                        name="Acme Corporation",
                        subscription_plan="Enterprise",
                        region="UK",
                        status=CustomerStatus.ACTIVE,
                        metadata_json={"sso_provider": "Entra ID"},
                    ),
                    Customer(
                        tenant_id=DEV_TENANT_ID,
                        external_ref="CRM-GLOBEX",
                        name="Globex Ltd",
                        subscription_plan="Growth",
                        region="EU",
                        status=CustomerStatus.ACTIVE,
                        metadata_json={},
                    ),
                ]
            )

        await session.commit()

    print("Development data is ready.")
    print(f"X-Helix-Subject: {DEV_SUBJECT}")
    print(f"X-Helix-Tenant-Id: {DEV_TENANT_ID}")


def main() -> None:
    asyncio.run(bootstrap())
