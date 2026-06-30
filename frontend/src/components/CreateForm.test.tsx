import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormEvent, useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { CreateForm } from './CreateForm';
import { emptyCreateForm } from '../test/fixtures';
import { TaskCreate } from '../types';

function CreateFormHarness({
  initialValues = emptyCreateForm(),
  onSubmit = vi.fn((event) => event.preventDefault()),
  isSubmitting = false,
  error = null,
}: {
  initialValues?: TaskCreate;
  onSubmit?: (event: FormEvent) => void;
  isSubmitting?: boolean;
  error?: string | null;
}) {
  const [values, setValues] = useState(initialValues);

  return (
    <CreateForm
      values={values}
      onChange={setValues}
      onSubmit={onSubmit}
      isSubmitting={isSubmitting}
      error={error}
    />
  );
}

describe('CreateForm', () => {
  it('renders create task form fields', () => {
    render(<CreateFormHarness />);

    expect(screen.getByRole('heading', { name: /create new task/i })).toBeInTheDocument();
    expect(screen.getAllByRole('textbox')).toHaveLength(2);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create task/i })).toBeInTheDocument();
  });

  it('shows validation error message', () => {
    render(<CreateFormHarness error="Title is required" />);

    expect(screen.getByText('Title is required')).toBeInTheDocument();
  });

  it('shows submitting state', () => {
    render(
      <CreateFormHarness
        initialValues={{ title: 'New task', description: '', priority: 'normal' }}
        isSubmitting
      />,
    );

    expect(screen.getByRole('button', { name: /creating/i })).toBeDisabled();
    expect(screen.getAllByRole('textbox')[0]).toBeDisabled();
  });

  it('updates values when user types', async () => {
    const user = userEvent.setup();

    render(<CreateFormHarness />);

    const [titleInput] = screen.getAllByRole('textbox');
    await user.type(titleInput, 'Deploy');

    expect(titleInput).toHaveValue('Deploy');
  });

  it('submits the form', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn((event) => event.preventDefault());

    render(
      <CreateFormHarness
        initialValues={{ title: 'New task', description: 'Details', priority: 'high' }}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole('button', { name: /create task/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
