import '@testing-library/jest-dom/vitest';
import { configure } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { restoreRealTimers } from './utils/async';

const storage = new Map<string, string>();

const localStorageMock = {
  getItem: (key: string) => (storage.has(key) ? storage.get(key)! : null),
  setItem: (key: string, value: string) => {
    storage.set(key, value);
  },
  removeItem: (key: string) => {
    storage.delete(key);
  },
  clear: () => {
    storage.clear();
  },
};

configure({
  asyncUtilTimeout: 3000,
});

vi.stubGlobal('localStorage', localStorageMock);

afterEach(() => {
  storage.clear();
  restoreRealTimers();
});
