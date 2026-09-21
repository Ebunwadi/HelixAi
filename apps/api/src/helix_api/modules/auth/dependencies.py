from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.db.session import get_session
from helix_api.modules.auth.schemas import AuthenticatedIdentity, CurrentContext
from helix_api.modules.auth.security import authenticate_request
from helix_api.modules.auth.service import AuthContextService
from helix_api.modules.tenants.repository import MembershipRepository, TenantRepository
from helix_api.modules.users.repository import UserRepository

TenantHeader = Annotated[UUID, Header(alias="X-Helix-Tenant-Id")]
IdentityDependency = Annotated[AuthenticatedIdentity, Depends(authenticate_request)]
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_current_context(
    tenant_id: TenantHeader,
    identity: IdentityDependency,
    session: SessionDependency,
) -> CurrentContext:
    service = AuthContextService(
        users=UserRepository(session),
        tenants=TenantRepository(session),
        memberships=MembershipRepository(session),
    )
    return await service.resolve(identity=identity, tenant_id=tenant_id)


CurrentContextDependency = Annotated[CurrentContext, Depends(get_current_context)]
