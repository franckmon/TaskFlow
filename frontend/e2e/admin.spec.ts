import { expect, test } from '@playwright/test';
import {
  expectAuthenticatedWorkspace,
  getSessionToken,
  loginAsAdmin,
  loginAsRegularUser,
} from './helpers/auth';
import {
  createTaskViaApi,
  deleteTaskViaApi,
  fetchTaskByIdViaApi,
  fetchTasksFromApi,
  getAdminToken,
} from './helpers/api';
import {
  createTaskViaUi,
  deleteTaskViaUi,
  expectDeleteButtonHidden,
  expectDeleteButtonVisible,
  expectTaskStatus,
  expectTaskVisible,
  searchTasks,
  uniqueTaskTitle,
  updateTaskStatusViaUi,
  waitForTasksWorkspace,
} from './helpers/tasks';

test.describe.configure({ mode: 'serial' });

test.describe('Admin functionality', () => {
  test('admin login exposes task deletion controls', async ({ page }) => {
    await loginAsAdmin(page);
    await expectAuthenticatedWorkspace(page);

    const title = uniqueTaskTitle('AdminLogin');
    await createTaskViaUi(page, { title });

    await expectDeleteButtonVisible(page, title);
  });

  test('admin deletes a task through the UI', async ({ page, request }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    const title = uniqueTaskTitle('Delete');
    await createTaskViaUi(page, { title });
    await expectDeleteButtonVisible(page, title);

    await deleteTaskViaUi(page, title);

    const token = await getAdminToken(request);
    const tasks = await fetchTasksFromApi(request, token, { search: title });
    expect(tasks).toHaveLength(0);
  });

  test('non-admin cannot delete tasks', async ({ page, request }) => {
    const adminToken = await getAdminToken(request);
    const title = uniqueTaskTitle('Protected');
    const task = await createTaskViaApi(request, adminToken, { title });

    await loginAsRegularUser(page);
    await waitForTasksWorkspace(page);
    await searchTasks(page, title);

    await expectTaskVisible(page, title);
    await expectDeleteButtonHidden(page, title);

    const userToken = await getSessionToken(page);
    const deleteResponse = await deleteTaskViaApi(request, userToken, task.id);

    expect(deleteResponse.status()).toBe(403);
    await expect(deleteResponse.json()).resolves.toEqual({
      detail: 'Only admin users can delete tasks',
      code: 'permission_denied',
    });

    const stillThere = await fetchTasksFromApi(request, adminToken, { search: title });
    expect(stillThere).toHaveLength(1);
    expect(stillThere[0].id).toBe(task.id);
  });

  test('admin can delete a completed task', async ({ page, request }) => {
    await loginAsAdmin(page);
    await waitForTasksWorkspace(page);

    const title = uniqueTaskTitle('CompletedDelete');
    await createTaskViaUi(page, { title });
    await updateTaskStatusViaUi(page, title, 'in_progress');
    await updateTaskStatusViaUi(page, title, 'done');
    await expectTaskStatus(page, title, 'done');

    const token = await getAdminToken(request);
    const [task] = await fetchTasksFromApi(request, token, { search: title });
    expect(task).toBeDefined();

    await deleteTaskViaUi(page, title);

    const tasks = await fetchTasksFromApi(request, token, { search: title });
    expect(tasks).toHaveLength(0);

    const getResponse = await fetchTaskByIdViaApi(request, token, task.id);
    expect(getResponse.status()).toBe(404);
  });
});
