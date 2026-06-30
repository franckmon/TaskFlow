from app.core.bootstrap import ensure_default_admin
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole

E2E_REGULAR_USERNAME = "regular"
E2E_REGULAR_PASSWORD = "userpassword"


def ensure_e2e_regular_user(db) -> bool:
    existing = db.query(User).filter(User.username == E2E_REGULAR_USERNAME).first()
    if existing is not None:
        return False

    db.add(
        User(
            username=E2E_REGULAR_USERNAME,
            hashed_password=get_password_hash(E2E_REGULAR_PASSWORD),
            role=UserRole.USER,
        )
    )
    db.flush()
    return True


def main() -> None:
    db = SessionLocal()
    try:
        db.query(User).delete(synchronize_session=False)
        db.commit()

        ensure_default_admin(db)
        ensure_e2e_regular_user(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
