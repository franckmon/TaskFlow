import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { Search } from './Search';

function SearchHarness({ onSearchChange = vi.fn() }: { onSearchChange?: (value: string) => void }) {
  const [search, setSearch] = useState('');

  return (
    <Search
      search={search}
      onSearchChange={(value) => {
        setSearch(value);
        onSearchChange(value);
      }}
    />
  );
}

describe('SearchBar', () => {
  it('renders search input', () => {
    render(<Search search="" onSearchChange={vi.fn()} />);

    expect(screen.getByPlaceholderText(/search tasks/i)).toBeInTheDocument();
  });

  it('shows current search value', () => {
    render(<Search search="billing" onSearchChange={vi.fn()} />);

    expect(screen.getByPlaceholderText(/search tasks/i)).toHaveValue('billing');
  });

  it('calls onSearchChange when user types', async () => {
    const user = userEvent.setup();
    const onSearchChange = vi.fn();

    render(<SearchHarness onSearchChange={onSearchChange} />);
    await user.type(screen.getByPlaceholderText(/search tasks/i), 'deploy');

    expect(onSearchChange).toHaveBeenCalled();
    expect(onSearchChange).toHaveBeenLastCalledWith('deploy');
    expect(screen.getByPlaceholderText(/search tasks/i)).toHaveValue('deploy');
  });
});
