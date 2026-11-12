from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User, UserRole
from app.services.notification_service import create_notification_and_send


def get_completed_sales(
    db: Session,
    start_date: date,
    end_date: date,
) -> Decimal:
    """
    Calculate revenue from completed orders within a date range.

    Revenue = sum(quantity * unit_price)
    The end date is exclusive.
    """

    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.min)

    total = (
        db.query(
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.unit_price),
                0,
            )
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.status == "completed",
            Order.order_date >= start_datetime,
            Order.order_date < end_datetime,
        )
        .scalar()
    )

    return Decimal(str(total or 0))


def get_alert_recipients(db: Session) -> list[User]:
    """Return enabled Admin and Analyst users."""

    return (
        db.query(User)
        .filter(
            User.role.in_([
                UserRole.ADMIN,
                UserRole.ANALYST,
            ]),
            User.is_enabled.is_(True),
        )
        .all()
    )


async def evaluate_business_alerts(
    db: Session,
    evaluation_date: date | None = None,
) -> dict:
    """
    Evaluate monthly revenue and previous-day sales alerts.

    Monthly revenue:
        Generate an alert when completed revenue reaches
        or exceeds the configured monthly target.

    Low daily sales:
        Generate an alert when the previous completed day's
        revenue is below the configured daily threshold.
    """

    if evaluation_date is None:
        evaluation_date = datetime.now().date()

    recipients = get_alert_recipients(db)

    notifications = []

    # --------------------------------------------------
    # 1. Monthly Revenue Target Alert
    # --------------------------------------------------

    monthly_target = settings.MONTHLY_REVENUE_TARGET

    if monthly_target is not None:
        month_start = evaluation_date.replace(day=1)

        if month_start.month == 12:
            next_month_start = date(
                month_start.year + 1,
                1,
                1,
            )
        else:
            next_month_start = date(
                month_start.year,
                month_start.month + 1,
                1,
            )

        monthly_revenue = get_completed_sales(
            db,
            month_start,
            next_month_start,
        )

        if monthly_revenue >= monthly_target:
            event_key = (
                f"monthly_revenue_target:{month_start:%Y-%m}"
            )

            for recipient in recipients:
                notification = await create_notification_and_send(
                    db,
                    recipient_user_id=recipient.id,
                    title="Monthly Revenue Target Achieved",
                    message=(
                        f"Monthly completed revenue has reached "
                        f"{monthly_revenue:,.2f}, meeting or exceeding "
                        f"the target of {monthly_target:,.2f}."
                    ),
                    notification_type="Revenue",
                    priority="High",
                    event_key=event_key,
                )

                if notification is not None:
                    notifications.append(notification)

    # --------------------------------------------------
    # 2. Previous-Day Low Sales Alert
    # --------------------------------------------------

    low_sales_threshold = settings.LOW_DAILY_SALES_THRESHOLD

    previous_day = evaluation_date - timedelta(days=1)

    if low_sales_threshold is not None:
        previous_day_revenue = get_completed_sales(
            db,
            previous_day,
            evaluation_date,
        )

        if previous_day_revenue < low_sales_threshold:
            event_key = (
                f"low_daily_sales:{previous_day:%Y-%m-%d}"
            )

            for recipient in recipients:
                notification = await create_notification_and_send(
                    db,
                    recipient_user_id=recipient.id,
                    title="Low Daily Sales Alert",
                    message=(
                        f"Completed sales on {previous_day:%d-%m-%Y} "
                        f"were {previous_day_revenue:,.2f}, "
                        f"below the configured threshold of "
                        f"{low_sales_threshold:,.2f}."
                    ),
                    notification_type="Sales",
                    priority="High",
                    event_key=event_key,
                )

                if notification is not None:
                    notifications.append(notification)

    return {
        "evaluation_date": evaluation_date.isoformat(),
        "recipients_checked": len(recipients),
        "notifications_processed": len(notifications),
        "monthly_revenue_target_enabled": monthly_target is not None,
        "low_daily_sales_threshold_enabled": (
            low_sales_threshold is not None
        ),
    } 