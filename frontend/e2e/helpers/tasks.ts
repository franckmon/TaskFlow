import { expect, Page } from '@playwright/test';

export interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: 'low' | 'normal' | 'high';
}

export function uniqueTaskTitle(label: string) {
  return `E2E ${label} ${Date.now()}`;
}

function createTaskSection(page: Page) {
  return page.getByRole('heading', { name: 'Create New Task' }).locator('..');
}

function tasksToolbar(page: Page) {
  return page.locator('.bg-white').filter({ has: page.getByPlaceholder('Search tasks...') });
}

export async function waitForTasksWorkspace(page: Page) {
  await expect(page.getByRole('heading', { name: 'Create New Task' })).toBeVisible();
  await expect(page.getByPlaceholder('Search tasks...')).toBeVisible();
}

export async function createTaskViaUi(page: Page, task: CreateTaskInput) {
  const section = createTaskSection(page);
  await section.locator('input[type="text"]').fill(task.title);

  if (task.description) {
    await section.locator('textarea').fill(task.description);
  }

  if (task.priority) {
    await section.locator('select').selectOption(task.priority);
  }

  await section.getByRole('button', { name: 'Create Task' }).click();
  await expect(taskRow(page, task.title)).toBeVisible();
}

export async function searchTasks(page: Page, query: string) {
  await page.getByPlaceholder('Search tasks...').fill(query);
}

export async function setStatusFilter(page: Page, status: '' | 'new' | 'in_progress' | 'done') {
  const toolbar = tasksToolbar(page);
  await toolbar.getByRole('combobox').nth(0).selectOption(status);
}

export async function setPriorityFilter(page: Page, priority: '' | 'low' | 'normal' | 'high') {
  const toolbar = tasksToolbar(page);
  await toolbar.getByRole('combobox').nth(1).selectOption(priority);
}

export async function setSort(page: Page, sortBy: 'created_at' | 'priority', order: 'asc' | 'desc') {
  const toolbar = tasksToolbar(page);
  await toolbar.getByRole('combobox').nth(2).selectOption(sortBy);
  await toolbar.getByRole('combobox').nth(3).selectOption(order);
}

export function taskRow(page: Page, title: string) {
  return page.getByRole('row').filter({ hasText: title });
}

export async function updateTaskStatusViaUi(
  page: Page,
  title: string,
  status: 'new' | 'in_progress' | 'done',
) {
  const row = taskRow(page, title);
  await row.getByRole('combobox').selectOption(status);
}

export async function expectTaskVisible(page: Page, title: string) {
  await expect(taskRow(page, title)).toBeVisible();
}

export async function expectTaskHidden(page: Page, title: string) {
  await expect(taskRow(page, title)).not.toBeVisible();
}

export async function expectTaskStatus(page: Page, title: string, statusLabel: string) {
  const row = taskRow(page, title);
  await expect(row.getByText(statusLabel, { exact: true })).toBeVisible();
}

export async function goToNextTasksPage(page: Page) {
  await page.getByRole('button', { name: 'Next' }).click();
}

export async function goToPreviousTasksPage(page: Page) {
  await page.getByRole('button', { name: 'Previous' }).click();
}

export async function expectCurrentPage(page: Page, pageNumber: number) {
  await expect(
    page.getByText(`Page ${pageNumber}`, { exact: true }),
  ).toBeVisible();
}

export async function deleteTaskViaUi(page: Page, title: string) {
  page.once('dialog', (dialog) => {
    expect(dialog.type()).toBe('confirm');
    expect(dialog.message()).toContain('Are you sure you want to delete this task?');
    void dialog.accept();
  });

  const row = taskRow(page, title);
  await row.getByRole('button', { name: 'Delete' }).click();
  await expectTaskHidden(page, title);
}

export async function expectDeleteButtonVisible(page: Page, title: string) {
  const row = taskRow(page, title);
  await expect(row.getByRole('button', { name: 'Delete' })).toBeVisible();
}

export async function expectDeleteButtonHidden(page: Page, title: string) {
  const row = taskRow(page, title);
  await expect(row.getByRole('button', { name: 'Delete' })).not.toBeVisible();
}
