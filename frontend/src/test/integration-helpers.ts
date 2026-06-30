import { screen } from '@testing-library/react';
import { UserEvent } from '@testing-library/user-event';
import { expect, vi } from 'vitest';
import { getMe, getStoredToken, login } from '../api/auth';
import { getTasks } from '../api/tasks';
import { sampleTask, sampleUser } from './fixtures';
import { resolveDeferred } from './utils/async';
import {
  waitForAuthenticatedWorkspace,
  waitForLoginScreen,
  waitForTasksLoaded,
} from './utils/wait';

export { resolveDeferred };

export function setupUnauthenticatedSession() {
  vi.mocked(getStoredToken).mockReturnValue(null);
}

export function setupAuthenticatedApi() {
  vi.mocked(login).mockResolvedValue({
    access_token: 'token',
    token_type: 'bearer',
    role: 'admin',
  });
  vi.mocked(getMe).mockResolvedValue(sampleUser());
  vi.mocked(getTasks).mockResolvedValue([sampleTask()]);
}

export async function loginThroughUi(user: UserEvent) {
  await waitForLoginScreen();

  const [usernameInput, passwordInput] = screen.getAllByDisplayValue('');
  await user.type(usernameInput, 'admin');
  await user.type(passwordInput, 'password');
  await user.click(screen.getByRole('button', { name: /login/i }));

  await waitForAuthenticatedWorkspace('admin');
}

export async function waitForTasksToLoad() {
  await waitForTasksLoaded();
}

// Combobox order on TasksPage:
const TASKS_PAGE_STATIC_COMBOBOX_COUNT = 5;

export function getFilterSelects() {
  const [, statusFilter, priorityFilter] = screen.getAllByRole('combobox');
  return { statusFilter, priorityFilter };
}

export function getSortSelects() {
  const comboboxes = screen.getAllByRole('combobox');
  return {
    sortBy: comboboxes[3],
    sortOrder: comboboxes[4],
  };
}

export function getRowStatusSelect(rowIndex = 0) {
  return screen.getAllByRole('combobox')[TASKS_PAGE_STATIC_COMBOBOX_COUNT + rowIndex];
}

export function getCreateFormFields() {
  const [titleInput, descriptionInput] = screen.getAllByRole('textbox');
  const [prioritySelect] = screen.getAllByRole('combobox');

  return {
    titleInput,
    descriptionInput,
    prioritySelect,
  };
}
