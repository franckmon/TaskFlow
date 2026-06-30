import api from './client';
import { Task, TaskCreate, TaskQueryParams, TaskUpdate } from '../types';

export type GetTasksOptions = {
  signal?: AbortSignal;
};

export const getTasks = async (
  params?: TaskQueryParams,
  options?: GetTasksOptions,
): Promise<Task[]> => {
  const response = await api.get<Task[]>('/tasks/', {
    params,
    signal: options?.signal,
  });
  return response.data;
};

export const getTask = async (id: number): Promise<Task> => {
  const response = await api.get<Task>(`/tasks/${id}`);
  return response.data;
};

export const createTask = async (data: TaskCreate): Promise<Task> => {
  const response = await api.post<Task>('/tasks/', data);
  return response.data;
};

export const updateTask = async (id: number, data: TaskUpdate): Promise<Task> => {
  const response = await api.put<Task>(`/tasks/${id}`, data);
  return response.data;
};

// Server allows delete only for admin users.
export const deleteTask = async (id: number): Promise<void> => {
  await api.delete(`/tasks/${id}`);
};
