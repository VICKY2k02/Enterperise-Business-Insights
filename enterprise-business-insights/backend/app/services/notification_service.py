from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User, UserRole
from app.utils.websocket_manager import notification_manager


VALID_TYPES = {
    "Revenue",
    "Sales",
    "Order",
    "Customer",
    "System",
}

VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


def notification_to_dict(notification: Notification) -> dict:
    """Convert a saved notification into a WebSocket-safe dictionary."""

    return {
        "event": "new_notification",
        "notification": {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "priority": notification.priority,
            "related_entity_id": notification.related_entity_id,
            "related_entity_type": notification.related_entity_type,
            "recipient_user_id": notification.recipient_user_id,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            ),
            "read_at": (
                notification.read_at.isoformat()
                if notification.read_at
                else None
            ),
        },
    }


async def send_notification_to_user(notification: Notification) -> None:
    """Send a notification to its recipient through WebSocket."""

    await notification_manager.send_to_user(
        notification.recipient_user_id,
        notification_to_dict(notification),
    )


def _create_notification_with_status(
    db: Session,
    *,
    recipient_user_id: int,
    title: str,
    message: str,
    notification_type: str,
    priority: str,
    event_key: str | None = None,
    related_entity_id: int | None = None,
    related_entity_type: str | None = None,
) -> tuple[Notification | None, bool]:
    """
    Create a notification and report whether a new record was inserted.

    Returns:
        (notification, True): A new notification was created.
        (existing_notification, False): A duplicate already existed.
        (None, False): No notification was created or found.
    """

    if notification_type not in VALID_TYPES:
        raise ValueError("Invalid notification type")

    if priority not in VALID_PRIORITIES:
        raise ValueError("Invalid notification priority")

    # Check for an existing event before inserting.
    if event_key is not None:
        existing = (
            db.query(Notification)
            .filter(
                Notification.recipient_user_id == recipient_user_id,
                Notification.event_key == event_key,
            )
            .first()
        )

        if existing is not None:
            return existing, False

    notification = Notification(
        recipient_user_id=recipient_user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        event_key=event_key,
        related_entity_id=related_entity_id,
        related_entity_type=related_entity_type,
    )

    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification, True

    except IntegrityError:
        db.rollback()

        # Another request may have inserted the same event
        # between our initial check and database commit.
        if event_key is not None:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.recipient_user_id == recipient_user_id,
                    Notification.event_key == event_key,
                )
                .first()
            )

            if existing is not None:
                return existing, False

        raise


def create_notification(
    db: Session,
    *,
    recipient_user_id: int,
    title: str,
    message: str,
    notification_type: str,
    priority: str,
    event_key: str | None = None,
    related_entity_id: int | None = None,
    related_entity_type: str | None = None,
) -> Notification | None:
    """Create a notification without sending a WebSocket message."""

    notification, _created = _create_notification_with_status(
        db,
        recipient_user_id=recipient_user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        event_key=event_key,
        related_entity_id=related_entity_id,
        related_entity_type=related_entity_type,
    )

    return notification


async def create_notification_and_send(
    db: Session,
    *,
    recipient_user_id: int,
    title: str,
    message: str,
    notification_type: str,
    priority: str,
    event_key: str | None = None,
    related_entity_id: int | None = None,
    related_entity_type: str | None = None,
) -> Notification | None:
    """
    Create a notification and send it only when a new record is inserted.

    Duplicate events are returned but never sent again.
    """

    notification, created = _create_notification_with_status(
        db,
        recipient_user_id=recipient_user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        event_key=event_key,
        related_entity_id=related_entity_id,
        related_entity_type=related_entity_type,
    )

    if notification is not None and created:
        await send_notification_to_user(notification)

    return notification


def create_system_notifications(
    db: Session,
    *,
    title: str,
    message: str,
    priority: str = "Medium",
    event_key: str | None = None,
) -> list[Notification]:

    admins = (
        db.query(User)
        .filter(
            User.role == UserRole.ADMIN,
            User.is_enabled.is_(True),
        )
        .all()
    )

    notifications = []

    for admin in admins:
        notification = create_notification(
            db,
            recipient_user_id=admin.id,
            title=title,
            message=message,
            notification_type="System",
            priority=priority,
            event_key=event_key,
        )

        if notification is not None:
            notifications.append(notification)

    return notifications


async def create_system_notifications_and_send(
    db: Session,
    *,
    title: str,
    message: str,
    priority: str = "Medium",
    event_key: str | None = None,
) -> list[Notification]:

    admins = (
        db.query(User)
        .filter(
            User.role == UserRole.ADMIN,
            User.is_enabled.is_(True),
        )
        .all()
    )

    notifications = []

    for admin in admins:
        notification = await create_notification_and_send(
            db,
            recipient_user_id=admin.id,
            title=title,
            message=message,
            notification_type="System",
            priority=priority,
            event_key=event_key,
        )

        if notification is not None:
            notifications.append(notification)

    return notifications


def get_unread_count(
    db: Session,
    recipient_user_id: int,
) -> int:

    count = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_read.is_(False),
        )
        .scalar()
    )

    return count or 0


def mark_notification_as_read(
    db: Session,
    notification: Notification,
) -> Notification:

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notification)

    return notification