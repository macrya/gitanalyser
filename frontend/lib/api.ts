import axios from 'axios';
import type {
  User,
  Repository,
  Analysis,
  AnalysisDetail,
  PullRequest,
  AuthToken
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authApi = {
  getGitHubAuthUrl: async (): Promise<{ url: string }> => {
    const { data } = await api.get('/api/auth/github');
    return data;
  },

  handleGitHubCallback: async (code: string): Promise<AuthToken> => {
    const { data } = await api.post('/api/auth/github/callback', { code });
    return data;
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await api.get('/api/auth/me');
    return data;
  },
};

// Repository API
export const repositoryApi = {
  list: async (): Promise<{ repositories: Repository[]; total: number }> => {
    const { data } = await api.get('/api/repositories/');
    return data;
  },

  get: async (id: number): Promise<Repository> => {
    const { data } = await api.get(`/api/repositories/${id}`);
    return data;
  },

  sync: async (): Promise<{ message: string; synced_count: number }> => {
    const { data } = await api.post('/api/repositories/sync');
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/repositories/${id}`);
  },
};

// Analysis API
export const analysisApi = {
  create: async (repositoryId: number): Promise<Analysis> => {
    const { data } = await api.post(`/api/analysis/?repository_id=${repositoryId}`);
    return data;
  },

  get: async (id: number): Promise<AnalysisDetail> => {
    const { data } = await api.get(`/api/analysis/${id}`);
    return data;
  },

  listByRepository: async (repositoryId: number): Promise<Analysis[]> => {
    const { data } = await api.get(`/api/analysis/repository/${repositoryId}`);
    return data;
  },
};

// Pull Request API
export const pullRequestApi = {
  create: async (
    analysisId: number,
    title?: string,
    description?: string
  ): Promise<PullRequest> => {
    const { data } = await api.post('/api/pull-requests/', null, {
      params: { analysis_id: analysisId, title, description },
    });
    return data;
  },

  get: async (id: number): Promise<PullRequest> => {
    const { data } = await api.get(`/api/pull-requests/${id}`);
    return data;
  },

  listByRepository: async (repositoryId: number): Promise<PullRequest[]> => {
    const { data } = await api.get(`/api/pull-requests/repository/${repositoryId}`);
    return data;
  },
};

export default api;
