export type TaskStatus = 'new' | 'in_progress' | 'done';
export type TaskSortField = 'created_at' | 'priority';
export type SortOrder = 'asc' | 'desc';
export type TaskPriority = 'low' | 'normal' | 'high';

export const TASK_TITLE_MIN_LENGTH = 3;
export const TASK_TITLE_MAX_LENGTH = 120;
export const TASK_DESCRIPTION_MAX_LENGTH = 1000;

export type UserRole = 'admin' | 'user';

export interface User {
  username: string;
  role: UserRole;
}

export interface Task {
  id: number;
  /** 3–120 characters */
  title: string;
  /** max 1000 characters */
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: TaskPriority;
}

export interface TaskUpdate {
  /** 3–120 characters */
  title?: string;
  /** max 1000 characters */
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
}

export interface TaskSorting {
  sort_by: TaskSortField;
  sort_order: SortOrder;
}

export interface TaskFilters {
  status: TaskStatus | '';
  priority: TaskPriority | '';
  search: string;
}

export interface TaskPagination {
  skip: number;
  limit: number;
}

export interface TaskQueryParams {
  skip?: number;
  limit?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  sort_by?: TaskSortField;
  sort_order?: SortOrder;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
}
