import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { clearStoredToken } from '../api/auth';
import { subscribeAuthUnauthorized } from '../api/authEvents';
import { User } from '../types';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
}

export interface AuthContextValue extends AuthState {
  setIsAuthenticated: (value: boolean) => void;
  setUser: (value: User | null) => void;
  setIsLoading: (value: boolean) => void;
  resetAuthState: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const resetAuthState = useCallback(() => {
    clearStoredToken();
    setIsAuthenticated(false);
    setUser(null);
    setIsLoading(false);
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.history.replaceState(null, '', '/login');
    }
  }, []);

  useEffect(() => {
    return subscribeAuthUnauthorized(resetAuthState);
  }, [resetAuthState]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        isLoading,
        setIsAuthenticated,
        setUser,
        setIsLoading,
        resetAuthState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
