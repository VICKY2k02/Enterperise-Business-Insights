from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Order, OrderItem
from app.schemas.analytics import (
    RevenueTrendItem,
    RevenueTrendResponse,
)


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/revenue-trend", response_model=RevenueTrendResponse)
def get_revenue_trend(
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
        month_column = func.date_trunc("month", Order.order_date)

        statement = (
            select(
                month_column.label("month"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)
                .label("revenue"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(
                Order.status == "completed",
                Order.order_date >= datetime.combine(start_date, time.min),
                Order.order_date
                < datetime.combine(end_date + timedelta(days=1), time.min),
            )
            .group_by(month_column)
            .order_by(month_column)
        )

        rows = db.execute(statement).all()

        # Include months with zero revenue.
        revenue_by_month = {
            row.month.strftime("%Y-%m"): float(row.revenue or 0)
            for row in rows
        }

        items = []
        current_month = start_date.replace(day=1)
        last_month = end_date.replace(day=1)

        while current_month <= last_month:
            month_key = current_month.strftime("%Y-%m")
            items.append(
                RevenueTrendItem(
                    month=month_key,
                    revenue=round(revenue_by_month.get(month_key, 0), 2),
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