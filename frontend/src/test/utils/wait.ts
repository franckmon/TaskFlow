import { screen, waitFor } from '@testing-library/react';

export async function waitForLoginScreen() {
  await screen.findByRole('heading', { name: /task flow login/i });
}

export async function waitForAuthenticatedWorkspace(username = 'admin') {
  await screen.findByText(new RegExp(`welcome, ${username}`, 'i'));
}

export async function waitForTasksLoaded() {
  await waitFor(() => {
    expect(screen.queryByText('Loading tasks...')).toBeNull();
  });
}

export async function waitForText(text: string | RegExp) {
  await screen.findByText(text);
}
