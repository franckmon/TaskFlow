import { AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import api from './client';
import {
  clearStoredToken,
  getMe,
  getStoredToken,
  login,
  logout,
  storeToken,
} from './auth';

const axiosResponse = (data: unknown) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: new AxiosHeaders(),
  config: { headers: new AxiosHeaders() } as InternalAxiosRequestConfig,
});

describe('auth api', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('logs in and returns token payload', async () => {
    vi.spyOn(api, 'post').mockResolvedValue(
      axiosResponse({
        access_token: 'token',
        token_type: 'bearer',
        role: 'admin',
      }),
    );

    await expect(login({ username: 'admin', password: 'secret' })).resolves.toEqual({
      access_token: 'token',
      token_type: 'bearer',
      role: 'admin',
    });
  });

  it('loads current user profile', async () => {
    vi.spyOn(api, 'get').mockResolvedValue(
      axiosResponse({ username: 'admin', role: 'admin' }),
    );

    await expect(getMe()).resolves.toEqual({ username: 'admin', role: 'admin' });
  });

  it('stores and clears auth token in localStorage', () => {
    storeToken('token');
    expect(getStoredToken()).toBe('token');

    logout();
    expect(getStoredToken()).toBeNull();
    expect(localStorage.getItem('username')).toBeNull();

    clearStoredToken();
    expect(getStoredToken()).toBeNull();
  });
});
