import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.bootstrap import ensure_default_admin
from app.core.config import settings
from app.core.database import Base
from app.core.exceptions import AppError, InvalidStatusTransitionError
from app.domain.task_types import TaskPriority, TaskStatus
from app.models.task import Task
from app.models.user import User
from app.services.task_service import TaskService
import app.models.task  # noqa: F401
import app.models.user  # noqa: F401

WORKER_COUNT = 6


@pytest.fixture
def concurrency_engine(tmp_path):
    """File-backed SQLite with NullPool: one connection per thread, shared database."""
    db_file = tmp_path / "concurrency.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session_factory(concurrency_engine) -> sessionmaker[Session]:
    factory = sessionmaker(bind=concurrency_engine, autocommit=False, autoflush=False)
    with factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
    return factory


def _count_bootstrap_admins(session: Session) -> int:
    return session.query(User).filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME).count()


def _run_bootstrap(factory: sessionmaker[Session]) -> bool:
    session = factory()
    try:
        created = ensure_default_admin(session)
        if created:
            session.commit()
        else:
            session.rollback()
        return created
    except IntegrityError:
        session.rollback()
        return False
    finally:
        session.close()


def _load_task(factory: sessionmaker[Session], task_id: int) -> Task:
    session = factory()
    try:
        task = session.get(Task, task_id)
        assert task is not None
        return task
    finally:
        session.close()


def _run_workers(worker, count: int = WORKER_COUNT) -> None:
    barrier = threading.Barrier(count)

    def wrapped() -> None:
        worker(barrier)

    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(wrapped) for _ in range(count)]
        for future in as_completed(futures):
            future.result()


class TestConcurrentBootstrap:
    def test_ensure_default_admin_is_safe_under_threaded_race(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        results: list[bool] = []

        def worker(barrier: threading.Barrier) -> None:
            barrier.wait()
            results.append(_run_bootstrap(session_factory))

        _run_workers(worker)

        verify = session_factory()
        try:
            assert _count_bootstrap_admins(verify) == 1
            assert any(results)
        finally:
            verify.close()

    def test_ensure_default_admin_is_safe_under_asyncio_gather(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        async def run_all() -> list[bool]:
            return list(
                await asyncio.gather(
                    *[
                        asyncio.to_thread(_run_bootstrap, session_factory)
                        for _ in range(WORKER_COUNT)
                    ]
                )
            )

        results = asyncio.run(run_all())

        verify = session_factory()
        try:
            assert _count_bootstrap_admins(verify) == 1
            assert any(results)
        finally:
            verify.close()


class TestConcurrentTaskUpdates:
    @pytest.fixture
    def task_id(self, session_factory: sessionmaker[Session]) -> int:
        session = session_factory()
        try:
            service = TaskService(session)
            task = service.create_task(
                title="Concurrent task",
                description="Race condition check",
                status=TaskStatus.NEW,
                priority=TaskPriority.NORMAL,
            )
            return task.id
        finally:
            session.close()

    def test_concurrent_status_transition_to_in_progress_is_consistent(
        self,
        session_factory: sessionmaker[Session],
        task_id: int,
    ) -> None:
        errors: list[AppError] = []

        def worker(barrier: threading.Barrier) -> None:
            barrier.wait()
            session = session_factory()
            try:
                TaskService(session).update_task(
                    task_id,
                    status=TaskStatus.IN_PROGRESS,
                )
            except AppError as exc:
                errors.append(exc)
            finally:
                session.close()

        _run_workers(worker)

        task = _load_task(session_factory, task_id)
        assert task.status == TaskStatus.IN_PROGRESS
        assert not errors

    def test_concurrent_invalid_status_transitions_do_not_corrupt_state(
        self,
        session_factory: sessionmaker[Session],
        task_id: int,
    ) -> None:
        invalid_errors: list[InvalidStatusTransitionError] = []

        def worker(barrier: threading.Barrier) -> None:
            barrier.wait()
            session = session_factory()
            try:
                TaskService(session).update_task(task_id, status=TaskStatus.DONE)
            except InvalidStatusTransitionError as exc:
                invalid_errors.append(exc)
            finally:
                session.close()

        _run_workers(worker)

        task = _load_task(session_factory, task_id)
        assert task.status == TaskStatus.NEW
        assert len(invalid_errors) == WORKER_COUNT

    def test_concurrent_field_updates_keep_single_consistent_row(
        self,
        session_factory: sessionmaker[Session],
        task_id: int,
    ) -> None:
        expected_titles = {f"Concurrent title {index}" for index in range(WORKER_COUNT)}
        priorities = [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH]

        def worker(barrier: threading.Barrier, index: int) -> None:
            barrier.wait()
            session = session_factory()
            title = f"Concurrent title {index}"
            try:
                TaskService(session).update_task(
                    task_id,
                    title=title,
                    priority=priorities[index % 3],
                    description=f"Description for {title}",
                )
            finally:
                session.close()

        barrier = threading.Barrier(WORKER_COUNT)
        with ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
            futures = [executor.submit(worker, barrier, index) for index in range(WORKER_COUNT)]
            for future in as_completed(futures):
                future.result()

        task = _load_task(session_factory, task_id)
        assert task.title in expected_titles
        assert task.priority in priorities
        assert task.description is not None
        assert task.description.startswith("Description for ")
        assert task.status == TaskStatus.NEW

        verify = session_factory()
        try:
            rows = verify.execute(select(Task).where(Task.id == task_id)).scalars().all()
            assert len(rows) == 1
            assert verify.execute(select(func.count()).select_from(Task)).scalar_one() == 1
        finally:
            verify.close()

    def test_concurrent_forward_status_chain_ends_in_done(
        self,
        session_factory: sessionmaker[Session],
        task_id: int,
    ) -> None:
        async def run_phase(status: TaskStatus) -> None:
            await asyncio.gather(
                *[
                    asyncio.to_thread(_update_task_status, session_factory, task_id, status)
                    for _ in range(WORKER_COUNT)
                ]
            )

        asyncio.run(run_phase(TaskStatus.IN_PROGRESS))
        assert _load_task(session_factory, task_id).status == TaskStatus.IN_PROGRESS

        asyncio.run(run_phase(TaskStatus.DONE))
        assert _load_task(session_factory, task_id).status == TaskStatus.DONE


def _update_task_status(
    factory: sessionmaker[Session],
    task_id: int,
    status: TaskStatus,
) -> None:
    session = factory()
    try:
        TaskService(session).update_task(task_id, status=status)
    except AppError:
        pass
    finally:
        session.close()
