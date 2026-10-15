
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import BusinessActivity
from app.schemas.activity import ActivityListItem, PaginatedActivities


router = APIRouter(prefix="/api/activities", tags=["Activities"])


@router.get("", response_model=PaginatedActivities)
def get_activities(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    activity_type: str | None = Query(default=None, min_length=1, max_length=50),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PaginatedActivities:

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    try:
        filters = []

        if activity_type:
            filters.append(
                BusinessActivity.activity_type == activity_type.strip().lower()
            )

        if search:
            filters.append(
                BusinessActivity.description.ilike(f"%{search.strip()}%")
            )

        if start_date:
            filters.append(
                BusinessActivity.timestamp
                >= datetime.combine(start_date, time.min)
            )

        if end_date:
            filters.append(
                BusinessActivity.timestamp
                < datetime.combine(end_date + timedelta(days=1), time.min)
            )

        total = db.scalar(
            select(func.count(BusinessActivity.id)).where(*filters)
        ) or 0

        statement = (
            select(BusinessActivity)
            .where(*filters)
            .order_by(
                BusinessActivity.timestamp.desc(),
                BusinessActivity.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        activities = db.scalars(statement).all()

        return PaginatedActivities(
            total=total,
            limit=limit,
            offset=offset,
            items=[
                ActivityListItem.model_validate(activity)
                for activity in activities
            ],
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Activity data is temporarily unavailable. Please try again.",
        ) from None
