from datetime import date

from pydantic import BaseModel, ConfigDict


class AnalyticsTotals(BaseModel):
    revenue: float
    orders: int
    profit: float
    customers: int


class AnalyticsChange(BaseModel):
    revenue_percentage: float | None
    orders_percentage: float | None
    profit_percentage: float | None


class ComparisonPeriod(BaseModel):
    start_date: date
    end_date: date
    totals: AnalyticsTotals
    changes: AnalyticsChange


class RevenueTrendPoint(BaseModel):
    period: str
    revenue: float


class OrderStatusCount(BaseModel):
    status: str
    count: int


class TopCategoryAnalytics(BaseModel):
    name: str
    sales: float
    items_sold: int
    contribution_percentage: float


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    totals: AnalyticsTotals
    revenue_trend_interval: str
    revenue_trend: list[RevenueTrendPoint]
    order_status_breakdown: list[OrderStatusCount]
    top_category: TopCategoryAnalytics | None
    previous_period: ComparisonPeriod | None

class RevenueTrendItem(BaseModel):
    month: str
    revenue: float


class RevenueTrendResponse(BaseModel):
    start_date: str
    end_date: str
    items: list[RevenueTrendItem]