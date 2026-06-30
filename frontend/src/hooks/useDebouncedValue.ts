import { useEffect, useState } from 'react';

export const SEARCH_DEBOUNCE_MS = 300;

export const useDebouncedValue = <T>(value: T, delayMs = SEARCH_DEBOUNCE_MS): T => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [value, delayMs]);

  return debouncedValue;
};
