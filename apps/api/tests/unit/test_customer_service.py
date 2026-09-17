from uuid import UUID, uuid4

import pytest

from helix_api.core.errors import NotFoundError
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.customers.models import Customer
from helix_api.modules.customers.service import CustomerService
from helix_api.modules.tenants.models import MembershipRole


class FakeCustomerRepository:
    def __init__(self, customers: list[Customer]) -> None:
        self.customers = customers

    async def list_for_tenant(self, tenant_id: UUID) -> list[Customer]:
        return [item for item in self.customers if item.tenant_id == tenant_id]

    async def get_for_tenant(self, *, tenant_id: UUID, customer_id: UUID) -> Customer | None:
        return next(
            (
                item
                for item in self.customers
                if item.id == customer_id and item.tenant_id == tenant_id
            ),
            None,
        )


def context_for(tenant_id: UUID) -> CurrentContext:
    return CurrentContext(
        user_id=uuid4(),
        tenant_id=tenant_id,
        role=MembershipRole.OPERATOR,
        external_identity_id="operator",
        tenant_name="Tenant",
        tenant_slug="tenant",
    )


@pytest.mark.asyncio
async def test_customer_service_does_not_return_cross_tenant_customer() -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    customer_b = Customer(id=uuid4(), tenant_id=tenant_b, name="Other Tenant Customer")
    service = CustomerService(FakeCustomerRepository([customer_b]))  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        await service.get_customer(context=context_for(tenant_a), customer_id=customer_b.id)
