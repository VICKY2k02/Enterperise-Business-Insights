
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        CheckConstraint(
            "type IN ('Revenue', 'Sales', 'Order', 'Customer', 'System')",
            name="ck_notifications_type",
        ),
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High', 'Critical')",
            name="ck_notifications_priority",
        ),
        UniqueConstraint(
            "recipient_user_id",
            "event_key",
            name="uq_notifications_recipient_event",
        ),
        Index(
            "ix_notifications_recipient_created",
            "recipient_user_id",
            "created_at",
        ),
        Index(
            "ix_notifications_recipient_read",
            "recipient_user_id",
            "is_read",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    notification_type: Mapped[str] = mapped_column(
        "type",
        String(20),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    related_entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    related_entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    recipient_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Used to prevent the same event creating duplicate notifications.
    event_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recipient = relationship("User")
