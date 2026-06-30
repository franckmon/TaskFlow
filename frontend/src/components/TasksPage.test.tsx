import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { sampleTask } from '../test/fixtures';
import { TasksPage } from './TasksPage';

const createTask = vi.fn();

const buildUseTasksState = (overrides: Record<string, unknown> = {}) => ({
  tasks: [],
  isInitialLoading: false,
  isRefreshing: false,
  isCreating: false,
  deletingTaskId: null,
  updatingTaskId: null,
  error: null,
  filters: { status: '', priority: '', search: '' },
  pagination: { skip: 0, limit: 10 },
  sorting: { sort_by: 'created_at', sort_order: 'desc' },
  currentPage: 1,
  hasNextPage: false,
  setStatusFilter: vi.fn(),
  setPriorityFilter: vi.fn(),
  setSearchFilter: vi.fn(),
  setSortBy: vi.fn(),
  setSortOrder: vi.fn(),
  nextPage: vi.fn(),
  prevPage: vi.fn(),
  updateTaskStatus: vi.fn(),
  removeTask: vi.fn(),
  createTask,
  ...overrides,
});

let useTasksState = buildUseTasksState();

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { username: 'admin', role: 'admin' },
  }),
}));

vi.mock('../hooks/useTasks', () => ({
  useTasks: () => useTasksState,
}));

describe('TasksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useTasksState = buildUseTasksState();
    createTask.mockImplementation(async () => {
      useTasksState = buildUseTasksState({ error: 'Invalid task data' });
      return 'Invalid task data';
    });
  });

  it('shows create form error when task creation fails', async () => {
    const user = userEvent.setup();

    render(<TasksPage />);

    const [titleInput] = screen.getAllByRole('textbox');
    await user.type(titleInput, 'Broken task');
    await user.click(screen.getByRole('button', { name: /create task/i }));

    expect(await screen.findByText('Invalid task data')).toBeInTheDocument();
    expect(createTask).toHaveBeenCalled();
  });

  it('shows initial loading state before tasks are available', () => {
    useTasksState = buildUseTasksState({ isInitialLoading: true });

    render(<TasksPage />);

    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
    expect(screen.queryByText('Updating...')).not.toBeInTheDocument();
  });

  it('keeps the table visible during background refresh', () => {
    useTasksState = buildUseTasksState({
      isRefreshing: true,
      tasks: [sampleTask({ title: 'Existing task' })],
    });

    render(<TasksPage />);

    expect(screen.getByText('Existing task')).toBeInTheDocument();
    expect(screen.getByText('Updating...')).toBeInTheDocument();
    expect(screen.queryByText('Loading tasks...')).not.toBeInTheDocument();
  });
});
