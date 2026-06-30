import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { StatusUpdate } from './StatusUpdate';

describe('StatusUpdate', () => {
  it('renders current status', () => {
    render(
      <StatusUpdate currentStatus="in_progress" onStatusChange={vi.fn()} />,
    );

    expect(screen.getByRole('combobox')).toHaveValue('in_progress');
  });

  it('calls onStatusChange when user selects a new status', async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();

    render(
      <StatusUpdate currentStatus="new" onStatusChange={onStatusChange} />,
    );

    await user.selectOptions(screen.getByRole('combobox'), 'done');

    expect(onStatusChange).toHaveBeenCalledWith('done');
  });

  it('disables select while updating', () => {
    render(
      <StatusUpdate
        currentStatus="new"
        onStatusChange={vi.fn()}
        isUpdating
      />,
    );

    expect(screen.getByRole('combobox')).toBeDisabled();
  });
});
