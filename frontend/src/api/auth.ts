import api from './client';
import { LoginRequest, TokenResponse, User } from '../types';

export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/auth/login', data);
  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await api.get<User>('/auth/me');
  return response.data;
};

export const clearStoredToken = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('username'); // legacy key; not written by current login flow
};

export const storeToken = (token: string) => {
  localStorage.setItem('token', token);
};

export const getStoredToken = (): string | null => {
  return localStorage.getItem('token');
};

export const logout = () => {
  clearStoredToken();
};
