from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    BusinessActivity,
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
)
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardKPIs,
    DashboardAnalytics,
    KPIData,
    RevenueTrendItem,
    OrdersSummary,
    TopCategory as TopCategorySchema,
    RecentActivity as RecentActivitySchema,
)


QUALIFYING_STATUS = "completed"


def get_month_range(year: int, month: int):
    start = datetime(year, month, 1)

    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    return start, end


def get_previous_month(year: int, month: int):
    if month == 1:
        return year - 1, 12

    return year, month - 1


def get_period_totals(db: Session, start: datetime, end: datetime):
    revenue = db.scalar(
        select(
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.unit_price), 0
            )
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= start,
            Order.order_date < end,
        )
    )

    profit = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    OrderItem.quantity
                    * (OrderItem.unit_price - OrderItem.unit_cost)
                ),
                0,
            )
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= start,
            Order.order_date < end,
        )
    )

    orders = db.scalar(
        select(func.count(Order.id)).where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= start,
            Order.order_date < end,
        )
    )

    customers = db.scalar(
        select(func.count(Customer.id)).where(
            Customer.registration_date < end
        )
    )

    return {
        "revenue": float(revenue or 0),
        "profit": float(profit or 0),
        "orders": int(orders or 0),
        "customers": int(customers or 0),
    }


def calculate_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0

    return round(((current - previous) / previous) * 100, 2)


def get_dashboard_data(db: Session) -> DashboardResponse:
    now = datetime.now()

    current_start, current_end = get_month_range(now.year, now.month)

    previous_year, previous_month = get_previous_month(
        now.year, now.month
    )
    previous_start, previous_end = get_month_range(
        previous_year, previous_month
    )

    current = get_period_totals(db, current_start, current_end)
    previous = get_period_totals(db, previous_start, previous_end)

    # Revenue trend for the latest six calendar months.
    trend_start_year = now.year
    trend_start_month = now.month - 5

    while trend_start_month <= 0:
        trend_start_month += 12
        trend_start_year -= 1

    trend_start, _ = get_month_range(
        trend_start_year, trend_start_month
    )

    trend_rows = db.execute(
        select(
            func.date_trunc("month", Order.order_date).label("month"),
            func.sum(
                OrderItem.quantity * OrderItem.unit_price
            ).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= trend_start,
            Order.order_date < current_end,
        )
        .group_by(func.date_trunc("month", Order.order_date))
        .order_by(func.date_trunc("month", Order.order_date))
    ).all()

    revenue_by_month = {
        row.month.strftime("%Y-%m"): float(row.revenue or 0)
        for row in trend_rows
    }

    revenue_trend = []

    for offset in range(6):
        month_number = trend_start_month + offset
        year_number = trend_start_year

        while month_number > 12:
            month_number -= 12
            year_number += 1

        month_start, _ = get_month_range(year_number, month_number)
        month_key = month_start.strftime("%Y-%m")

        revenue_trend.append(
            RevenueTrendItem(
                month=month_start.strftime("%b"),
                revenue=revenue_by_month.get(month_key, 0.0),
            )
        )

    # Top-selling category for the current month.
    category_row = db.execute(
        select(
            Category.name,
            func.sum(
                OrderItem.quantity * OrderItem.unit_price
            ).label("sales"),
        )
        .join(Product, Product.category_id == Category.id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= current_start,
            Order.order_date < current_end,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(
            OrderItem.quantity * OrderItem.unit_price
        ).desc())
        .limit(1)
    ).first()

    if category_row and current["revenue"] > 0:
        top_category = TopCategorySchema(
            name=category_row.name,
            percentage=round(
                float(category_row.sales) / current["revenue"] * 100,
                2,
            ),
        )
    else:
        top_category = TopCategorySchema(
            name="No data",
            percentage=0.0,
        )

    print(
        "Dashboard database:",
        db.execute(select(func.current_database())).scalar(),
    )

    print(
        "Dashboard activity count:",
        db.scalar(select(func.count(BusinessActivity.id))),
    )

    latest_activities = db.scalars(
        select(BusinessActivity)
        .order_by(
            BusinessActivity.timestamp.desc(),
            BusinessActivity.id.desc(),
        )
        .limit(5)
    ).all()

    print(
        "Dashboard latest activities:",
        [
            {
                "id": activity.id,
                "type": activity.activity_type,
                "description": activity.description,
                "timestamp": str(activity.timestamp),
            }
            for activity in latest_activities
        ],
    )

    # Latest five activities.
    activity_rows = db.scalars(
        select(BusinessActivity)
        .order_by(
            BusinessActivity.timestamp.desc(),
            BusinessActivity.id.desc(),
        )
        .limit(5)
    ).all()

    recent_activities = [
        RecentActivitySchema(
            id=activity.id,
            title=activity.activity_type.replace("_", " ").title(),
            description=activity.description,
            value=activity.timestamp.strftime("%d %b %Y, %I:%M %p"),
        )
        for activity in activity_rows
    ]

    return DashboardResponse(
        kpis=DashboardKPIs(
            revenue=KPIData(
                value=current["revenue"],
                change=calculate_change(
                    current["revenue"], previous["revenue"]
                ),
            ),
            orders=KPIData(
                value=current["orders"],
                change=calculate_change(
                    current["orders"], previous["orders"]
                ),
            ),
            customers=KPIData(
                value=current["customers"],
                change=calculate_change(
                    current["customers"], previous["customers"]
                ),
            ),
            profit=KPIData(
                value=current["profit"],
                change=calculate_change(
                    current["profit"], previous["profit"]
                ),
            ),
        ),
        analytics=DashboardAnalytics(
            revenueTrend=revenue_trend,
            ordersSummary=OrdersSummary(
                orders=current["orders"],
                sales=current["revenue"],
            ),
            topCategory=top_category,
        ),
        recentActivities=recent_activities,
    )
