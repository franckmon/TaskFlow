from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListQuery
from app.schemas.common import MessageResponse
from app.services.task_service import TaskService
from app.domain.user import UserEntity
from app.api.mappers import task_to_response
from app.api.openapi_responses import (
    RESPONSES_FORBIDDEN,
    RESPONSES_INVALID_STATUS,
    RESPONSES_NOT_FOUND,
    RESPONSES_TASK_COMPLETED,
    RESPONSES_UNAUTHORIZED,
    RESPONSES_VALIDATION,
    merge_responses,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_TASK_LIST_RESPONSES = merge_responses(RESPONSES_UNAUTHORIZED, RESPONSES_VALIDATION)
_TASK_READ_RESPONSES = merge_responses(RESPONSES_UNAUTHORIZED, RESPONSES_NOT_FOUND)
_TASK_MUTATION_RESPONSES = merge_responses(
    RESPONSES_UNAUTHORIZED,
    RESPONSES_NOT_FOUND,
    RESPONSES_VALIDATION,
    RESPONSES_TASK_COMPLETED,
    RESPONSES_INVALID_STATUS,
)
_TASK_CREATE_RESPONSES = merge_responses(
    RESPONSES_UNAUTHORIZED,
    RESPONSES_VALIDATION,
    RESPONSES_INVALID_STATUS,
)
_TASK_DELETE_RESPONSES = merge_responses(
    RESPONSES_UNAUTHORIZED,
    RESPONSES_FORBIDDEN,
    RESPONSES_NOT_FOUND,
    RESPONSES_TASK_COMPLETED,
)


@router.post(
    "/",
    response_model=TaskResponse,
    summary="Create a task",
    description=(
        "Create a new task for the authenticated user. The initial `status` must be `new`."
    ),
    response_description="Created task",
    responses=_TASK_CREATE_RESPONSES,
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
):
    service = TaskService(db)
    result = service.create_task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
    )
    return task_to_response(result)


@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List tasks",
    description=(
        "Return tasks matching optional filters, search text, sort order, and pagination. "
        "Results are ordered by `sort_by` and `sort_order` (default: `created_at` desc)."
    ),
    response_description="List of matching tasks (may be empty)",
    responses=_TASK_LIST_RESPONSES,
)
def get_tasks(
    query: Annotated[TaskListQuery, Depends()],
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
):
    service = TaskService(db)
    tasks = service.get_tasks(
        skip=query.skip,
        limit=query.limit,
        status=query.status,
        priority=query.priority,
        search=query.search,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    return [task_to_response(task) for task in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
    description="Return a single task by primary key.",
    response_description="Requested task",
    responses=_TASK_READ_RESPONSES,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
):
    service = TaskService(db)
    task = service.get_task(task_id)
    return task_to_response(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description=(
        "Apply a partial update. Omitted fields are unchanged. "
        "Tasks with status `done` cannot be edited. "
        "Status changes must follow `new` → `in_progress` → `done`."
    ),
    response_description="Updated task",
    responses=_TASK_MUTATION_RESPONSES,
)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    _: UserEntity = Depends(get_current_user),
):
    service = TaskService(db)
    result = service.update_task(
        task_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
    )
    return task_to_response(result)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    summary="Delete a task",
    description="Delete a task. Requires the `admin` role.",
    response_description="Deletion confirmation",
    responses=_TASK_DELETE_RESPONSES,
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    service = TaskService(db)
    service.delete_task(task_id, current_user)
    return MessageResponse(message="Task deleted successfully")
