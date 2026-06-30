from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository
from app.domain.user_types import UserRole
from app.domain.task_types import TaskPriority, TaskSortField, SortOrder, TaskStatus
from app.core.exceptions import PermissionDeniedError, TaskNotFoundError
from app.domain.task import TaskEntity
from app.domain.user import UserEntity
from app.persistence.mappers import task_model_to_entity
from app.domain.task_status import (
    validate_initial_status,
    validate_status_transition,
    validate_task_deletable,
    validate_task_modifiable,
)


class TaskService:
    """Business logic for the shared workspace task list (all users, same tasks)."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TaskRepository(db)

    @staticmethod
    def _require_admin(user: UserEntity) -> None:
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admin users can delete tasks")

    @staticmethod
    def _to_entity(task) -> TaskEntity:
        return task_model_to_entity(task)

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _rollback(self) -> None:
        self.db.rollback()

    def get_task(self, task_id: int) -> TaskEntity:
        task = self.repository.get(task_id)
        if not task:
            raise TaskNotFoundError("Task not found")
        return self._to_entity(task)

    def get_tasks(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
        sort_by: TaskSortField = TaskSortField.CREATED_AT,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[TaskEntity]:
        # No per-user scoping: every authenticated caller sees the full workspace list.
        tasks = self.repository.filter(
            status=status,
            priority=priority,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
        )
        return [self._to_entity(task) for task in tasks]

    def create_task(
        self,
        *,
        title: str,
        description: Optional[str],
        status: TaskStatus,
        priority: TaskPriority,
    ) -> TaskEntity:
        try:
            validate_initial_status(status)
            task = self.repository.create(
                title=title,
                description=description,
                status=status,
                priority=priority,
            )
            self._commit()
            return self._to_entity(task)
        except Exception:
            self._rollback()
            raise

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> TaskEntity:
        try:
            task = self.repository.get(task_id)
            if not task:
                raise TaskNotFoundError("Task not found")

            update_data = {
                k: v
                for k, v in {
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                }.items()
                if v is not None
            }
            if not update_data:
                return self._to_entity(task)

            validate_task_modifiable(task.status)

            new_status = update_data.get("status")
            if new_status is not None:
                validate_status_transition(task.status, new_status)

            updated_task = self.repository.update(task_id, **update_data)
            if not updated_task:
                raise TaskNotFoundError("Task not found")

            self._commit()
            return self._to_entity(updated_task)
        except Exception:
            self._rollback()
            raise

    def delete_task(self, task_id: int, current_user: UserEntity) -> None:
        try:
            self._require_admin(current_user)

            task = self.repository.get(task_id)
            if not task:
                raise TaskNotFoundError("Task not found")

            validate_task_deletable(
                task.status,
                is_admin=current_user.role == UserRole.ADMIN,
            )

            if not self.repository.delete(task_id):
                raise TaskNotFoundError("Task not found")

            self._commit()
        except Exception:
            self._rollback()
            raise
