import pytest
from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository


@pytest.fixture
def task_repository(db_session: Session) -> TaskRepository:
    return TaskRepository(db_session)
