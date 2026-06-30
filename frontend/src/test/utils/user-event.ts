import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

export function createUser() {
  return userEvent.setup();
}

export function createUserWithFakeTimers() {
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}
