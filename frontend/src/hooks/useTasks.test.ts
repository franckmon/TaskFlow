import { act, renderHook, waitFor } from '@testing-library/react';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createTask, deleteTask, getTasks, updateTask } from '../api/tasks';
import { ApiClientError } from '../api/client';
import { sampleTask } from '../test/fixtures';
import {
  advanceDebounce,
  enableFakeTimers,
  restoreRealTimers,
  runPendingTimers,
} from '../test/utils/async';
import { SEARCH_DEBOUNCE_MS } from './useDebouncedValue';
import { useTasks } from './useTasks';

vi.mock('../api/tasks', () => ({
  getTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}));

const expectGetTasksCalledWith = (params: Record<string, unknown>) => {
  expect(getTasks).toHaveBeenLastCalledWith(
    expect.objectContaining(params),
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  );
};

describe('useTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getTasks).mockResolvedValue([sampleTask()]);
  });

  afterEach(() => {
    restoreRealTimers();
  });

  it('does not fetch tasks when disabled', () => {
    renderHook(() => useTasks(false));

    expect(getTasks).not.toHaveBeenCalled();
  });

  it('loads tasks successfully', async () => {
    const tasks = [sampleTask({ id: 1, title: 'First' }), sampleTask({ id: 2, title: 'Second' })];
    vi.mocked(getTasks).mockResolvedValue(tasks);

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    expect(getTasks).toHaveBeenCalledWith(
      {
        skip: 0,
        limit: 10,
        sort_by: 'created_at',
        sort_order: 'desc',
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(result.current.tasks).toEqual(tasks);
    expect(result.current.error).toBeNull();
  });

  it('tracks initial loading state while fetching tasks for the first time', async () => {
    let resolveTasks: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;
    vi.mocked(getTasks).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTasks = resolve;
        }),
    );

    const { result } = renderHook(() => useTasks(true));

    expect(result.current.isInitialLoading).toBe(true);
    expect(result.current.isRefreshing).toBe(false);

    await act(async () => {
      resolveTasks([sampleTask()]);
    });

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });
  });

  it('tracks background refresh without initial loading after the first fetch', async () => {
    let resolveFirst: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;
    let resolveSecond: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;
    let callCount = 0;

    vi.mocked(getTasks).mockImplementation(() => {
      callCount += 1;

      if (callCount === 1) {
        return new Promise((resolve) => {
          resolveFirst = resolve;
        });
      }

      return new Promise((resolve) => {
        resolveSecond = resolve;
      });
    });

    const { result } = renderHook(() => useTasks(true));

    await act(async () => {
      resolveFirst([sampleTask({ id: 1, title: 'First load' })]);
    });

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    await act(async () => {
      result.current.setStatusFilter('done');
    });

    await waitFor(() => {
      expect(result.current.isRefreshing).toBe(true);
      expect(result.current.isInitialLoading).toBe(false);
    });

    await act(async () => {
      resolveSecond([sampleTask({ id: 2, title: 'Filtered tasks' })]);
    });

    await waitFor(() => {
      expect(result.current.isRefreshing).toBe(false);
      expect(result.current.tasks).toEqual([sampleTask({ id: 2, title: 'Filtered tasks' })]);
    });
  });

  it('sets error when task fetch fails', async () => {
    vi.mocked(getTasks).mockRejectedValue(new ApiClientError('Failed to load tasks'));

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    expect(result.current.tasks).toEqual([]);
    expect(result.current.error).toBe('Failed to load tasks');
  });

  it('refetches tasks when filters change', async () => {
    enableFakeTimers();

    const { result } = renderHook(() => useTasks(true));

    await runPendingTimers();

    expect(getTasks).toHaveBeenCalledTimes(1);

    await act(async () => {
      result.current.setStatusFilter('done');
    });
    await runPendingTimers();

    expectGetTasksCalledWith({
      status: 'done',
      skip: 0,
    });

    await act(async () => {
      result.current.setSearchFilter('billing');
    });

    expect(getTasks).toHaveBeenCalledTimes(2);

    await advanceDebounce(SEARCH_DEBOUNCE_MS);

    expectGetTasksCalledWith({
      search: 'billing',
      skip: 0,
    });
  });

  it('debounces search requests until typing stops', async () => {
    enableFakeTimers();

    const { result } = renderHook(() => useTasks(true));

    await runPendingTimers();

    expect(getTasks).toHaveBeenCalledTimes(1);

    await act(async () => {
      result.current.setSearchFilter('b');
      result.current.setSearchFilter('bi');
      result.current.setSearchFilter('bill');
    });

    expect(getTasks).toHaveBeenCalledTimes(1);
    expect(result.current.filters.search).toBe('bill');

    await advanceDebounce(SEARCH_DEBOUNCE_MS);

    expect(getTasks).toHaveBeenCalledTimes(2);
    expectGetTasksCalledWith({
      search: 'bill',
    });
  });

  it('updates pagination state', async () => {
    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    act(() => {
      result.current.nextPage();
    });

    await waitFor(() => {
      expectGetTasksCalledWith({
        skip: 10,
        limit: 10,
      });
    });

    expect(result.current.currentPage).toBe(2);
  });

  it('moves back to the previous page', async () => {
    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    act(() => {
      result.current.nextPage();
      result.current.prevPage();
    });

    await waitFor(() => {
      expectGetTasksCalledWith({
        skip: 0,
        limit: 10,
      });
    });

    expect(result.current.currentPage).toBe(1);
  });

  it('ignores stale responses when a newer fetch is started', async () => {
    let resolveFirst: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;
    let resolveSecond: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;
    let callCount = 0;

    vi.mocked(getTasks).mockImplementation(() => {
      callCount += 1;

      if (callCount === 1) {
        return new Promise((resolve) => {
          resolveFirst = resolve;
        });
      }

      return new Promise((resolve) => {
        resolveSecond = resolve;
      });
    });

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(getTasks).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      result.current.setStatusFilter('done');
    });

    await waitFor(() => {
      expect(getTasks).toHaveBeenCalledTimes(2);
    });

    const freshTasks = [sampleTask({ id: 2, title: 'Fresh tasks' })];
    const staleTasks = [sampleTask({ id: 1, title: 'Stale tasks' })];

    await act(async () => {
      resolveSecond(freshTasks);
    });

    await waitFor(() => {
      expect(result.current.tasks).toEqual(freshTasks);
    });

    await act(async () => {
      resolveFirst(staleTasks);
    });

    expect(result.current.tasks).toEqual(freshTasks);
    expect(result.current.error).toBeNull();
  });

  it('ignores aborted fetch errors', async () => {
    let callCount = 0;

    vi.mocked(getTasks).mockImplementation((_params, options) => {
      callCount += 1;

      if (callCount === 1) {
        return new Promise((_resolve, reject) => {
          options?.signal?.addEventListener('abort', () => {
            reject(new ApiClientError('canceled', new axios.CanceledError('canceled')));
          });
        });
      }

      return Promise.resolve([sampleTask({ id: 2, title: 'Latest tasks' })]);
    });

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(getTasks).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      result.current.setStatusFilter('done');
    });

    await waitFor(() => {
      expect(result.current.tasks).toEqual([sampleTask({ id: 2, title: 'Latest tasks' })]);
      expect(result.current.error).toBeNull();
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });
  });

  it('cancels in-flight fetch on unmount', async () => {
    let capturedSignal: AbortSignal | undefined;
    let resolveTasks: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;

    vi.mocked(getTasks).mockImplementation((_params, options) => {
      capturedSignal = options?.signal;

      return new Promise((resolve) => {
        resolveTasks = resolve;
      });
    });

    const { unmount } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(capturedSignal).toBeDefined();
    });

    unmount();

    expect(capturedSignal?.aborted).toBe(true);

    await act(async () => {
      resolveTasks([sampleTask({ title: 'After unmount' })]);
    });
  });

  it('creates a task and refreshes the list', async () => {
    vi.mocked(createTask).mockResolvedValue(sampleTask({ id: 3, title: 'Created task' }));

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let createError: string | null = 'pending';
    await act(async () => {
      createError = await result.current.createTask({
        title: 'Created task',
        description: 'Details',
        priority: 'high',
      });
    });

    expect(createError).toBeNull();
    expect(createTask).toHaveBeenCalledWith({
      title: 'Created task',
      description: 'Details',
      priority: 'high',
    });
    expect(getTasks).toHaveBeenCalledTimes(2);
    expect(result.current.isCreating).toBe(false);
  });

  it('returns error when task creation fails', async () => {
    vi.mocked(createTask).mockRejectedValue(new ApiClientError('Invalid task data'));

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let createError: string | null = null;
    await act(async () => {
      createError = await result.current.createTask({
        title: 'Bad task',
      });
    });

    expect(createError).toBe('Invalid task data');
    expect(result.current.error).toBe('Invalid task data');
    expect(result.current.isCreating).toBe(false);
  });

  it('updates task status and refreshes the list', async () => {
    vi.mocked(updateTask).mockResolvedValue(sampleTask({ status: 'in_progress' }));

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let updateError: string | null = 'pending';
    await act(async () => {
      updateError = await result.current.updateTaskStatus(1, 'in_progress');
    });

    expect(updateError).toBeNull();
    expect(updateTask).toHaveBeenCalledWith(1, { status: 'in_progress' });
    expect(getTasks).toHaveBeenCalledTimes(2);
    expect(result.current.updatingTaskId).toBeNull();
  });

  it('returns error when status update fails', async () => {
    vi.mocked(updateTask).mockRejectedValue(
      new ApiClientError("Invalid status transition from 'new' to 'done'"),
    );

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let updateError: string | null = null;
    await act(async () => {
      updateError = await result.current.updateTaskStatus(1, 'done');
    });

    expect(updateError).toBe("Invalid status transition from 'new' to 'done'");
    expect(result.current.error).toBe("Invalid status transition from 'new' to 'done'");
    expect(result.current.updatingTaskId).toBeNull();
  });

  it('deletes a task and refreshes the list', async () => {
    vi.mocked(deleteTask).mockResolvedValue(undefined);

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let deleteError: string | null = 'pending';
    await act(async () => {
      deleteError = await result.current.removeTask(1);
    });

    expect(deleteError).toBeNull();
    expect(deleteTask).toHaveBeenCalledWith(1);
    expect(getTasks).toHaveBeenCalledTimes(2);
    expect(result.current.deletingTaskId).toBeNull();
  });

  it('returns error when delete fails', async () => {
    vi.mocked(deleteTask).mockRejectedValue(
      new ApiClientError('Only admin users can delete tasks'),
    );

    const { result } = renderHook(() => useTasks(true));

    await waitFor(() => {
      expect(result.current.isInitialLoading).toBe(false);
      expect(result.current.isRefreshing).toBe(false);
    });

    let deleteError: string | null = null;
    await act(async () => {
      deleteError = await result.current.removeTask(1);
    });

    expect(deleteError).toBe('Only admin users can delete tasks');
    expect(result.current.error).toBe('Only admin users can delete tasks');
    expect(result.current.deletingTaskId).toBeNull();
  });
});
