import { expect, Page } from '@playwright/test';

const adminUsername = 'admin';
const adminPassword = 'admin';
const regularUsername = 'regular';
const regularPassword = 'userpassword';

export const regularUserCredentials = {
  username: regularUsername,
  password: regularPassword,
};

export async function openLoginPage(page: Page) {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Task Flow Login' })).toBeVisible();
}

export async function fillLoginForm(
  page: Page,
  credentials: { username: string; password: string },
) {
  const form = page.locator('form');
  await form.locator('input[type="text"]').fill(credentials.username);
  await form.locator('input[type="password"]').fill(credentials.password);
}

export async function submitLogin(page: Page) {
  await page.getByRole('button', { name: 'Login' }).click();
}

export async function loginAsAdmin(page: Page) {
  await openLoginPage(page);
  await fillLoginForm(page, { username: adminUsername, password: adminPassword });
  await submitLogin(page);
  await expect(page.getByText(/Welcome/i)).toBeVisible();
}

export async function loginAsRegularUser(page: Page) {
  await openLoginPage(page);
  await fillLoginForm(page, regularUserCredentials);
  await submitLogin(page);
  await expect(page.getByText(/Welcome/i)).toBeVisible();
}

export async function getSessionToken(page: Page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));
  expect(token).toBeTruthy();
  return token as string;
}

export async function expectAuthenticatedWorkspace(page: Page) {
  await expect(page.getByRole('heading', { name: 'Task Flow' })).toBeVisible();
  await expect(page.getByText(/Welcome/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Create New Task' })).toBeVisible();
}

export async function expectLoginScreen(page: Page) {
  await expect(page.getByRole('heading', { name: 'Task Flow Login' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
}
