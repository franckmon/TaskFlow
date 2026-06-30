import { expect, test } from '@playwright/test';
import {
  expectAuthenticatedWorkspace,
  expectLoginScreen,
  fillLoginForm,
  loginAsAdmin,
  openLoginPage,
  submitLogin,
} from './helpers/auth';

test.describe('Authentication', () => {
  test('logs in with valid credentials', async ({ page }) => {
    await loginAsAdmin(page);

    await expectAuthenticatedWorkspace(page);
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
  });

  test('shows an error for invalid credentials', async ({ page }) => {
    await openLoginPage(page);
    await fillLoginForm(page, { username: 'admin', password: 'wrong-password' });
    await submitLogin(page);

    await expect(page.getByText('Incorrect username or password')).toBeVisible();
    await expectLoginScreen(page);
    await expect(page.getByText('Welcome, admin')).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Task' })).not.toBeVisible();
  });

  test('keeps the user signed in after reload', async ({ page }) => {
    await loginAsAdmin(page);
    await expectAuthenticatedWorkspace(page);

    await page.reload();

    await expectAuthenticatedWorkspace(page);
    await expect(page.getByRole('heading', { name: 'Task Flow Login' })).not.toBeVisible();
  });

  test('logs out back to the login screen', async ({ page }) => {
    await loginAsAdmin(page);
    await expectAuthenticatedWorkspace(page);

    await page.getByRole('button', { name: 'Logout' }).click();

    await expectLoginScreen(page);
    await expect(page.getByText('Welcome, admin')).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Task' })).not.toBeVisible();
  });

  test('shows the login screen when the saved session is not valid', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'invalid-session-token');
    });

    await page.goto('/');

    await expectLoginScreen(page);
    await expect(page.getByText('Welcome, admin')).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Create New Task' })).not.toBeVisible();
  });
});
