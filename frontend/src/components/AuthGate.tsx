import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { LoginScreen } from './LoginScreen';
import { LoadingScreen } from './LoadingScreen';

interface AuthGateProps {
  children: React.ReactNode;
}

export const AuthGate: React.FC<AuthGateProps> = ({ children }) => {
  const {
    isAuthenticated,
    isLoading,
    loginValues,
    setLoginValues,
    loginError,
    isLoginLoading,
    handleLoginSubmit,
  } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <LoginScreen
        values={loginValues}
        onChange={setLoginValues}
        onSubmit={handleLoginSubmit}
        error={loginError}
        isLoading={isLoginLoading}
      />
    );
  }

  return <>{children}</>;
};
