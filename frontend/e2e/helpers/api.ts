import { APIRequestContext, expect } from '@playwright/test';

const API_BASE_URL = process.env.E2E_API_URL?.trim();

if (!API_BASE_URL) {
  throw new Error(
    'E2E_API_URL is required for Playwright API helpers. Set it in the Playwright webServer env.',
  );
}

export interface ApiTask {
  id: number;
  title: string;
  description: string | null;
  status: 'new' | 'in_progress' | 'done';
  priority: 'low' | 'normal' | 'high';
  created_at: string;
  updated_at: string;
}

export async function getAdminToken(request: APIRequestContext) {
  const response = await request.post(`${API_BASE_URL}/auth/login`, {
    data: { username: 'admin', password: 'admin' },
  });

  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  return body.access_token as string;
}

export async function fetchTasksFromApi(
  request: APIRequestContext,
  token: string,
  params: Record<string, string | number> = {},
): Promise<ApiTask[]> {
  const response = await request.get(`${API_BASE_URL}/tasks/`, {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });

  expect(response.ok()).toBeTruthy();
  return response.json();
}

export async function createTaskViaApi(
  request: APIRequestContext,
  token: string,
  task: {
    title: string;
    description?: string;
    status?: ApiTask['status'];
    priority?: ApiTask['priority'];
  },
): Promise<ApiTask> {
  const response = await request.post(`${API_BASE_URL}/tasks/`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      title: task.title,
      description: task.description ?? '',
      status: task.status ?? 'new',
      priority: task.priority ?? 'normal',
    },
  });

  expect(response.ok()).toBeTruthy();
  return response.json();
}

export async function updateTaskViaApi(
  request: APIRequestContext,
  token: string,
  taskId: number,
  data: Partial<Pick<ApiTask, 'status' | 'priority' | 'title' | 'description'>>,
): Promise<ApiTask> {
  const response = await request.put(`${API_BASE_URL}/tasks/${taskId}`, {
    headers: { Authorization: `Bearer ${token}` },
    data,
  });

  expect(response.ok()).toBeTruthy();
  return response.json();
}

export async function deleteTaskViaApi(
  request: APIRequestContext,
  token: string,
  taskId: number,
) {
  return request.delete(`${API_BASE_URL}/tasks/${taskId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchTaskByIdViaApi(
  request: APIRequestContext,
  token: string,
  taskId: number,
) {
  return request.get(`${API_BASE_URL}/tasks/${taskId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
