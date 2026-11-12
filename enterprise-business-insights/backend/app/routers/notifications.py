
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
    NotificationMessage,
)
from app.services.notification_service import get_unread_count


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    notification_type: Literal[
        "Revenue", "Sales", "Order", "Customer", "System"
    ] | None = Query(default=None, alias="type"),
    priority: Literal[
        "Low", "Medium", "High", "Critical"
    ] | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    sort_order: Literal["newest", "oldest"] = Query(default="newest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(
        Notification.recipient_user_id == current_user.id
    )

    if notification_type:
        query = query.filter(
            Notification.notification_type == notification_type
        )

    if priority:
        query = query.filter(Notification.priority == priority)

    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()

    if sort_order == "newest":
        query = query.order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
    else:
        query = query.order_by(
            Notification.created_at.asc(),
            Notification.id.asc(),
        )

    notifications = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NotificationListResponse(
        items=notifications,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
def read_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UnreadCountResponse(
        unread_count=get_unread_count(db, current_user.id)
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notification)

    return notification


@router.patch(
    "/read-all",
    response_model=NotificationMessage,
)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.recipient_user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update(
        {
            Notification.is_read: True,
            Notification.read_at: datetime.now(timezone.utc),
        },
        synchronize_session=False,
    )

    db.commit()

    return NotificationMessage(
        message="All notifications marked as read"
    )


@router.delete(
    "/{notification_id}",
    response_model=NotificationMessage,
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()

    return NotificationMessage(
        message="Notification deleted successfully"
    )
