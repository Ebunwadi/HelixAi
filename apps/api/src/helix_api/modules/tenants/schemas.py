from uuid import UUID

from pydantic import BaseModel, ConfigDict

from helix_api.modules.tenants.models import TenantStatus


class TenantRead(BaseModel):
    id: UUID
    name: str
    slug: str
    status: TenantStatus

    model_config = ConfigDict(from_attributes=True)
