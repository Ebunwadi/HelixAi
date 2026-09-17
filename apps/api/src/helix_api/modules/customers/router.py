from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.db.session import get_session
from helix_api.modules.auth.dependencies import get_current_context
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.customers.repository import CustomerRepository
from helix_api.modules.customers.schemas import CustomerRead
from helix_api.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
async def list_customers(
    context: CurrentContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> list[CustomerRead]:
    customers = await CustomerService(CustomerRepository(session)).list_customers(context)
    return [CustomerRead.model_validate(customer) for customer in customers]


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: UUID,
    context: CurrentContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> CustomerRead:
    customer = await CustomerService(CustomerRepository(session)).get_customer(
        context=context,
        customer_id=customer_id,
    )
    return CustomerRead.model_validate(customer)
