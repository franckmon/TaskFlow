import { act, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { storeToken } from '../api/auth';
import { emitAuthUnauthorized } from '../api/authEvents';
import { renderWithAuth } from '../test/utils/renderWithAuth';
import { useAuthContext } from './AuthContext';

const AuthProbe = () => {
  const { isAuthenticated, user, isLoading } = useAuthContext();

  return (
    <div>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="user">{user?.username ?? 'none'}</span>
    </div>
  );
};

describe('AuthProvider', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('resets auth state and redirects to login when auth unauthorized event is emitted', async () => {
    const replaceState = vi.spyOn(window.history, 'replaceState');

    act(() => {
      storeToken('stored-token');
    });

    renderWithAuth(<AuthProbe />);

    act(() => {
      emitAuthUnauthorized();
    });

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBeNull();
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user')).toHaveTextContent('none');
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(replaceState).toHaveBeenCalledWith(null, '', '/login');
    });
  });
});
