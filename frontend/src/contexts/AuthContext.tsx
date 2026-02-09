import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, LoginRequest } from '../types/auth';
import { authAPI } from '../api/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  signUp: (credentials: LoginRequest) => Promise<any>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for Supabase auth callback in URL hash
    const hash = window.location.hash;
    if (hash && hash.includes('access_token')) {
      const params = new URLSearchParams(hash.substring(1)); // Remove the #
      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');

      if (accessToken) {
        setToken(accessToken);
        localStorage.setItem('access_token', accessToken);
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }

        // Fetch user profile if needed, or just set a basic user object
        // For now, we'll set a placeholder since we have a valid token
        setUser({ id: 'confirmed-user', email: 'confirmed@example.com', created_at: new Date().toISOString() });

        // Clean up the URL
        window.history.replaceState(null, '', window.location.pathname);
        setIsLoading(false);
        return;
      }
    }

    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      setToken(savedToken);
      // TODO: Validate token and get user info
    }
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authAPI.login(credentials);
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const signUp = async (credentials: LoginRequest) => {
    try {
      const response = await authAPI.signup(credentials);
      console.log('Signup response:', response);
      if (response.access_token) {
        setToken(response.access_token);
        setUser(response.user);
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
      } else {
        console.log('Signup successful but no access token returned (email confirmation might be required)');
      }
      return response;
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    signUp,
    logout,
    isLoading,
    isAuthenticated: !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
