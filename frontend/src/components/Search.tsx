import React from 'react';

interface SearchProps {
  search: string;
  onSearchChange: (search: string) => void;
}

export const Search: React.FC<SearchProps> = ({ search, onSearchChange }) => {
  return (
    <div className="mb-4">
      <input
        type="text"
        placeholder="Search tasks..."
        className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
      />
    </div>
  );
};
