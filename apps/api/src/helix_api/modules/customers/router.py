from uuid import UUID

from fastapi import APIRouter

from helix_api.modules.auth.dependencies import CurrentContextDependency, SessionDependency
from helix_api.modules.customers.repository import CustomerRepository
from helix_api.modules.customers.schemas import CustomerRead
from helix_api.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
async def list_customers(
    context: CurrentContextDependency,
    session: SessionDependency,
) -> list[CustomerRead]:
    customers = await CustomerService(CustomerRepository(session)).list_customers(context)
    return [CustomerRead.model_validate(customer) for customer in customers]


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: UUID,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> CustomerRead:
    customer = await CustomerService(CustomerRepository(session)).get_customer(
        context=context,
        customer_id=customer_id,
    )
    return CustomerRead.model_validate(customer)
