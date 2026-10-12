from pydantic import BaseModel
from typing import List


class KPIData(BaseModel):
    value: float
    change: float


class RevenueTrendItem(BaseModel):
    month: str
    revenue: float


class OrdersSummary(BaseModel):
    orders: int
    sales: float


class TopCategory(BaseModel):
    name: str
    percentage: float


class RecentActivity(BaseModel):
    id: int
    title: str
    description: str
    value: str


class DashboardKPIs(BaseModel):
    revenue: KPIData
    orders: KPIData
    customers: KPIData
    profit: KPIData


class DashboardAnalytics(BaseModel):
    revenueTrend: List[RevenueTrendItem]
    ordersSummary: OrdersSummary
    topCategory: TopCategory


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    analytics: DashboardAnalytics
    recentActivities: List[RecentActivity]