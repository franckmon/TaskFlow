import { expect, test } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';
import {
  createTaskViaApi,
  fetchTasksFromApi,
  getAdminToken,
} from './helpers/api';
import {
  createTaskViaUi,
  expectCurrentPage,
  expectTaskHidden,
  expectTaskStatus,
  expectTaskVisible,
  goToNextTasksPage,
  searchTasks,
  setPriorityFilter,
  setSort,
  setStatusFilter,
  taskRow,
  uniqueTaskTitle,
  updateTaskStatusViaUi,
  waitForTasksWorkspace,
} from './helpers/tasks';

test.describe.configure({ mode: 'serial' });

test.describe('Task management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);
  });

  test('creates a task through the form', async ({ page, request }) => {
    const title = uniqueTaskTitle('Create');
    const description = 'Created from Playwright';

    await createTaskViaUi(page, {
      title,
      description,
      priority: 'high',
    });

    await expectTaskVisible(page, title);
    await expect(taskRow(page, title)).toContainText('high');

    const token = await getAdminToken(request);
    const tasks = await fetchTasksFromApi(request, token, { search: title });

    expect(tasks).toHaveLength(1);
    expect(tasks[0]).toMatchObject({
      title,
      description,
      priority: 'high',
      status: 'new',
    });
  });

  test('searches tasks by title', async ({ page, request }) => {
    const token = await getAdminToken(request);
    const visibleTitle = uniqueTaskTitle('Search Visible');
    const hiddenTitle = uniqueTaskTitle('Search Hidden');

    await createTaskViaApi(request, token, { title: visibleTitle, description: 'billing report' });
    await createTaskViaApi(request, token, { title: hiddenTitle, description: 'other work' });

    await page.reload();
    await waitForTasksWorkspace(page);

    await searchTasks(page, 'billing');

    await expectTaskVisible(page, visibleTitle);
    await expectTaskHidden(page, hiddenTitle);

    const apiTasks = await fetchTasksFromApi(request, token, { search: 'billing' });
    expect(apiTasks.some((task) => task.title === visibleTitle)).toBeTruthy();
    expect(apiTasks.some((task) => task.title === hiddenTitle)).toBeFalsy();
  });

  test('filters tasks by status and priority', async ({ page, request }) => {
    const token = await getAdminToken(request);
    const matchingTitle = uniqueTaskTitle('Filter Match');
    const otherTitle = uniqueTaskTitle('Filter Other');

    await createTaskViaApi(request, token, {
      title: matchingTitle,
      priority: 'high',
    });
    await createTaskViaApi(request, token, {
      title: otherTitle,
      priority: 'low',
    });

    await page.reload();
    await waitForTasksWorkspace(page);

    await setStatusFilter(page, 'new');
    await setPriorityFilter(page, 'high');

    await expectTaskVisible(page, matchingTitle);
    await expectTaskHidden(page, otherTitle);

    const apiTasks = await fetchTasksFromApi(request, token, {
      status: 'new',
      priority: 'high',
      search: 'Filter',
    });

    expect(apiTasks.some((task) => task.title === matchingTitle)).toBeTruthy();
    expect(apiTasks.some((task) => task.title === otherTitle)).toBeFalsy();
  });

  test('sorts tasks by priority ascending', async ({ page, request }) => {
    const token = await getAdminToken(request);
    const runId = uniqueTaskTitle('Sort');
    const lowTitle = `${runId} Low`;
    const normalTitle = `${runId} Normal`;

    await createTaskViaApi(request, token, { title: lowTitle, priority: 'low' });
    await createTaskViaApi(request, token, { title: normalTitle, priority: 'normal' });

    await page.reload();
    await waitForTasksWorkspace(page);
    await searchTasks(page, runId);

    await setSort(page, 'priority', 'asc');

    const rows = page.getByRole('row').filter({ hasText: runId });
    await expect(rows).toHaveCount(2);
    await expect(rows.nth(0)).toContainText(lowTitle);
    await expect(rows.nth(1)).toContainText(normalTitle);

    const apiTasks = await fetchTasksFromApi(request, token, {
      search: runId,
      sort_by: 'priority',
      sort_order: 'asc',
    });

    expect(apiTasks).toHaveLength(2);
    expect(apiTasks[0].title).toBe(lowTitle);
    expect(apiTasks[1].title).toBe(normalTitle);
  });

  test('paginates task results', async ({ page, request }) => {
    const token = await getAdminToken(request);
    const prefix = uniqueTaskTitle('Page');

    for (let index = 1; index <= 11; index += 1) {
      await createTaskViaApi(request, token, {
        title: `${prefix} ${String(index).padStart(2, '0')}`,
      });
    }

    await page.reload();
    await waitForTasksWorkspace(page);
    await searchTasks(page, prefix);

    await expectCurrentPage(page, 1);
    await expectTaskVisible(page, `${prefix} 11`);
    await expectTaskHidden(page, `${prefix} 01`);

    await goToNextTasksPage(page);

    await expectCurrentPage(page, 2);
    await expectTaskVisible(page, `${prefix} 01`);
    await expectTaskHidden(page, `${prefix} 11`);

    const firstPage = await fetchTasksFromApi(request, token, {
      search: prefix,
      skip: 0,
      limit: 10,
    });
    const secondPage = await fetchTasksFromApi(request, token, {
      search: prefix,
      skip: 10,
      limit: 10,
    });

    expect(firstPage).toHaveLength(10);
    expect(firstPage[0].title).toContain(`${prefix} 11`);
    expect(secondPage).toHaveLength(1);
    expect(secondPage[0].title).toContain(`${prefix} 01`);
  });

  test('updates task status from the table', async ({ page, request }) => {
    const token = await getAdminToken(request);
    const title = uniqueTaskTitle('Status');

    const created = await createTaskViaApi(request, token, { title });

    await page.reload();
    await waitForTasksWorkspace(page);
    await searchTasks(page, title);

    await updateTaskStatusViaUi(page, title, 'in_progress');

    await expectTaskStatus(page, title, 'in progress');

    const updated = await fetchTasksFromApi(request, token, { search: title });
    expect(updated).toHaveLength(1);
    expect(updated[0].id).toBe(created.id);
    expect(updated[0].status).toBe('in_progress');
  });
});
