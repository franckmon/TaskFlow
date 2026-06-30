import axios from 'axios';

export const AUTH_UNAUTHORIZED_EVENT = 'auth:unauthorized';

const LOGIN_PATH = '/auth/login';

export const emitAuthUnauthorized = (): void => {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT));
};

export const subscribeAuthUnauthorized = (listener: () => void): (() => void) => {
  window.addEventListener(AUTH_UNAUTHORIZED_EVENT, listener);
  return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, listener);
};

export const isLoginRequest = (error: unknown): boolean => {
  if (!axios.isAxiosError(error)) {
    return false;
  }

  const requestUrl = error.config?.url ?? '';
  return requestUrl.includes(LOGIN_PATH);
};

export const shouldEmitAuthUnauthorized = (error: unknown): boolean => {
  return (
    axios.isAxiosError(error) &&
    error.response?.status === 401 &&
    !isLoginRequest(error)
  );
};
