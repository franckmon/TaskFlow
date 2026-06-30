import { act } from '@testing-library/react';
import { vi } from 'vitest';
import { SEARCH_DEBOUNCE_MS } from '../../hooks/useDebouncedValue';

export async function resolveDeferred<T>(resolver: (value: T) => void, value: T) {
  await act(async () => {
    resolver(value);
  });
}

export async function advanceTimers(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

export async function advanceDebounce(delayMs = SEARCH_DEBOUNCE_MS): Promise<void> {
  await advanceTimers(delayMs);
}

export async function runPendingTimers(): Promise<void> {
  await act(async () => {
    await vi.runAllTimersAsync();
  });
}

export function enableFakeTimers(): void {
  vi.useFakeTimers();
}

export function restoreRealTimers(): void {
  vi.useRealTimers();
}

export async function withFakeTimers<T>(run: () => Promise<T> | T): Promise<T> {
  enableFakeTimers();
  try {
    return await run();
  } finally {
    restoreRealTimers();
  }
}
