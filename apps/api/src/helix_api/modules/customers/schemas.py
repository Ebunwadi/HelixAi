from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from helix_api.modules.customers.models import CustomerStatus


class CustomerRead(BaseModel):
    id: UUID
    external_ref: str | None
    name: str
    subscription_plan: str | None
    region: str | None
    status: CustomerStatus
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")

    model_config = ConfigDict(from_attributes=True)
