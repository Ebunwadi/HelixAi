from uuid import UUID

from pydantic import BaseModel, ConfigDict

from helix_api.modules.tenants.models import MembershipRole


class AuthenticatedIdentity(BaseModel):
    subject: str
    email: str | None = None
    display_name: str | None = None


class CurrentContext(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: MembershipRole
    external_identity_id: str
    email: str | None = None
    display_name: str | None = None
    tenant_name: str
    tenant_slug: str

    model_config = ConfigDict(use_enum_values=False)


class CurrentContextResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: MembershipRole
    email: str | None = None
    display_name: str | None = None
    tenant_name: str
    tenant_slug: str
