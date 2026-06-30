import React from 'react';
import { SortOrder, TaskSortField } from '../types';

interface SortControlsProps {
  sortBy: TaskSortField;
  sortOrder: SortOrder;
  onSortByChange: (sortBy: TaskSortField) => void;
  onSortOrderChange: (sortOrder: SortOrder) => void;
}

export const SortControls: React.FC<SortControlsProps> = ({
  sortBy,
  sortOrder,
  onSortByChange,
  onSortOrderChange,
}) => {
  return (
    <div className="flex gap-4">
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">Sort by</label>
        <select
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value as TaskSortField)}
        >
          <option value="created_at">Created At</option>
          <option value="priority">Priority</option>
        </select>
      </div>
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">Order</label>
        <select
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={sortOrder}
          onChange={(e) => onSortOrderChange(e.target.value as SortOrder)}
        >
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>
    </div>
  );
};
