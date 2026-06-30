import React from 'react';

interface TaskPaginationProps {
  currentPage: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export const TaskPagination: React.FC<TaskPaginationProps> = ({
  currentPage,
  canGoPrevious,
  canGoNext,
  onPrevious,
  onNext,
}) => (
  <div className="flex items-center justify-between mt-6">
    <button
      onClick={onPrevious}
      disabled={!canGoPrevious}
      className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50"
    >
      Previous
    </button>
    <span className="text-gray-600">Page {currentPage}</span>
    <button
      onClick={onNext}
      disabled={!canGoNext}
      className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50"
    >
      Next
    </button>
  </div>
);
