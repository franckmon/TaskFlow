from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError
from app.services.auth_service import AuthService
from app.domain.user import UserEntity

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> UserEntity:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedError("Invalid authentication credentials")

    username: str = payload.get("sub")
    if username is None:
        raise UnauthorizedError("Invalid authentication credentials")

    auth_service = AuthService(db)
    return auth_service.get_user_by_username(username)
