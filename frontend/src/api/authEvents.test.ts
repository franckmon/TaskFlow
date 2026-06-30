import { describe, expect, it, vi } from 'vitest';
import axios from 'axios';
import {
  AUTH_UNAUTHORIZED_EVENT,
  emitAuthUnauthorized,
  isLoginRequest,
  shouldEmitAuthUnauthorized,
} from './authEvents';

describe('authEvents', () => {
  it('identifies login request errors', () => {
    const error = new axios.AxiosError(
      'Unauthorized',
      '401',
      { headers: {} } as never,
      {},
      { status: 401, data: {}, headers: {}, statusText: 'Unauthorized', config: {} as never },
    );
    error.config = { url: '/auth/login' } as never;

    expect(isLoginRequest(error)).toBe(true);
    expect(shouldEmitAuthUnauthorized(error)).toBe(false);
  });

  it('allows unauthorized event for protected endpoints', () => {
    const error = new axios.AxiosError(
      'Unauthorized',
      '401',
      { headers: {} } as never,
      {},
      { status: 401, data: {}, headers: {}, statusText: 'Unauthorized', config: {} as never },
    );
    error.config = { url: '/tasks/' } as never;

    expect(shouldEmitAuthUnauthorized(error)).toBe(true);
  });

  it('dispatches auth unauthorized event', () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, listener);

    emitAuthUnauthorized();

    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, listener);
  });
});
