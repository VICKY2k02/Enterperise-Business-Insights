from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.dashboard import router as dashboard_router
from app.routers.orders import router as orders_router
from app.routers.customers import router as customers_router
from app.routers.analytics import router as analytics_router
from app.routers.activities import router as activities_router
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.notifications import router as notifications_router
from app.routers.notification_ws import router as notification_ws_router
from app.routers.business_alerts import router as business_alerts_router


app = FastAPI(
    title="Enterprise Business Insights API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(orders_router)
app.include_router(customers_router)
app.include_router(analytics_router)
app.include_router(activities_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(notifications_router)
app.include_router(notification_ws_router)
app.include_router(business_alerts_router)


@app.get("/")
def root():
    return {
        "message": "Enterprise Business Insights API is running"
    }