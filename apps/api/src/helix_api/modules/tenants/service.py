from helix_api.core.errors import NotFoundError
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.tenants.models import Tenant
from helix_api.modules.tenants.repository import TenantRepository


class TenantService:
    def __init__(self, repository: TenantRepository) -> None:
        self.repository = repository

    async def get_current(self, context: CurrentContext) -> Tenant:
        tenant = await self.repository.get(context.tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found")
        return tenant
