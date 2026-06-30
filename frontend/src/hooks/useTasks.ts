import { useCallback, useEffect, useRef, useState } from 'react';
import { createTask, deleteTask, getTasks, updateTask } from '../api/tasks';
import { getErrorMessage, isAbortError } from '../api/client';
import { useDebouncedValue } from './useDebouncedValue';
import {
  Task,
  TaskCreate,
  TaskFilters,
  TaskPagination,
  TaskPriority,
  TaskQueryParams,
  TaskSorting,
  TaskSortField,
  SortOrder,
  TaskStatus,
} from '../types';

const DEFAULT_FILTERS: TaskFilters = {
  status: '',
  priority: '',
  search: '',
};

const DEFAULT_PAGINATION: TaskPagination = {
  skip: 0,
  limit: 10,
};

const DEFAULT_SORTING: TaskSorting = {
  sort_by: 'created_at',
  sort_order: 'desc',
};

const buildQueryParams = (
  filters: TaskFilters,
  pagination: TaskPagination,
  sorting: TaskSorting,
): TaskQueryParams => {
  const params: TaskQueryParams = {
    skip: pagination.skip,
    limit: pagination.limit,
    sort_by: sorting.sort_by,
    sort_order: sorting.sort_order,
  };

  if (filters.status) {
    params.status = filters.status;
  }
  if (filters.priority) {
    params.priority = filters.priority;
  }
  if (filters.search) {
    params.search = filters.search;
  }

  return params;
};

export const useTasks = (enabled: boolean) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFilters>(DEFAULT_FILTERS);
  const [pagination, setPagination] = useState<TaskPagination>(DEFAULT_PAGINATION);
  const [sorting, setSorting] = useState<TaskSorting>(DEFAULT_SORTING);
  const [isCreating, setIsCreating] = useState(false);
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<number | null>(null);
  const debouncedSearch = useDebouncedValue(filters.search);
  const fetchAbortControllerRef = useRef<AbortController | null>(null);
  const hasLoadedOnceRef = useRef(false);

  const isActiveFetch = (controller: AbortController) =>
    fetchAbortControllerRef.current === controller && !controller.signal.aborted;

  useEffect(() => {
    setPagination((current) => {
      if (current.skip === 0) {
        return current;
      }

      return { ...current, skip: 0 };
    });
  }, [debouncedSearch]);

  const fetchTasks = useCallback(async () => {
    if (!enabled) {
      return;
    }

    fetchAbortControllerRef.current?.abort();
    const controller = new AbortController();
    fetchAbortControllerRef.current = controller;

    if (hasLoadedOnceRef.current) {
      setIsRefreshing(true);
    } else {
      setIsInitialLoading(true);
    }
    setError(null);

    try {
      const data = await getTasks(
        buildQueryParams(
          { ...filters, search: debouncedSearch },
          pagination,
          sorting,
        ),
        { signal: controller.signal },
      );

      if (!isActiveFetch(controller)) {
        return;
      }

      setTasks(data);
      hasLoadedOnceRef.current = true;
    } catch (err) {
      if (isAbortError(err) || !isActiveFetch(controller)) {
        return;
      }

      setError(getErrorMessage(err));
    } finally {
      if (isActiveFetch(controller)) {
        setIsInitialLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [enabled, filters.status, filters.priority, debouncedSearch, pagination, sorting]);

  useEffect(() => {
    fetchTasks();

    return () => {
      fetchAbortControllerRef.current?.abort();
      fetchAbortControllerRef.current = null;
    };
  }, [fetchTasks]);

  const setStatusFilter = (status: TaskStatus | '') => {
    setPagination((current) => ({ ...current, skip: 0 }));
    setFilters((current) => ({ ...current, status }));
  };

  const setPriorityFilter = (priority: TaskPriority | '') => {
    setPagination((current) => ({ ...current, skip: 0 }));
    setFilters((current) => ({ ...current, priority }));
  };

  const setSearchFilter = (search: string) => {
    setFilters((current) => ({ ...current, search }));
  };

  const setSortBy = (sort_by: TaskSortField) => {
    setPagination((current) => ({ ...current, skip: 0 }));
    setSorting((current) => ({ ...current, sort_by }));
  };

  const setSortOrder = (sort_order: SortOrder) => {
    setPagination((current) => ({ ...current, skip: 0 }));
    setSorting((current) => ({ ...current, sort_order }));
  };

  const nextPage = () => {
    setPagination((current) => ({
      ...current,
      skip: current.skip + current.limit,
    }));
  };

  const prevPage = () => {
    setPagination((current) => ({
      ...current,
      skip: Math.max(0, current.skip - current.limit),
    }));
  };

  const updateTaskStatus = async (id: number, status: TaskStatus): Promise<string | null> => {
    setError(null);
    setUpdatingTaskId(id);
    try {
      await updateTask(id, { status });
      await fetchTasks();
      return null;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      return message;
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const removeTask = async (id: number): Promise<string | null> => {
    setError(null);
    setDeletingTaskId(id);
    try {
      await deleteTask(id);
      await fetchTasks();
      return null;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      return message;
    } finally {
      setDeletingTaskId(null);
    }
  };

  const addTask = async (data: TaskCreate): Promise<string | null> => {
    setError(null);
    setIsCreating(true);
    try {
      await createTask(data);
      await fetchTasks();
      return null;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      return message;
    } finally {
      setIsCreating(false);
    }
  };

  const currentPage = Math.floor(pagination.skip / pagination.limit) + 1;
  // API returns no total count; treat a full page as evidence of a possible next page.
  const hasNextPage = tasks.length === pagination.limit;

  return {
    tasks,
    isInitialLoading,
    isRefreshing,
    isCreating,
    deletingTaskId,
    updatingTaskId,
    error,
    filters,
    pagination,
    sorting,
    currentPage,
    hasNextPage,
    setStatusFilter,
    setPriorityFilter,
    setSearchFilter,
    setSortBy,
    setSortOrder,
    nextPage,
    prevPage,
    refetch: fetchTasks,
    updateTaskStatus,
    removeTask,
    createTask: addTask,
  };
};
