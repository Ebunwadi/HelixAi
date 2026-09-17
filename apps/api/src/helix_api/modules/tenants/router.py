from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.db.session import get_session
from helix_api.modules.auth.dependencies import get_current_context
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.tenants.repository import TenantRepository
from helix_api.modules.tenants.schemas import TenantRead
from helix_api.modules.tenants.service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/current", response_model=TenantRead)
async def get_current_tenant(
    context: CurrentContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> TenantRead:
    tenant = await TenantService(TenantRepository(session)).get_current(context)
    return TenantRead.model_validate(tenant)
