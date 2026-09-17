from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.modules.customers.models import Customer


class CustomerRepository:
    """All customer reads require the tenant scope as part of the query."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_tenant(self, tenant_id: UUID) -> list[Customer]:
        result = await self.session.execute(
            select(Customer).where(Customer.tenant_id == tenant_id).order_by(Customer.name.asc())
        )
        return list(result.scalars().all())

    async def get_for_tenant(self, *, tenant_id: UUID, customer_id: UUID) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()
