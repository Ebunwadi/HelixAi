from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from helix_api.db.base import Base


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subscription_plan: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            name="customer_status",
        ),
        default=CustomerStatus.ACTIVE,
        nullable=False,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
