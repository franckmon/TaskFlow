import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { TaskTable } from './TaskTable';
import { sampleTask } from '../test/fixtures';

describe('TaskTable', () => {
  it('renders task rows', () => {
    render(
      <TaskTable
        tasks={[sampleTask({ title: 'Deploy release', description: 'Release notes' })]}
        onStatusChange={vi.fn()}
        onDelete={vi.fn()}
        isAdmin={false}
      />,
    );

    expect(screen.getByRole('columnheader', { name: /title/i })).toBeInTheDocument();
    expect(screen.getByText('Deploy release')).toBeInTheDocument();
    expect(screen.getByText('Release notes')).toBeInTheDocument();
    expect(screen.getByText('new')).toBeInTheDocument();
    expect(screen.getByText('normal')).toBeInTheDocument();
  });

  it('shows delete button only for admin users', () => {
    const { rerender } = render(
      <TaskTable
        tasks={[sampleTask()]}
        onStatusChange={vi.fn()}
        onDelete={vi.fn()}
        isAdmin={false}
      />,
    );

    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();

    rerender(
      <TaskTable
        tasks={[sampleTask()]}
        onStatusChange={vi.fn()}
        onDelete={vi.fn()}
        isAdmin
      />,
    );

    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  it('calls onStatusChange when status is updated', async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();

    render(
      <TaskTable
        tasks={[sampleTask({ id: 7, status: 'new' })]}
        onStatusChange={onStatusChange}
        onDelete={vi.fn()}
        isAdmin={false}
      />,
    );

    const row = screen.getByRole('row', { name: /sample task/i });
    await user.selectOptions(within(row).getByRole('combobox'), 'in_progress');

    expect(onStatusChange).toHaveBeenCalledWith(7, 'in_progress');
  });

  it('calls onDelete when admin confirms deletion', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <TaskTable
        tasks={[sampleTask({ id: 9 })]}
        onStatusChange={vi.fn()}
        onDelete={onDelete}
        isAdmin
      />,
    );

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(onDelete).toHaveBeenCalledWith(9);
  });
});
