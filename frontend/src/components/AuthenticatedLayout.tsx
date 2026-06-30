import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { AppLayout } from './AppLayout';

interface AuthenticatedLayoutProps {
  children: React.ReactNode;
}

export const AuthenticatedLayout: React.FC<AuthenticatedLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <AppLayout username={user?.username} onLogout={logout}>
      {children}
    </AppLayout>
  );
};
