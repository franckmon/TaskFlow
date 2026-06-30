import axios from 'axios';

export interface ApiErrorBody {
  detail?: string | Array<{ msg: string }>;
  code?: string;
}

const DEFAULT_MESSAGES: Record<number, string> = {
  400: 'The request could not be completed.',
  401: 'Please sign in to continue.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  422: 'Please check your input and try again.',
  500: 'Something went wrong. Please try again later.',
};

export class ApiClientError extends Error {
  readonly status?: number;
  readonly code?: string;

  constructor(message: string, originalError?: unknown) {
    super(message, { cause: originalError });
    this.name = 'ApiClientError';

    if (axios.isAxiosError(originalError)) {
      this.status = originalError.response?.status;
    }

    this.code = getApiErrorCode(originalError);
  }
}

export const normalizeApiError = (error: unknown): string => {
  if (!axios.isAxiosError(error)) {
    return 'An unexpected error occurred. Please try again.';
  }

  const body = error.response?.data as ApiErrorBody | undefined;

  if (body?.detail) {
    if (typeof body.detail === 'string') {
      return body.detail;
    }

    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return body.detail.map((item) => item.msg).join('. ');
    }
  }

  const status = error.response?.status;
  if (status && DEFAULT_MESSAGES[status]) {
    return DEFAULT_MESSAGES[status];
  }

  return 'An unexpected error occurred. Please try again.';
};

export const getApiErrorCode = (error: unknown): string | undefined => {
  if (!axios.isAxiosError(error)) {
    return undefined;
  }

  return (error.response?.data as ApiErrorBody | undefined)?.code;
};

export const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return normalizeApiError(error);
};

export const isUnauthorizedError = (error: unknown): boolean => {
  if (error instanceof ApiClientError) {
    return error.status === 401;
  }

  return axios.isAxiosError(error) && error.response?.status === 401;
};

export const isAbortError = (error: unknown): boolean => {
  if (axios.isCancel(error)) {
    return true;
  }

  if (error instanceof Error && error.cause !== undefined) {
    return isAbortError(error.cause);
  }

  return false;
};
