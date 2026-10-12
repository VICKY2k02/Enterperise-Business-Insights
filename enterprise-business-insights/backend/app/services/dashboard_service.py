from app.schemas.dashboard import DashboardResponse


def get_dashboard_data() -> DashboardResponse:
    return DashboardResponse(
        kpis={
            "revenue": {
                "value": 2450000,
                "change": 12.5,
            },
            "orders": {
                "value": 1248,
                "change": 8.2,
            },
            "customers": {
                "value": 856,
                "change": 5.4,
            },
            "profit": {
                "value": 684000,
                "change": 10.8,
            },
        },
        analytics={
            "revenueTrend": [
                {
                    "month": "Jan",
                    "revenue": 180000,
                },
                {
                    "month": "Feb",
                    "revenue": 210000,
                },
                {
                    "month": "Mar",
                    "revenue": 195000,
                },
                {
                    "month": "Apr",
                    "revenue": 240000,
                },
                {
                    "month": "May",
                    "revenue": 225000,
                },
                {
                    "month": "Jun",
                    "revenue": 280000,
                },
            ],
            "ordersSummary": {
                "orders": 1248,
                "sales": 245000,
            },
            "topCategory": {
                "name": "Electronics",
                "percentage": 42,
            },
        },
        recentActivities=[
            {
                "id": 1,
                "title": "New order received",
                "description": "Order #ORD1024",
                "value": "₹24,500",
            },
            {
                "id": 2,
                "title": "Sales target updated",
                "description": "North Region",
                "value": "2 hours ago",
            },
        ],
    )