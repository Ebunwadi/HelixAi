from fastapi import APIRouter

from helix_api.modules.auth.dependencies import CurrentContextDependency, SessionDependency
from helix_api.modules.tenants.repository import TenantRepository
from helix_api.modules.tenants.schemas import TenantRead
from helix_api.modules.tenants.service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/current", response_model=TenantRead)
async def get_current_tenant(
    context: CurrentContextDependency,
    session: SessionDependency,
) -> TenantRead:
    tenant = await TenantService(TenantRepository(session)).get_current(context)
    return TenantRead.model_validate(tenant)
