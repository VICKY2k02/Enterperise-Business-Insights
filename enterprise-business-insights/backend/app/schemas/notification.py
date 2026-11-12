
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


NotificationType = Literal[
    "Revenue",
    "Sales",
    "Order",
    "Customer",
    "System",
]

NotificationPriority = Literal[
    "Low",
    "Medium",
    "High",
    "Critical",
]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    notification_type: NotificationType = Field(
        validation_alias="notification_type"
    )
    priority: NotificationPriority
    related_entity_id: int | None
    related_entity_type: str | None
    recipient_user_id: int
    is_read: bool
    created_at: datetime
    read_at: datetime | None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMessage(BaseModel):
    message: str
