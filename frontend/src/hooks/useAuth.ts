import { useCallback, useEffect, useState } from 'react';
import { getMe, getStoredToken, login, storeToken } from '../api/auth';
import { getErrorMessage, isUnauthorizedError } from '../api/client';
import { useAuthContext } from '../contexts/AuthContext';
import { LoginRequest } from '../types';

const INITIAL_LOGIN_FORM: LoginRequest = {
  username: '',
  password: '',
};

export const AuthSessionInitializer = () => {
  const { setIsAuthenticated, setUser, setIsLoading, resetAuthState } = useAuthContext();

  const restoreSession = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await getMe();
      setUser(currentUser);
      setIsAuthenticated(true);
    } catch (error) {
      if (isUnauthorizedError(error)) {
        resetAuthState();
        return;
      }
    } finally {
      setIsLoading(false);
    }
  }, [resetAuthState, setIsAuthenticated, setIsLoading, setUser]);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  return null;
};

export const useAuth = () => {
  const {
    isAuthenticated,
    user,
    isLoading,
    setIsAuthenticated,
    setUser,
    resetAuthState,
  } = useAuthContext();

  const [loginValues, setLoginValues] = useState<LoginRequest>(INITIAL_LOGIN_FORM);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoginLoading, setIsLoginLoading] = useState(false);

  const handleLogin = useCallback(async (data: LoginRequest): Promise<string | null> => {
    try {
      const response = await login(data);
      storeToken(response.access_token);

      try {
        // Session role comes from /auth/me, not the login response payload.
        const currentUser = await getMe();
        setUser(currentUser);
        setIsAuthenticated(true);
        return null;
      } catch (error) {
        resetAuthState();
        return getErrorMessage(error);
      }
    } catch (error) {
      return getErrorMessage(error);
    }
  }, [resetAuthState, setIsAuthenticated, setUser]);

  const handleLogout = useCallback(() => {
    resetAuthState();
  }, [resetAuthState]);

  const handleLoginSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    setLoginError(null);
    setIsLoginLoading(true);

    const error = await handleLogin(loginValues);
    if (error) {
      setLoginError(error);
    }

    setIsLoginLoading(false);
  }, [handleLogin, loginValues]);

  return {
    isAuthenticated,
    user,
    isLoading,
    logout: handleLogout,
    loginValues,
    setLoginValues,
    loginError,
    isLoginLoading,
    handleLoginSubmit,
  };
};
