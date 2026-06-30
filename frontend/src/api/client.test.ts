import { AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AUTH_UNAUTHORIZED_EVENT } from './authEvents';
import api from './client';

describe('api client', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    localStorage.clear();
    mock = new MockAdapter(api);
  });

  afterEach(() => {
    mock.restore();
  });

  it('adds bearer token to outgoing requests when token is stored', async () => {
    localStorage.setItem('token', 'stored-token');
    mock.onGet('/protected').reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer stored-token');
      return [200, {}];
    });

    await api.get('/protected');
  });

  it('rejects failed responses as ApiClientError', async () => {
    mock.onGet('/tasks').reply(401, { detail: 'Unauthorized' });

    await expect(api.get('/tasks')).rejects.toMatchObject({
      name: 'ApiClientError',
      message: 'Unauthorized',
      status: 401,
    });
  });

  it('emits auth unauthorized event for 401 responses except login', async () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, listener);

    mock.onGet('/tasks/').reply(401, { detail: 'Unauthorized' });

    await expect(api.get('/tasks/')).rejects.toBeDefined();
    expect(listener).toHaveBeenCalledTimes(1);

    window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, listener);
  });

  it('does not emit auth unauthorized event for failed login', async () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, listener);

    mock.onPost('/auth/login').reply(401, {
      detail: 'Incorrect username or password',
      code: 'invalid_credentials',
    });

    await expect(
      api.post('/auth/login', { username: 'admin', password: 'wrong-password' }),
    ).rejects.toBeDefined();
    expect(listener).not.toHaveBeenCalled();

    window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, listener);
  });

  it('throws when VITE_API_URL is missing', async () => {
    vi.stubEnv('VITE_API_URL', '');
    vi.resetModules();

    await expect(import('./client')).rejects.toThrow('VITE_API_URL is required');
  });
});
