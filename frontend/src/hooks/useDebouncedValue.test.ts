import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { advanceDebounce, advanceTimers, enableFakeTimers, restoreRealTimers } from '../test/utils/async';
import { SEARCH_DEBOUNCE_MS, useDebouncedValue } from './useDebouncedValue';

describe('useDebouncedValue', () => {
  beforeEach(() => {
    enableFakeTimers();
  });

  afterEach(() => {
    restoreRealTimers();
  });

  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebouncedValue('initial'));

    expect(result.current).toBe('initial');
  });

  it('updates after the default debounce delay', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value),
      { initialProps: { value: 'first' } },
    );

    act(() => {
      rerender({ value: 'second' });
    });

    expect(result.current).toBe('first');

    await advanceDebounce(SEARCH_DEBOUNCE_MS);

    expect(result.current).toBe('second');
  });

  it('cancels pending updates when the value changes again', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value),
      { initialProps: { value: '' } },
    );

    act(() => {
      rerender({ value: 'bi' });
    });

    await advanceTimers(100);

    act(() => {
      rerender({ value: 'billing' });
    });

    await advanceDebounce(SEARCH_DEBOUNCE_MS);

    expect(result.current).toBe('billing');
  });

  it('supports a custom delay', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 500),
      { initialProps: { value: 'first' } },
    );

    act(() => {
      rerender({ value: 'second' });
    });

    await advanceTimers(300);
    expect(result.current).toBe('first');

    await advanceTimers(200);
    expect(result.current).toBe('second');
  });
});
