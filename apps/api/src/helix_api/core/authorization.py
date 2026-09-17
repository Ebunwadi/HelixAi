from collections.abc import Iterable

from helix_api.core.errors import AuthorizationError
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.tenants.models import MembershipRole


def require_role(context: CurrentContext, allowed_roles: Iterable[MembershipRole]) -> None:
    allowed = set(allowed_roles)
    if context.role not in allowed:
        raise AuthorizationError()
