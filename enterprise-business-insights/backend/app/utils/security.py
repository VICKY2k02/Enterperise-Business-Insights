
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Convert a plain-text password into a secure password hash."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against its stored hash."""
    return password_hasher.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    """Create a signed JWT with an expiration time."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
