import { act, waitFor } from '@testing-library/react';
import { AxiosError, AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import { FormEvent } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearStoredToken,
  getMe,
  getStoredToken,
  login,
  storeToken,
} from '../api/auth';
import { ApiClientError } from '../api/client';
import { AuthSessionInitializer } from '../hooks/useAuth';
import { sampleUser } from '../test/fixtures';
import { renderUseAuth, renderWithAuth } from '../test/utils/renderWithAuth';

vi.mock('../api/auth', () => ({
  login: vi.fn(),
  getMe: vi.fn(),
  getStoredToken: vi.fn(),
  storeToken: vi.fn(),
  clearStoredToken: vi.fn(),
}));

const createUnauthorizedError = () =>
  new ApiClientError(
    'Unauthorized',
    new AxiosError(
      'Unauthorized',
      AxiosError.ERR_BAD_REQUEST,
      { headers: new AxiosHeaders() } as InternalAxiosRequestConfig,
      {},
      {
        status: 401,
        data: { detail: 'Unauthorized' },
        headers: {},
        statusText: 'Unauthorized',
        config: { headers: new AxiosHeaders() } as InternalAxiosRequestConfig,
      },
    ),
  );

const createSubmitEvent = () =>
  ({ preventDefault: vi.fn() }) as unknown as FormEvent;

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('exposes initial session loading state from auth context', () => {
    const { result } = renderUseAuth();

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('updates login form state', () => {
    const { result } = renderUseAuth();

    act(() => {
      result.current.setLoginValues({ username: 'admin', password: 'secret' });
    });

    expect(result.current.loginValues).toEqual({
      username: 'admin',
      password: 'secret',
    });
  });

  it('authenticates user after successful login', async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      role: 'admin',
    });
    vi.mocked(getMe).mockResolvedValue(sampleUser());

    const { result } = renderUseAuth();

    act(() => {
      result.current.setLoginValues({ username: 'admin', password: 'secret' });
    });

    await act(async () => {
      await result.current.handleLoginSubmit(createSubmitEvent());
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
    expect(storeToken).toHaveBeenCalledWith('token');
    expect(result.current.user).toEqual(sampleUser());
    expect(result.current.loginError).toBeNull();
    expect(result.current.isLoginLoading).toBe(false);
  });

  it('sets login error when login api fails', async () => {
    vi.mocked(login).mockRejectedValue(
      new ApiClientError('Incorrect username or password'),
    );

    const { result } = renderUseAuth();

    act(() => {
      result.current.setLoginValues({ username: 'admin', password: 'wrong' });
    });

    await act(async () => {
      await result.current.handleLoginSubmit(createSubmitEvent());
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.loginError).toBe('Incorrect username or password');
    expect(storeToken).not.toHaveBeenCalled();
    expect(result.current.isLoginLoading).toBe(false);
  });

  it('clears auth state when profile load fails after login', async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      role: 'admin',
    });
    vi.mocked(getMe).mockRejectedValue(new ApiClientError('User not found'));

    const { result } = renderUseAuth();

    act(() => {
      result.current.setLoginValues({ username: 'admin', password: 'secret' });
    });

    await act(async () => {
      await result.current.handleLoginSubmit(createSubmitEvent());
    });

    expect(clearStoredToken).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.loginError).toBe('User not found');
  });

  it('clears auth state on logout', async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      role: 'admin',
    });
    vi.mocked(getMe).mockResolvedValue(sampleUser());

    const { result } = renderUseAuth();

    act(() => {
      result.current.setLoginValues({ username: 'admin', password: 'secret' });
    });

    await act(async () => {
      await result.current.handleLoginSubmit(createSubmitEvent());
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    act(() => {
      result.current.logout();
    });

    expect(clearStoredToken).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});

describe('AuthSessionInitializer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('finishes loading when no stored token exists', async () => {
    vi.mocked(getStoredToken).mockReturnValue(null);

    renderWithAuth(<AuthSessionInitializer />);

    await waitFor(() => {
      expect(getMe).not.toHaveBeenCalled();
    });
  });

  it('restores authenticated session from stored token', async () => {
    vi.mocked(getStoredToken).mockReturnValue('stored-token');
    vi.mocked(getMe).mockResolvedValue(sampleUser());

    renderWithAuth(<AuthSessionInitializer />);

    await waitFor(() => {
      expect(getMe).toHaveBeenCalled();
    });
  });

  it('clears stored auth when profile restore is unauthorized', async () => {
    vi.mocked(getStoredToken).mockReturnValue('stored-token');
    vi.mocked(getMe).mockRejectedValue(createUnauthorizedError());

    renderWithAuth(<AuthSessionInitializer />);

    await waitFor(() => {
      expect(clearStoredToken).toHaveBeenCalled();
    });
  });
});
