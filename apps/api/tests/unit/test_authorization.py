from uuid import uuid4

import pytest

from helix_api.core.authorization import require_role
from helix_api.core.errors import AuthorizationError
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.tenants.models import MembershipRole


def make_context(role: MembershipRole) -> CurrentContext:
    return CurrentContext(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role=role,
        external_identity_id="subject",
        email="user@example.com",
        display_name="User",
        tenant_name="Tenant",
        tenant_slug="tenant",
    )


def test_require_role_accepts_allowed_role() -> None:
    require_role(make_context(MembershipRole.ADMIN), [MembershipRole.ADMIN])


def test_require_role_rejects_disallowed_role() -> None:
    with pytest.raises(AuthorizationError):
        require_role(make_context(MembershipRole.OPERATOR), [MembershipRole.ADMIN])
