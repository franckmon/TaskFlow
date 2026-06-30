import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole


def seed_admin(username: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists, skipping.")
            return

        db.add(
            User(
                username=username,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN,
            )
        )
        db.commit()
        print(f"Created admin user '{username}'.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm admin user creation (required)",
    )
    args = parser.parse_args()

    if not args.confirm:
        print("Refusing to seed without --confirm flag.", file=sys.stderr)
        sys.exit(1)

    seed_admin(args.username, args.password)


if __name__ == "__main__":
    main()
