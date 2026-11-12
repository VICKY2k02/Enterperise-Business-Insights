
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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

# Request for one product in an order
class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=10000)


# Request for creating an order
class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    items: list[OrderItemCreate] = Field(min_length=1)


# Response after creating an order
class OrderCreateResponse(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    total_amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


# Request for changing order status
class OrderStatusUpdate(BaseModel):
    status: Literal["completed", "cancelled"]