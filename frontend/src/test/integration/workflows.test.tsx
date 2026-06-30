import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import {
  clearStoredToken,
  getMe,
  getStoredToken,
  login,
  logout,
  storeToken,
} from '../../api/auth';
import { ApiClientError } from '../../api/client';
import {
  createTask,
  deleteTask,
  getTasks,
  updateTask,
} from '../../api/tasks';
import { sampleTask } from '../fixtures';
import {
  getCreateFormFields,
  getFilterSelects,
  getRowStatusSelect,
  getSortSelects,
  loginThroughUi,
  resolveDeferred,
  setupAuthenticatedApi,
  setupUnauthenticatedSession,
  waitForTasksToLoad,
} from '../integration-helpers';
import { renderApp } from '../render-app';
import { advanceDebounce, enableFakeTimers, restoreRealTimers } from '../utils/async';
import { createUser } from '../utils/user-event';
import { waitForText } from '../utils/wait';

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  getMe: vi.fn(),
  storeToken: vi.fn(),
  clearStoredToken: vi.fn(),
  logout: vi.fn(),
  getStoredToken: vi.fn(),
}));

vi.mock('../../api/tasks', () => ({
  getTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}));

describe('Task Flow integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupUnauthenticatedSession();
    setupAuthenticatedApi();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('lets the user log in and reach the tasks workspace', async () => {
    const user = createUser();

    renderApp();
    await loginThroughUi(user);

    expect(screen.getByRole('heading', { name: /create new task/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search tasks/i)).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith({ username: 'admin', password: 'password' });
    expect(storeToken).toHaveBeenCalledWith('token');
  });

  it('shows session loading before the login screen', async () => {
    let resolveProfile: (value: Awaited<ReturnType<typeof getMe>>) => void = () => undefined;

    vi.mocked(getStoredToken).mockReturnValue('existing-token');
    vi.mocked(getMe).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveProfile = resolve;
        }),
    );

    renderApp();

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await resolveDeferred(resolveProfile, {
      username: 'admin',
      role: 'admin',
    });

    await waitForText(/welcome, admin/i);
  });

  it('shows loading state while tasks are fetched', async () => {
    const user = createUser();
    let resolveTasks: (value: ReturnType<typeof sampleTask>[]) => void = () => undefined;

    vi.mocked(getTasks).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTasks = resolve;
        }),
    );

    renderApp();
    await loginThroughUi(user);

    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();

    await resolveDeferred(resolveTasks, [sampleTask()]);

    await waitForText('Sample task');
  });

  it('shows a lightweight refresh indicator while keeping the table visible', async () => {
    const user = createUser();
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

    renderApp();
    await loginThroughUi(user);

    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();

    await resolveDeferred(resolveFirst, [sampleTask({ title: 'Existing task' })]);

    await waitForText('Existing task');

    const { statusFilter } = getFilterSelects();
    await user.selectOptions(statusFilter, 'done');

    await waitFor(() => {
      expect(screen.getByText('Updating...')).toBeInTheDocument();
      expect(screen.getByText('Existing task')).toBeInTheDocument();
    });

    await resolveDeferred(resolveSecond, [sampleTask({ title: 'Done task', status: 'done' })]);

    await waitFor(() => {
      expect(screen.queryByText('Updating...')).not.toBeInTheDocument();
      expect(screen.getByText('Done task')).toBeInTheDocument();
    });
  });

  it('shows an empty state when there are no tasks', async () => {
    const user = createUser();
    vi.mocked(getTasks).mockResolvedValue([]);

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    expect(screen.getByText('No tasks found')).toBeInTheDocument();
  });

  it('shows an api error when task loading fails', async () => {
    const user = createUser();
    vi.mocked(getTasks).mockRejectedValue(new ApiClientError('Failed to load tasks'));

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    expect(screen.getByText('Failed to load tasks')).toBeInTheDocument();
  });

  it('lets the user create a task', async () => {
    const user = createUser();
    let callCount = 0;
    vi.mocked(getTasks).mockImplementation(async () => {
      callCount += 1;
      return callCount === 1
        ? []
        : [sampleTask({ id: 2, title: 'Deploy release', priority: 'high' })];
    });
    vi.mocked(createTask).mockResolvedValue(
      sampleTask({ id: 2, title: 'Deploy release', priority: 'high' }),
    );

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    const { titleInput, descriptionInput, prioritySelect } = getCreateFormFields();
    await user.type(titleInput, 'Deploy release');
    await user.type(descriptionInput, 'Release notes');
    await user.selectOptions(prioritySelect, 'high');
    await user.click(screen.getByRole('button', { name: /create task/i }));

    await waitFor(() => {
      expect(createTask).toHaveBeenCalledWith({
        title: 'Deploy release',
        description: 'Release notes',
        priority: 'high',
      });
    });

    await waitForText('Deploy release');
  });

  it('lets the user search tasks', async () => {
    const user = createUser();
    vi.mocked(getTasks).mockImplementation(async (params) => {
      if (params?.search?.includes('billing')) {
        return [sampleTask({ id: 3, title: 'Billing report' })];
      }

      return [sampleTask(), sampleTask({ id: 2, title: 'Other task' })];
    });

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    enableFakeTimers();
    fireEvent.change(screen.getByPlaceholderText(/search tasks/i), {
      target: { value: 'billing' },
    });
    await advanceDebounce();
    restoreRealTimers();

    await waitFor(() => {
      expect(getTasks).toHaveBeenLastCalledWith(
        expect.objectContaining({ search: 'billing' }),
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });

    await waitForText('Billing report');
  });

  it('lets the user filter tasks by status and priority', async () => {
    const user = createUser();
    vi.mocked(getTasks).mockImplementation(async (params) => {
      if (params?.status === 'done' && params?.priority === 'high') {
        return [sampleTask({ id: 2, title: 'Done task', status: 'done', priority: 'high' })];
      }

      return [sampleTask()];
    });

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    const { statusFilter, priorityFilter } = getFilterSelects();
    await user.selectOptions(statusFilter, 'done');
    await user.selectOptions(priorityFilter, 'high');

    await waitFor(() => {
      expect(getTasks).toHaveBeenLastCalledWith(
        expect.objectContaining({
          status: 'done',
          priority: 'high',
          skip: 0,
        }),
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });

    await waitForText('Done task');
  });

  it('lets the user sort tasks', async () => {
    const user = createUser();

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    const { sortBy, sortOrder } = getSortSelects();
    await user.selectOptions(sortBy, 'priority');
    await user.selectOptions(sortOrder, 'asc');

    await waitFor(() => {
      expect(getTasks).toHaveBeenLastCalledWith(
        expect.objectContaining({
          sort_by: 'priority',
          sort_order: 'asc',
          skip: 0,
        }),
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });
  });

  it('lets the user change task status', async () => {
    const user = createUser();
    let callCount = 0;
    vi.mocked(getTasks).mockImplementation(async () => {
      callCount += 1;
      return callCount === 1
        ? [sampleTask({ id: 4, status: 'new' })]
        : [sampleTask({ id: 4, status: 'in_progress' })];
    });
    vi.mocked(updateTask).mockResolvedValue(sampleTask({ id: 4, status: 'in_progress' }));

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    await user.selectOptions(getRowStatusSelect(), 'in_progress');

    await waitFor(() => {
      expect(updateTask).toHaveBeenCalledWith(4, { status: 'in_progress' });
    });

    await waitForText('in progress');
  });

  it('lets the user delete a task', async () => {
    const user = createUser();
    let callCount = 0;
    vi.mocked(getTasks).mockImplementation(async () => {
      callCount += 1;
      return callCount === 1
        ? [sampleTask({ id: 5, title: 'Delete me' })]
        : [];
    });
    vi.mocked(deleteTask).mockResolvedValue(undefined);

    renderApp();
    await loginThroughUi(user);
    await waitForTasksToLoad();

    await user.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(deleteTask).toHaveBeenCalledWith(5);
    });

    await waitForText('No tasks found');
  });

  it('shows login error after failed authentication', async () => {
    const user = createUser();
    vi.mocked(login).mockRejectedValue(new ApiClientError('Incorrect username or password'));

    renderApp();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /task flow login/i })).toBeInTheDocument();
    });

    const [usernameInput, passwordInput] = screen.getAllByDisplayValue('');
    await user.type(usernameInput, 'admin');
    await user.type(passwordInput, 'wrong');
    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitForText('Incorrect username or password');
    expect(clearStoredToken).not.toHaveBeenCalled();
    expect(logout).not.toHaveBeenCalled();
  });
});
