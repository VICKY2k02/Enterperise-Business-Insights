
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderListItem(BaseModel):
    id: int
    order_date: datetime
    customer_id: int
    customer_name: str
    customer_email: str
    total_amount: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedOrders(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OrderListItem]
