from uuid import UUID

from helix_api.core.errors import AuthorizationError
from helix_api.modules.auth.schemas import AuthenticatedIdentity, CurrentContext
from helix_api.modules.tenants.models import TenantStatus
from helix_api.modules.tenants.repository import MembershipRepository, TenantRepository
from helix_api.modules.users.repository import UserRepository


class AuthContextService:
    def __init__(
        self,
        *,
        users: UserRepository,
        tenants: TenantRepository,
        memberships: MembershipRepository,
    ) -> None:
        self.users = users
        self.tenants = tenants
        self.memberships = memberships

    async def resolve(
        self,
        *,
        identity: AuthenticatedIdentity,
        tenant_id: UUID,
    ) -> CurrentContext:
        user = await self.users.get_by_external_identity(identity.subject)
        if user is None:
            raise AuthorizationError("Authenticated user is not provisioned in HelixAI")

        membership = await self.memberships.get_active(user_id=user.id, tenant_id=tenant_id)
        if membership is None:
            raise AuthorizationError("You do not have an active membership in this tenant")

        tenant = await self.tenants.get(tenant_id)
        if tenant is None or tenant.status != TenantStatus.ACTIVE:
            raise AuthorizationError("The selected tenant is not available")

        return CurrentContext(
            user_id=user.id,
            tenant_id=tenant.id,
            role=membership.role,
            external_identity_id=user.external_identity_id,
            email=user.email,
            display_name=user.display_name,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
        )
