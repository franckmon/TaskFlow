from dataclasses import dataclass

from app.domain.user_types import UserRole


@dataclass
class UserEntity:
    username: str
    role: UserRole
