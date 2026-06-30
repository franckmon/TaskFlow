import { LoginRequest, Task, TaskCreate, User } from '../types';

export const sampleTask = (overrides: Partial<Task> = {}): Task => ({
  id: 1,
  title: 'Sample task',
  description: 'Task description',
  status: 'new',
  priority: 'normal',
  created_at: '2024-06-15T10:00:00.000Z',
  updated_at: '2024-06-15T10:00:00.000Z',
  ...overrides,
});

export const sampleUser = (overrides: Partial<User> = {}): User => ({
  username: 'admin',
  role: 'admin',
  ...overrides,
});

export const emptyCreateForm = (): TaskCreate => ({
  title: '',
  description: '',
  priority: 'normal',
});

export const emptyLoginForm = (): LoginRequest => ({
  username: '',
  password: '',
});
