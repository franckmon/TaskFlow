from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole


def ensure_default_admin(db: Session) -> bool:
    """Idempotent: create bootstrap admin from settings when missing."""
    if settings.is_production:
        return False
    with db.no_autoflush:
        existing = db.query(User).filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME).first()
    if existing is not None:
        return False

    db.add(
        User(
            username=settings.BOOTSTRAP_ADMIN_USERNAME,
            hashed_password=get_password_hash(settings.BOOTSTRAP_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
    )
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    return True
