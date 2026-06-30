import React from 'react';

export const RefreshIndicator: React.FC = () => (
  <div
    className="mb-3 flex items-center justify-end gap-2 text-sm text-gray-500"
    role="status"
    aria-live="polite"
  >
    <span
      className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
      aria-hidden="true"
    />
    Updating...
  </div>
);
