from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.business_alert_service import evaluate_business_alerts


router = APIRouter(
    prefix="/api/business-alerts",
    tags=["Business Alerts"],
)


@router.post("/evaluate")
async def evaluate_alerts(
    evaluation_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    """
    Evaluate monthly revenue and previous-day low-sales alerts.

    Admin access only.
    """

    return await evaluate_business_alerts(
        db=db,
        evaluation_date=evaluation_date,
    )