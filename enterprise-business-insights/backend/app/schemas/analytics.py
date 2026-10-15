from pydantic import BaseModel


class RevenueTrendItem(BaseModel):
    month: str
    revenue: float


class RevenueTrendResponse(BaseModel):
    start_date: str
    end_date: str
    items: list[RevenueTrendItem]
