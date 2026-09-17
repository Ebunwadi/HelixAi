from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.db.session import get_session
from helix_api.modules.auth.schemas import AuthenticatedIdentity, CurrentContext
from helix_api.modules.auth.security import authenticate_request
from helix_api.modules.auth.service import AuthContextService
from helix_api.modules.tenants.repository import MembershipRepository, TenantRepository
from helix_api.modules.users.repository import UserRepository


async def get_current_context(
    tenant_id: UUID = Header(alias="X-Helix-Tenant-Id"),
    identity: AuthenticatedIdentity = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> CurrentContext:
    service = AuthContextService(
        users=UserRepository(session),
        tenants=TenantRepository(session),
        memberships=MembershipRepository(session),
    )
    return await service.resolve(identity=identity, tenant_id=tenant_id)
