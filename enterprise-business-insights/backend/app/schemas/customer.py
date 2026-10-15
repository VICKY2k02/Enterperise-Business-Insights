from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    status: str = "active"

class CustomerListItem(BaseModel):
    id: int
    name: str
    email: str
    registration_date: datetime
    status: str
    order_count: int
    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomers(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CustomerListItem]
