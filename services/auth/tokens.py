import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api_gateway.database import get_db
from services.cases.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30
bearer_scheme = HTTPBearer(auto_error=False)


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a secret of at least 32 characters"
        )
    return secret


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "customer_id": user.customer_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or missing access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            _secret(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, RuntimeError):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_analyst(user: User = Depends(get_current_user)) -> User:
    if user.role != "analyst":
        raise HTTPException(
            status_code=403,
            detail="Analyst access required",
        )
    return user


def require_customer_ownership(customer_id: str, user: User) -> None:
    if user.role != "customer" or not user.customer_id:
        raise HTTPException(status_code=403, detail="Customer access required")
    if user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access to this customer is forbidden")
