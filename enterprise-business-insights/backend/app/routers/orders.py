import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models import Customer, Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    OrderListItem,
    OrderStatusUpdate,
    PaginatedOrders,
)
from app.services.notification_service import create_notification_and_send


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("",response_model=OrderCreateResponse,status_code=201,)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.ANALYST)
    ),
) -> OrderCreateResponse:

    # Prevent duplicate product entries in the same request.
    product_ids = [item.product_id for item in order_data.items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=422,
            detail="Each product can only appear once in an order.",
        )

    try:
        # Check whether the customer exists.
        customer = db.get(Customer, order_data.customer_id)

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found.",
            )

        # Retrieve products and their actual prices from the database.
        products = (
            db.query(Product)
            .filter(Product.id.in_(product_ids))
            .all()
        )

        products_by_id = {
            product.id: product for product in products
        }

        if len(products_by_id) != len(product_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more products were not found.",
            )

        total_amount = Decimal("0.00")
        order_items = []

        for requested_item in order_data.items:
            product = products_by_id[requested_item.product_id]

            if product.status.lower() != "active":
                raise HTTPException(
                    status_code=400,
                    detail=f"Product '{product.name}' is not active.",
                )

            unit_price = Decimal(str(product.unit_price))
            unit_cost = Decimal(str(product.unit_cost))

            total_amount += unit_price * requested_item.quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=requested_item.quantity,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                )
            )

        # Create the order.
        new_order = Order(
            customer_id=customer.id,
            order_date=datetime.now(),
            total_amount=total_amount,
            status="pending",
        )

        db.add(new_order)
        db.flush()

        # Attach all order items to the newly created order.
        for item in order_items:
            item.order_id = new_order.id
            db.add(item)

        # Save the order and all its items together.
        db.commit()
        db.refresh(new_order)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating an order.")
        raise HTTPException(
            status_code=503,
            detail="Unable to create the order. Please try again.",
        ) from None

    # Generate notifications after the order has been committed.
    # A notification failure must not undo a successfully saved order.
    recipients = (
        db.query(User)
        .filter(
            User.role.in_([UserRole.ADMIN, UserRole.ANALYST]),
            User.is_enabled.is_(True),
        )
        .all()
    )

    for recipient in recipients:
        try:
            await create_notification_and_send(
                db,
                recipient_user_id=recipient.id,
                title="New Order Created",
                message=(
                    f"Order #{new_order.id} has been created "
                    f"for customer {customer.name}. "
                    f"Total amount: {total_amount:.2f}."
                ),
                notification_type="Order",
                priority="Medium",
                event_key=f"order_created:{new_order.id}",
                related_entity_id=new_order.id,
                related_entity_type="order",
            )
        except Exception:
            logger.exception(
                "Failed to generate order notification for user %s.",
                recipient.id,
            )

    return OrderCreateResponse(
        id=new_order.id,
        customer_id=new_order.customer_id,
        order_date=new_order.order_date,
        total_amount=Decimal(str(new_order.total_amount)),
        status=new_order.status,
    )


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



@router.patch(
    "/{order_id}/status",
    response_model=OrderCreateResponse,
)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.ANALYST)
    ),
) -> OrderCreateResponse:

    try:
        order = db.get(Order, order_id)

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found.",
            )

        current_status = order.status.lower()
        requested_status = status_data.status

        if current_status not in {"pending", "completed", "cancelled"}:
            raise HTTPException(
                status_code=409,
                detail=f"Unsupported current order status: {current_status}.",
            )

        # Do not allow a cancelled order to be reopened.
        if current_status == "cancelled" and requested_status == "completed":
            raise HTTPException(
                status_code=409,
                detail="A cancelled order cannot be completed.",
            )

        # Repeating the same status does not generate another notification.
        if current_status == requested_status:
            return OrderCreateResponse(
                id=order.id,
                customer_id=order.customer_id,
                order_date=order.order_date,
                total_amount=Decimal(str(order.total_amount)),
                status=order.status,
            )

        # Update and save the order first.
        order.status = requested_status

        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating order status.")
        raise HTTPException(
            status_code=503,
            detail="Unable to update order status. Please try again.",
        ) from None

    # Notify enabled Admin and Analyst users after the order is committed.
    recipients = (
        db.query(User)
        .filter(
            User.role.in_([UserRole.ADMIN, UserRole.ANALYST]),
            User.is_enabled.is_(True),
        )
        .all()
    )

    notification_title = (
        "Order Completed"
        if requested_status == "completed"
        else "Order Cancelled"
    )

    notification_priority = (
        "Medium"
        if requested_status == "completed"
        else "High"
    )

    for recipient in recipients:
        try:
            await create_notification_and_send(
                db,
                recipient_user_id=recipient.id,
                title=notification_title,
                message=(
                    f"Order #{order.id} status changed "
                    f"from {current_status} to {requested_status}."
                ),
                notification_type="Order",
                priority=notification_priority,
                event_key=f"order_status:{order.id}:{requested_status}",
                related_entity_id=order.id,
                related_entity_type="order",
            )
        except Exception:
            logger.exception(
                "Failed to generate status notification for user %s.",
                recipient.id,
            )

    return OrderCreateResponse(
        id=order.id,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=Decimal(str(order.total_amount)),
        status=order.status,
    )
