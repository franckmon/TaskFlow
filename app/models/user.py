from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy import Enum as SQLEnum
from app.domain.user_types import UserRole
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER)
