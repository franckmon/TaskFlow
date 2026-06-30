from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def check_database_health(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1")).scalar_one()
        return True
    except SQLAlchemyError:
        return False


def get_health_payload(db: Session) -> tuple[int, dict[str, str]]:
    if check_database_health(db):
        return status.HTTP_200_OK, {"status": "ok"}
    return status.HTTP_503_SERVICE_UNAVAILABLE, {"status": "degraded"}


def health_check_response(db: Session) -> dict[str, str] | JSONResponse:
    status_code, payload = get_health_payload(db)
    if status_code == status.HTTP_200_OK:
        return payload
    return JSONResponse(status_code=status_code, content=payload)
