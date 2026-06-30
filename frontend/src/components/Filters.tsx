import React from 'react';
import { TaskStatus, TaskPriority } from '../types';

interface FiltersProps {
  status: TaskStatus | '';
  priority: TaskPriority | '';
  onStatusChange: (status: TaskStatus | '') => void;
  onPriorityChange: (priority: TaskPriority | '') => void;
}

export const Filters: React.FC<FiltersProps> = ({ status, priority, onStatusChange, onPriorityChange }) => {
  return (
    <div className="flex gap-4 mb-4">
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
        <select
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={status}
          onChange={(e) => onStatusChange(e.target.value as TaskStatus | '')}
        >
          <option value="">All</option>
          <option value="new">New</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
      </div>
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
        <select
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={priority}
          onChange={(e) => onPriorityChange(e.target.value as TaskPriority | '')}
        >
          <option value="">All</option>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
  );
};
