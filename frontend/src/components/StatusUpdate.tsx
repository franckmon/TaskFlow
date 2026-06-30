import React from 'react';
import { TaskStatus } from '../types';

interface StatusUpdateProps {
  currentStatus: TaskStatus;
  onStatusChange: (status: TaskStatus) => void;
  isUpdating?: boolean;
}

// UI lists every status; server enforces new → in_progress → done only.
export const StatusUpdate: React.FC<StatusUpdateProps> = ({
  currentStatus,
  onStatusChange,
  isUpdating = false,
}) => {
  return (
    <select
      className="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      value={currentStatus}
      onChange={(e) => onStatusChange(e.target.value as TaskStatus)}
      disabled={isUpdating}
    >
      <option value="new">New</option>
      <option value="in_progress">In Progress</option>
      <option value="done">Done</option>
    </select>
  );
};
