from fastapi import APIRouter

from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard_data


router = APIRouter(
    prefix="/api",
    tags=["Dashboard"],
)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def dashboard() -> DashboardResponse:
    return get_dashboard_data()