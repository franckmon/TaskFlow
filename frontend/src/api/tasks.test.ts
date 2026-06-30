import { AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import api from './client';
import { sampleTask } from '../test/fixtures';
import {
  createTask,
  deleteTask,
  getTask,
  getTasks,
  updateTask,
} from './tasks';

const axiosResponse = (data: unknown, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: new AxiosHeaders(),
  config: { headers: new AxiosHeaders() } as InternalAxiosRequestConfig,
});

describe('tasks api', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads tasks with query params', async () => {
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue(axiosResponse([sampleTask()]));

    await expect(getTasks({ search: 'billing' })).resolves.toEqual([sampleTask()]);
    expect(getSpy).toHaveBeenCalledWith('/tasks/', { params: { search: 'billing' } });
  });

  it('passes abort signal when provided', async () => {
    const controller = new AbortController();
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue(axiosResponse([sampleTask()]));

    await getTasks({ status: 'done' }, { signal: controller.signal });

    expect(getSpy).toHaveBeenCalledWith('/tasks/', {
      params: { status: 'done' },
      signal: controller.signal,
    });
  });

  it('loads a single task by id', async () => {
    vi.spyOn(api, 'get').mockResolvedValue(axiosResponse(sampleTask({ id: 4 })));

    await expect(getTask(4)).resolves.toEqual(sampleTask({ id: 4 }));
  });

  it('creates, updates, and deletes tasks', async () => {
    vi.spyOn(api, 'post').mockResolvedValue(
      axiosResponse(sampleTask({ id: 2, title: 'New task' })),
    );
    vi.spyOn(api, 'put').mockResolvedValue(
      axiosResponse(sampleTask({ id: 2, status: 'done' })),
    );
    vi.spyOn(api, 'delete').mockResolvedValue(axiosResponse(undefined, 204));

    await expect(
      createTask({ title: 'New task', description: '', priority: 'normal' }),
    ).resolves.toEqual(sampleTask({ id: 2, title: 'New task' }));

    await expect(updateTask(2, { status: 'done' })).resolves.toEqual(
      sampleTask({ id: 2, status: 'done' }),
    );

    await expect(deleteTask(2)).resolves.toBeUndefined();
  });
});
