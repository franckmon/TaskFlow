import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { DeleteButton } from './DeleteButton';

describe('DeleteButton', () => {
  it('renders delete button', () => {
    render(<DeleteButton onDelete={vi.fn()} />);

    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  it('calls onDelete when deletion is confirmed', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<DeleteButton onDelete={onDelete} />);
    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('does not call onDelete when deletion is cancelled', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(<DeleteButton onDelete={onDelete} />);
    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(onDelete).not.toHaveBeenCalled();
  });

  it('shows deleting state', () => {
    render(<DeleteButton onDelete={vi.fn()} isDeleting />);

    expect(screen.getByRole('button', { name: /deleting/i })).toBeDisabled();
  });
});
