import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Filters } from './Filters';

describe('Filters', () => {
  it('renders status and priority filters', () => {
    render(
      <Filters
        status=""
        priority=""
        onStatusChange={vi.fn()}
        onPriorityChange={vi.fn()}
      />,
    );

    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Priority')).toBeInTheDocument();
    expect(screen.getAllByRole('combobox')).toHaveLength(2);
  });

  it('calls onStatusChange when status filter changes', async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();

    render(
      <Filters
        status=""
        priority=""
        onStatusChange={onStatusChange}
        onPriorityChange={vi.fn()}
      />,
    );

    const [statusSelect, prioritySelect] = screen.getAllByRole('combobox');

    await user.selectOptions(statusSelect, 'done');

    expect(onStatusChange).toHaveBeenCalledWith('done');
  });

  it('calls onPriorityChange when priority filter changes', async () => {
    const user = userEvent.setup();
    const onPriorityChange = vi.fn();

    render(
      <Filters
        status=""
        priority=""
        onStatusChange={vi.fn()}
        onPriorityChange={onPriorityChange}
      />,
    );

    const [, prioritySelect] = screen.getAllByRole('combobox');

    await user.selectOptions(prioritySelect, 'high');

    expect(onPriorityChange).toHaveBeenCalledWith('high');
  });
});
