import { expect, test } from '@playwright/test';
import {
  expectAuthenticatedWorkspace,
  expectLoginScreen,
  fillLoginForm,
  loginAsAdmin,
  openLoginPage,
  submitLogin,
} from './helpers/auth';
import { abortApiRoute, delayApiRoute, delayTasksFetchAfterLogin } from './helpers/errors';
import { getAdminToken } from './helpers/api';
import { searchTasks, uniqueTaskTitle, waitForTasksWorkspace } from './helpers/tasks';

test.describe('Application error scenarios', () => {
  test('shows an error when the backend is unavailable during login', async ({ page }) => {
    await abortApiRoute(page, '**/auth/login');

    await openLoginPage(page);
    await fillLoginForm(page, { username: 'admin', password: 'admin' });
    await submitLogin(page);

    await expect(page.getByText('An unexpected error occurred. Please try again.')).toBeVisible();
    await expectLoginScreen(page);
  });

  test('shows an error when the backend is unavailable while loading tasks', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    await abortApiRoute(page, '**/tasks**');
    await searchTasks(page, uniqueTaskTitle('Unavailable'));

    await expect(page.getByText('An unexpected error occurred. Please try again.')).toBeVisible();
  });

  test('shows API validation errors when task creation fails', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    const createSection = page.getByRole('heading', { name: 'Create New Task' }).locator('..');
    await createSection.locator('input[type="text"]').fill('ab');
    await createSection.getByRole('button', { name: 'Create Task' }).click();

    await expect(createSection.getByText(/at least 3 characters/i)).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Task' })).toBeVisible();
  });

  test('returns to the login screen for an unauthorized saved session', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'invalid-session-token');
    });

    await page.goto('/');

    await expectLoginScreen(page);
    await expect(page.getByRole('heading', { name: 'Create New Task' })).not.toBeVisible();
  });

  test('shows an unauthorized error when task requests are rejected', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    await page.evaluate(() => {
      localStorage.setItem('token', 'invalid-session-token');
    });

    await searchTasks(page, uniqueTaskTitle('Unauthorized'));

    await expect(page.getByText('Invalid authentication credentials')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Task' })).toBeVisible();
  });

  test('shows an empty state when no tasks match the filters', async ({ page }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    await searchTasks(page, uniqueTaskTitle('Empty'));

    await expect(page.getByText('No tasks found')).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Title' })).not.toBeVisible();
  });

  test('shows loading while the saved session is restored', async ({ page, request }) => {
    const token = await getAdminToken(request);

    await delayApiRoute(page, '**/auth/me', 1000);

    await page.addInitScript((storedToken: string) => {
      localStorage.setItem('token', storedToken);
    }, token);

    await page.goto('/');

    await expect(page.getByText('Loading...', { exact: true })).toBeVisible();
    await expectAuthenticatedWorkspace(page);
  });

  test('shows loading while tasks are being fetched', async ({ page }) => {
    const tasksDelay = await delayTasksFetchAfterLogin(page, 1500);

    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    tasksDelay.enable();
    await searchTasks(page, uniqueTaskTitle('Loading'));

    await expect(page.getByText('Loading tasks...')).toBeVisible();
    await expect(page.getByText('Loading tasks...')).not.toBeVisible({ timeout: 10_000 });
  });

  test('shows loading while login is in progress', async ({ page }) => {
    await delayApiRoute(page, '**/auth/login', 1000, { methods: ['POST'] });

    await openLoginPage(page);
    await fillLoginForm(page, { username: 'admin', password: 'admin' });
    await submitLogin(page);

    await expect(page.getByRole('button', { name: 'Logging in...' })).toBeVisible();
    await expectAuthenticatedWorkspace(page);
  });
});
