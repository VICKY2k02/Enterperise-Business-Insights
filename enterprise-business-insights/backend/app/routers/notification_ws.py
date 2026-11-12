
import jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.websocket_manager import notification_manager


router = APIRouter()


@router.websocket("/ws/notifications")
async def notification_websocket(websocket: WebSocket):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    db: Session = SessionLocal()

    user_id = None

    try:
        # Validate the JWT using the existing application settings.
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdigit():
            await websocket.close(
                code=1008,
                reason="Invalid authentication token",
            )
            return

        user_id = int(subject)

        # Confirm that the user exists and is enabled.
        user = db.query(User).filter(User.id == user_id).first()

        if user is None or not user.is_enabled:
            await websocket.close(
                code=1008,
                reason="User not authorized",
            )
            return

        # Register this connection for the authenticated user.
        await notification_manager.connect(user_id, websocket)

        # Keep the connection alive until the client disconnects.
        while True:
            await websocket.receive_text()

    except InvalidTokenError:
        await websocket.close(
            code=1008,
            reason="Invalid or expired authentication token",
        )

    except WebSocketDisconnect:
        pass

    finally:
        if user_id is not None:
            notification_manager.disconnect(user_id, websocket)

        db.close()
