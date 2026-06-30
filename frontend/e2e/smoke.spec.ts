import { expect, test } from '@playwright/test';
import { expectAuthenticatedWorkspace, expectLoginScreen, loginAsAdmin } from './helpers/auth';
import {
  createTaskViaUi,
  expectTaskStatus,
  uniqueTaskTitle,
  updateTaskStatusViaUi,
  waitForTasksWorkspace,
} from './helpers/tasks';

test('smoke: application start, login, tasks, create, status update', async ({ page }) => {
  await page.goto('/');
  await expectLoginScreen(page);

  await loginAsAdmin(page);
  await expectAuthenticatedWorkspace(page);

  await waitForTasksWorkspace(page);
  await expect(page.getByText('Loading tasks...')).not.toBeVisible();
  await expect(
    page.getByRole('columnheader', { name: 'Title' }).or(page.getByText('No tasks found')),
  ).toBeVisible();

  const title = uniqueTaskTitle('Smoke');
  await createTaskViaUi(page, { title });
  await expect(page.getByRole('row').filter({ hasText: title })).toBeVisible();

  await updateTaskStatusViaUi(page, title, 'in_progress');
  await expectTaskStatus(page, title, 'in progress');
});
