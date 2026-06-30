from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc, asc
from app.domain.task_types import TaskPriority, TaskSortField, SortOrder, TaskStatus
from app.models.task import Task
from app.repositories.base import BaseRepository

SORT_COLUMNS = {
    TaskSortField.CREATED_AT: Task.created_at,
    TaskSortField.PRIORITY: Task.priority,
}


class TaskRepository(BaseRepository[Task]):
    """Data access for the shared workspace task list."""

    def __init__(self, db: Session):
        super().__init__(Task, db)

    def get_by_title(self, title: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.title == title).first()

    def filter(
        self,
        *,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
        sort_by: TaskSortField = TaskSortField.CREATED_AT,
        sort_order: SortOrder = SortOrder.DESC,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        # Ownership: global shared workspace — all tasks, no user_id filter.
        stmt = select(Task)

        if status is not None:
            stmt = stmt.filter(Task.status == status)

        if priority is not None:
            stmt = stmt.filter(Task.priority == priority)

        if search is not None:
            stmt = stmt.filter(
                or_(Task.title.ilike(f"%{search}%"), Task.description.ilike(f"%{search}%"))
            )

        order_col = SORT_COLUMNS[sort_by]
        ordering = asc(order_col) if sort_order == SortOrder.ASC else desc(order_col)
        stmt = stmt.order_by(ordering)

        stmt = stmt.offset(skip).limit(limit)

        return list(self.db.execute(stmt).scalars().all())
