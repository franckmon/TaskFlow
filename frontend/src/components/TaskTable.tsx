import React from 'react';
import { Task, TaskStatus, TaskPriority } from '../types';
import { StatusUpdate } from './StatusUpdate';
import { DeleteButton } from './DeleteButton';

interface TaskTableProps {
  tasks: Task[];
  onStatusChange: (id: number, status: TaskStatus) => void;
  onDelete: (id: number) => void;
  isAdmin: boolean;
  updatingTaskId?: number | null;
  deletingTaskId?: number | null;
}

const statusColors: Record<TaskStatus, string> = {
  new: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  done: 'bg-green-100 text-green-800',
};

const priorityColors: Record<TaskPriority, string> = {
  low: 'bg-gray-200 text-gray-700',
  normal: 'bg-yellow-200 text-yellow-800',
  high: 'bg-red-200 text-red-800',
};

export const TaskTable: React.FC<TaskTableProps> = ({
  tasks,
  onStatusChange,
  onDelete,
  isAdmin,
  updatingTaskId = null,
  deletingTaskId = null,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead>
          <tr className="bg-gray-50">
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {tasks.map((task) => (
            <tr key={task.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{task.title}</td>
              <td className="px-6 py-4 whitespace-nowrap text-gray-500">{task.description || '-'}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[task.status]}`}>
                  {task.status.replace('_', ' ')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[task.priority]}`}>
                  {task.priority}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">
                {new Date(task.created_at).toLocaleDateString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex gap-2">
                  <StatusUpdate
                    currentStatus={task.status}
                    onStatusChange={(status) => onStatusChange(task.id, status)}
                    isUpdating={updatingTaskId === task.id}
                  />
                  {isAdmin && (
                    <DeleteButton
                      onDelete={() => onDelete(task.id)}
                      isDeleting={deletingTaskId === task.id}
                    />
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
