import axios, { AxiosError, AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import { describe, expect, it } from 'vitest';
import {
  ApiClientError,
  getApiErrorCode,
  getErrorMessage,
  isAbortError,
  isUnauthorizedError,
  normalizeApiError,
} from './errors';

const createAxiosError = (
  status: number,
  data: unknown,
  code = AxiosError.ERR_BAD_REQUEST,
): AxiosError => {
  const config = { headers: new AxiosHeaders() } as InternalAxiosRequestConfig;

  return new AxiosError('Request failed', code, config, {}, {
    status,
    data,
    headers: {},
    statusText: 'Error',
    config,
  });
};

describe('ApiClientError', () => {
  it('stores status and code from axios errors', () => {
    const error = new ApiClientError(
      'Forbidden',
      createAxiosError(403, { code: 'forbidden', detail: 'Forbidden' }),
    );

    expect(error.name).toBe('ApiClientError');
    expect(error.message).toBe('Forbidden');
    expect(error.status).toBe(403);
    expect(error.code).toBe('forbidden');
  });
});

describe('normalizeApiError', () => {
  it('returns fallback message for non-axios errors', () => {
    expect(normalizeApiError(new Error('boom'))).toBe(
      'An unexpected error occurred. Please try again.',
    );
  });

  it('returns string detail from api response', () => {
    const error = createAxiosError(400, { detail: 'Invalid task data' });

    expect(normalizeApiError(error)).toBe('Invalid task data');
  });

  it('joins validation error messages from detail array', () => {
    const error = createAxiosError(422, {
      detail: [{ msg: 'title is required' }, { msg: 'priority is invalid' }],
    });

    expect(normalizeApiError(error)).toBe('title is required. priority is invalid');
  });

  it('uses default message for known http status codes', () => {
    const error = createAxiosError(404, {});

    expect(normalizeApiError(error)).toBe('The requested resource was not found.');
  });

  it('falls back when axios error has no response body', () => {
    const config = { headers: new AxiosHeaders() } as InternalAxiosRequestConfig;
    const error = new AxiosError('Network error', AxiosError.ERR_NETWORK, config);

    expect(normalizeApiError(error)).toBe('An unexpected error occurred. Please try again.');
  });
});

describe('getApiErrorCode', () => {
  it('returns undefined for non-axios errors', () => {
    expect(getApiErrorCode(new Error('boom'))).toBeUndefined();
  });

  it('returns code from response body', () => {
    const error = createAxiosError(401, { code: 'unauthorized' });

    expect(getApiErrorCode(error)).toBe('unauthorized');
  });
});

describe('getErrorMessage', () => {
  it('returns message from ApiClientError instances', () => {
    expect(getErrorMessage(new ApiClientError('Task not found'))).toBe('Task not found');
  });

  it('normalizes unknown errors', () => {
    expect(getErrorMessage(createAxiosError(500, {}))).toBe(
      'Something went wrong. Please try again later.',
    );
  });
});

describe('isUnauthorizedError', () => {
  it('detects unauthorized ApiClientError instances', () => {
    const error = new ApiClientError(
      'Unauthorized',
      createAxiosError(401, { code: 'unauthorized' }),
    );

    expect(isUnauthorizedError(error)).toBe(true);
  });

  it('detects unauthorized axios errors', () => {
    expect(isUnauthorizedError(createAxiosError(401, {}))).toBe(true);
  });

  it('returns false for other errors', () => {
    expect(isUnauthorizedError(new ApiClientError('Forbidden'))).toBe(false);
    expect(isUnauthorizedError(createAxiosError(403, {}))).toBe(false);
    expect(isUnauthorizedError(new Error('boom'))).toBe(false);
  });
});

describe('isAbortError', () => {
  it('detects axios cancel errors', () => {
    const cancelError = new axios.CanceledError('canceled');

    expect(isAbortError(cancelError)).toBe(true);
  });

  it('detects abort errors wrapped in ApiClientError', () => {
    const cancelError = new axios.CanceledError('canceled');
    const error = new ApiClientError('Request canceled', cancelError);

    expect(isAbortError(error)).toBe(true);
  });

  it('returns false for other errors', () => {
    expect(isAbortError(new ApiClientError('Failed to load tasks'))).toBe(false);
    expect(isAbortError(createAxiosError(500, {}))).toBe(false);
    expect(isAbortError(new Error('boom'))).toBe(false);
  });
});
