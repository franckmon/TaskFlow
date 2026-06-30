from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.exceptions import InvalidCredentialsError, UnauthorizedError
from app.domain.auth import AuthResult
from app.domain.user import UserEntity
from app.persistence.mappers import user_model_to_entity


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> AuthResult:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect username or password")

        user_entity = user_model_to_entity(user)
        access_token = create_access_token(
            data={"sub": user_entity.username, "role": user_entity.role.value}
        )
        return AuthResult(access_token=access_token, role=user_entity.role)

    def get_user_by_username(self, username: str) -> UserEntity:
        user = self.user_repo.get_by_username(username)
        if user is None:
            raise UnauthorizedError("User not found")
        return user_model_to_entity(user)
