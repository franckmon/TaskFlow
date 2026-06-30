import axios from 'axios';
import { emitAuthUnauthorized, shouldEmitAuthUnauthorized } from './authEvents';
import { ApiClientError, getErrorMessage, isAbortError, isUnauthorizedError, normalizeApiError } from './errors';

const API_BASE_URL = import.meta.env.VITE_API_URL?.trim();

if (!API_BASE_URL) {
  throw new Error(
    'VITE_API_URL is required. Copy frontend/.env.example to frontend/.env and set the API base URL.',
  );
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (shouldEmitAuthUnauthorized(error)) {
      emitAuthUnauthorized();
    }

    return Promise.reject(new ApiClientError(normalizeApiError(error), error));
  },
);

export default api;

export { ApiClientError, getErrorMessage, isAbortError, isUnauthorizedError };
