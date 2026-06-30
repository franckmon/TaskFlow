import React from 'react';

interface DeleteButtonProps {
  onDelete: () => void;
  isDeleting?: boolean;
}

export const DeleteButton: React.FC<DeleteButtonProps> = ({ onDelete, isDeleting = false }) => {
  const handleDelete = () => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    onDelete();
  };

  return (
    <button
      onClick={handleDelete}
      disabled={isDeleting}
      className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition disabled:bg-gray-400"
    >
      {isDeleting ? 'Deleting...' : 'Delete'}
    </button>
  );
};
