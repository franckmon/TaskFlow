import React from 'react';
import { LoginForm } from './LoginForm';
import { LoginRequest } from '../types';

interface LoginScreenProps {
  values: LoginRequest;
  onChange: (values: LoginRequest) => void;
  onSubmit: (event: React.FormEvent) => void;
  error?: string | null;
  isLoading: boolean;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  values,
  onChange,
  onSubmit,
  error,
  isLoading,
}) => {
  return (
    <LoginForm
      values={values}
      onChange={onChange}
      onSubmit={onSubmit}
      error={error}
      isLoading={isLoading}
    />
  );
};
