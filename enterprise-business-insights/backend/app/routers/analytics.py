from datetime import date, datetime, time, timedelta
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Category, Customer, Order, OrderItem, Product
from app.schemas.analytics import (
    AnalyticsChange,
    AnalyticsOverviewResponse,
    AnalyticsTotals,
    ComparisonPeriod,
    OrderStatusCount,
    RevenueTrendItem,
    RevenueTrendResponse,
    RevenueTrendPoint,
    TopCategoryAnalytics,
)


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

QUALIFYING_STATUS = "completed"
KNOWN_STATUSES = ("pending", "processing", "completed", "cancelled")


def get_period_bounds(
    start_date: date,
    end_date: date,
) -> tuple[datetime, datetime]:
    """Convert inclusive dates to a half-open datetime interval."""
    return (
        datetime.combine(start_date, time.min),
        datetime.combine(end_date + timedelta(days=1), time.min),
    )


def get_totals(
    db: Session,
    start: datetime,
    end: datetime,
) -> AnalyticsTotals:
    """Aggregate financial totals and completed orders in PostgreSQL."""
    revenue_expression = (
        OrderItem.quantity * OrderItem.unit_price
    )
    profit_expression = (
        OrderItem.quantity
        * (OrderItem.unit_price - OrderItem.unit_cost)
    )

    statement = (
        select(
            func.coalesce(
                func.sum(revenue_expression), 0
            ).label("revenue"),
            func.coalesce(
                func.sum(profit_expression), 0
            ).label("profit"),
            func.count(distinct(Order.id)).label("orders"),
        )
        .select_from(Order)
        .outerjoin(OrderItem, OrderItem.order_id == Order.id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= start,
            Order.order_date < end,
        )
    )

    row = db.execute(statement).one()

    # Count customers registered during this exact reporting period.
    customer_count = db.scalar(
        select(func.count(Customer.id)).where(
            Customer.registration_date >= start,
            Customer.registration_date < end,
        )
    )

    return AnalyticsTotals(
        revenue=round(float(row.revenue or 0), 2),
        orders=int(row.orders or 0),
        profit=round(float(row.profit or 0), 2),
        customers=int(customer_count or 0),
    )


def calculate_percentage_change(
    current: float,
    previous: float,
) -> float | None:
    """Return None when a positive current value has no baseline."""
    if previous == 0:
        if current == 0:
            return 0.0
        return None

    return round(((current - previous) / abs(previous)) * 100, 2)


def get_revenue_trend(
    db: Session,
    start_date: date,
    end_date: date,
) -> tuple[str, list[RevenueTrendPoint]]:
    """Aggregate revenue by day or month and fill missing buckets with zero."""
    days = (end_date - start_date).days + 1
    interval = "day" if days <= 31 else "month"

    bucket_expression = func.date_trunc(
        interval, Order.order_date
    )

    statement = (
        select(
            bucket_expression.label("bucket"),
            func.coalesce(
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                ),
                0,
            ).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= datetime.combine(
                start_date, time.min
            ),
            Order.order_date < datetime.combine(
                end_date + timedelta(days=1), time.min
            ),
        )
        .group_by(bucket_expression)
        .order_by(bucket_expression)
    )

    rows = db.execute(statement).all()

    revenue_by_bucket = {
        (
            row.bucket.strftime("%Y-%m-%d")
            if interval == "day"
            else row.bucket.strftime("%Y-%m")
        ): float(row.revenue or 0)
        for row in rows
    }

    points: list[RevenueTrendPoint] = []

    if interval == "day":
        current_date = start_date

        while current_date <= end_date:
            key = current_date.strftime("%Y-%m-%d")
            points.append(
                RevenueTrendPoint(
                    period=key,
                    revenue=round(revenue_by_bucket.get(key, 0), 2),
                )
            )
            current_date += timedelta(days=1)

    else:
        current_month = start_date.replace(day=1)
        last_month = end_date.replace(day=1)

        while current_month <= last_month:
            key = current_month.strftime("%Y-%m")
            points.append(
                RevenueTrendPoint(
                    period=key,
                    revenue=round(revenue_by_bucket.get(key, 0), 2),
                )
            )

            if current_month.month == 12:
                current_month = current_month.replace(
                    year=current_month.year + 1,
                    month=1,
                )
            else:
                current_month = current_month.replace(
                    month=current_month.month + 1,
                )

    return interval, points


def get_order_status_breakdown(
    db: Session,
    start: datetime,
    end: datetime,
) -> list[OrderStatusCount]:
    """Count all order statuses, including statuses with zero orders."""
    statement = (
        select(
            func.lower(Order.status).label("status"),
            func.count(Order.id).label("count"),
        )
        .where(
            Order.order_date >= start,
            Order.order_date < end,
        )
        .group_by(func.lower(Order.status))
    )

    counts = {
        str(row.status): int(row.count)
        for row in db.execute(statement).all()
    }

    # Preserve known statuses in a predictable order.
    result = [
        OrderStatusCount(
            status=status,
            count=counts.pop(status, 0),
        )
        for status in KNOWN_STATUSES
    ]

    # Preserve any additional statuses present in the database.
    result.extend(
        OrderStatusCount(status=status, count=count)
        for status, count in sorted(counts.items())
    )

    return result


def get_top_category(
    db: Session,
    start: datetime,
    end: datetime,
    total_revenue: float,
) -> TopCategoryAnalytics | None:
    """Rank categories by completed-order sales, highest first."""
    sales_expression = (
        OrderItem.quantity * OrderItem.unit_price
    )

    statement = (
        select(
            Category.name.label("name"),
            func.sum(sales_expression).label("sales"),
            func.coalesce(
                func.sum(OrderItem.quantity), 0
            ).label("items_sold"),
        )
        .join(Product, Product.category_id == Category.id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status == QUALIFYING_STATUS,
            Order.order_date >= start,
            Order.order_date < end,
        )
        .group_by(Category.id, Category.name)
        .order_by(
            func.sum(sales_expression).desc(),
            Category.name.asc(),
        )
        .limit(1)
    )

    row = db.execute(statement).first()

    if row is None:
        return None

    sales = float(row.sales or 0)
    contribution = (
        (sales / total_revenue) * 100
        if total_revenue > 0
        else 0.0
    )

    return TopCategoryAnalytics(
        name=row.name,
        sales=round(sales, 2),
        items_sold=int(row.items_sold or 0),
        contribution_percentage=round(contribution, 2),
    )


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
)
def get_analytics_overview(
    start_date: date = Query(
        ...,
        description="Inclusive reporting start date (YYYY-MM-DD)",
    ),
    end_date: date = Query(
        ...,
        description="Inclusive reporting end date (YYYY-MM-DD)",
    ),
    comparison_period: bool = Query(
        True,
        description="Include comparison with the immediately preceding equal-length period",
    ),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:

    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    try:
        start, end = get_period_bounds(start_date, end_date)

        totals = get_totals(db, start, end)

        trend_interval, trend = get_revenue_trend(
            db, start_date, end_date
        )

        statuses = get_order_status_breakdown(
            db, start, end
        )

        top_category = get_top_category(
            db, start, end, totals.revenue
        )

        previous_period = None

        if comparison_period:
            period_days = (end_date - start_date).days + 1
            previous_end_date = start_date - timedelta(days=1)
            previous_start_date = (
                previous_end_date - timedelta(days=period_days - 1)
            )

            previous_start, previous_end = get_period_bounds(
                previous_start_date,
                previous_end_date,
            )

            previous_totals = get_totals(
                db, previous_start, previous_end
            )

            previous_period = ComparisonPeriod(
                start_date=previous_start_date,
                end_date=previous_end_date,
                totals=previous_totals,
                changes=AnalyticsChange(
                    revenue_percentage=calculate_percentage_change(
                        totals.revenue,
                        previous_totals.revenue,
                    ),
                    orders_percentage=calculate_percentage_change(
                        totals.orders,
                        previous_totals.orders,
                    ),
                    profit_percentage=calculate_percentage_change(
                        totals.profit,
                        previous_totals.profit,
                    ),
                ),
            )

        return AnalyticsOverviewResponse(
            start_date=start_date,
            end_date=end_date,
            totals=totals,
            revenue_trend_interval=trend_interval,
            revenue_trend=trend,
            order_status_breakdown=statuses,
            top_category=top_category,
            previous_period=previous_period,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Analytics data is temporarily unavailable. Please try again.",
        ) from None


# Keep the existing endpoint available for Task 3 compatibility.
@router.get(
    "/revenue-trend",
    response_model=RevenueTrendResponse,
)
def get_revenue_trend_endpoint(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
) -> RevenueTrendResponse:

    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    try:
        start, end = get_period_bounds(start_date, end_date)
        month_column = func.date_trunc("month", Order.order_date)

        statement = (
            select(
                month_column.label("month"),
                func.coalesce(
                    func.sum(
                        OrderItem.quantity * OrderItem.unit_price
                    ),
                    0,
                ).label("revenue"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(
                Order.status == QUALIFYING_STATUS,
                Order.order_date >= start,
                Order.order_date < end,
            )
            .group_by(month_column)
            .order_by(month_column)
        )

        rows = db.execute(statement).all()

        revenue_by_month = {
            row.month.strftime("%Y-%m"): float(row.revenue or 0)
            for row in rows
        }

        items: list[RevenueTrendItem] = []
        current_month = start_date.replace(day=1)
        last_month = end_date.replace(day=1)

        while current_month <= last_month:
            key = current_month.strftime("%Y-%m")
            items.append(
                RevenueTrendItem(
                    month=key,
                    revenue=round(revenue_by_month.get(key, 0), 2),
                )
            )

            if current_month.month == 12:
                current_month = current_month.replace(
                    year=current_month.year + 1,
                    month=1,
                )
            else:
                current_month = current_month.replace(
                    month=current_month.month + 1,
                )

        return RevenueTrendResponse(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            items=items,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Revenue data is temporarily unavailable. Please try again.",
        ) from None