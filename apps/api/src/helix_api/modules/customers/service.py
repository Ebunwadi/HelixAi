from uuid import UUID

from helix_api.core.errors import NotFoundError
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.customers.models import Customer
from helix_api.modules.customers.repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository

    async def list_customers(self, context: CurrentContext) -> list[Customer]:
        return await self.repository.list_for_tenant(context.tenant_id)

    async def get_customer(self, *, context: CurrentContext, customer_id: UUID) -> Customer:
        customer = await self.repository.get_for_tenant(
            tenant_id=context.tenant_id,
            customer_id=customer_id,
        )
        if customer is None:
            # 404 deliberately avoids confirming that another tenant owns this ID.
            raise NotFoundError("Customer not found")
        return customer
