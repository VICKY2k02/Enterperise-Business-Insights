
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Customer, Order
from app.schemas.order import OrderListItem, PaginatedOrders


router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=PaginatedOrders)
def get_orders(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, min_length=1, max_length=20),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PaginatedOrders:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    try:
        filters = []

        if status:
            filters.append(Order.status == status.lower())

        if start_date:
            filters.append(
                Order.order_date >= datetime.combine(start_date, time.min)
            )

        if end_date:
            # Exclusive upper bound includes the entire end date.
            filters.append(
                Order.order_date
                < datetime.combine(end_date + timedelta(days=1), time.min)
            )

        total = db.scalar(
            select(func.count(Order.id)).where(*filters)
        ) or 0

        statement = (
            select(Order, Customer)
            .join(Customer, Customer.id == Order.customer_id)
            .where(*filters)
            .order_by(Order.order_date.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )

        rows = db.execute(statement).all()

        items = [
            OrderListItem(
                id=order.id,
                order_date=order.order_date,
                customer_id=order.customer_id,
                customer_name=customer.name,
                customer_email=customer.email,
                total_amount=float(order.total_amount or Decimal("0")),
                status=order.status,
            )
            for order, customer in rows
        ]

        return PaginatedOrders(
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Orders are temporarily unavailable. Please try again.",
        ) from None
