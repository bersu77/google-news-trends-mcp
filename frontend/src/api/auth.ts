import axios from 'axios';
import { LoginRequest, LoginResponse } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authAPI = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/api/auth/login', data);
    return response.data;
  },

  signup: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/api/auth/signup', data);
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string; refresh_token: string }> => {
    const response = await api.post('/api/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  getCurrentUser: async (token: string) => {
    const response = await api.get('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
};

export default api;
