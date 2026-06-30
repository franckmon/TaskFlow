import React from 'react';
import { TaskCreate, TaskPriority } from '../types';

interface CreateFormProps {
  values: TaskCreate;
  onChange: (values: TaskCreate) => void;
  onSubmit: (event: React.FormEvent) => void;
  isSubmitting: boolean;
  error?: string | null;
}

export const CreateForm: React.FC<CreateFormProps> = ({
  values,
  onChange,
  onSubmit,
  isSubmitting,
  error,
}) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold mb-4">Create New Task</h3>
      {error && <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            type="text"
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={values.title}
            onChange={(e) => onChange({ ...values, title: e.target.value })}
            required
            disabled={isSubmitting}
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={values.description}
            onChange={(e) => onChange({ ...values, description: e.target.value })}
            rows={3}
            disabled={isSubmitting}
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <select
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={values.priority}
            onChange={(e) => onChange({ ...values, priority: e.target.value as TaskPriority })}
            disabled={isSubmitting}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition disabled:bg-gray-400"
        >
          {isSubmitting ? 'Creating...' : 'Create Task'}
        </button>
      </form>
    </div>
  );
};
