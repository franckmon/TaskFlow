import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormEvent, useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { login } from '../api/auth';
import { LoginScreen } from './LoginScreen';
import { emptyLoginForm } from '../test/fixtures';
import { LoginRequest } from '../types';

vi.mock('../api/auth', () => ({
  login: vi.fn(),
}));

function LoginScreenWithApi() {
  const [values, setValues] = useState<LoginRequest>(emptyLoginForm());
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(values);
    } catch {
      setError('Incorrect username or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LoginScreen
      values={values}
      onChange={setValues}
      onSubmit={handleSubmit}
      error={error}
      isLoading={isLoading}
    />
  );
}

describe('LoginScreen', () => {
  it('renders login form', () => {
    render(
      <LoginScreen
        values={emptyLoginForm()}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        isLoading={false}
      />,
    );

    expect(screen.getByRole('heading', { name: /task flow login/i })).toBeInTheDocument();
    expect(screen.getAllByDisplayValue('')).toHaveLength(2);
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('shows login error message', () => {
    render(
      <LoginScreen
        values={emptyLoginForm()}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        isLoading={false}
        error="Incorrect username or password"
      />,
    );

    expect(screen.getByText('Incorrect username or password')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <LoginScreen
        values={{ username: 'admin', password: 'secret' }}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        isLoading
      />,
    );

    expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled();
  });

  it('submits credentials to login api', async () => {
    const user = userEvent.setup();
    const mockedLogin = vi.mocked(login);
    mockedLogin.mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      role: 'admin',
    });

    render(<LoginScreenWithApi />);

    const [usernameInput, passwordInput] = screen.getAllByDisplayValue('');
    await user.type(usernameInput, 'admin');
    await user.type(passwordInput, 'secret');
    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'secret',
      });
    });
  });

  it('shows api error after failed login', async () => {
    const user = userEvent.setup();
    vi.mocked(login).mockRejectedValue(new Error('Unauthorized'));

    render(<LoginScreenWithApi />);

    const [usernameInput, passwordInput] = screen.getAllByDisplayValue('');
    await user.type(usernameInput, 'admin');
    await user.type(passwordInput, 'wrong');
    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(await screen.findByText('Incorrect username or password')).toBeInTheDocument();
  });
});
