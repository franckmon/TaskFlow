from dataclasses import dataclass

from app.domain.user_types import UserRole


@dataclass
class AuthResult:
    access_token: str
    role: UserRole
