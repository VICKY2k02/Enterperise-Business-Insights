
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityListItem(BaseModel):
    id: int
    activity_type: str
    description: str
    related_entity: str | None
    related_entity_id: int | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedActivities(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ActivityListItem]
