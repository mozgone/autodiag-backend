import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sellex_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('sellex_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password }).then((r) => r.data);

export const register = (data: {
  company_name: string; full_name: string; email: string; password: string;
}) => api.post('/auth/register', data).then((r) => r.data);

export const getMe = () => api.get('/auth/me').then((r) => r.data);

// Telegram
export const telegramAuth = (data: { init_data: string }) =>
  api.post('/auth/telegram', data).then((r) => r.data);

export const telegramLoginAndLink = (data: { init_data: string; email: string; password: string }) =>
  api.post('/auth/telegram/link', data).then((r) => r.data);

export const telegramUnlink = () =>
  api.delete('/auth/telegram/link');

// Managers
export const getManagers = (period = 'week') =>
  api.get('/managers/', { params: { period } }).then((r) => r.data);
export const getManager = (id: string, period = 'week') =>
  api.get(`/managers/${id}`, { params: { period } }).then((r) => r.data);
export const getManagerCalls = (id: string, limit = 20) =>
  api.get(`/managers/${id}/calls`, { params: { limit } }).then((r) => r.data);

// Analytics
export const getOverview = (period = 'week') =>
  api.get('/analytics/overview', { params: { period } }).then((r) => r.data);
export const getRevenueChart = (period = 'week') =>
  api.get('/analytics/chart/revenue', { params: { period } }).then((r) => r.data);
export const getRanking = (period = 'week') =>
  api.get('/analytics/ranking', { params: { period } }).then((r) => r.data);

// App settings
export const getAppInfo = () => api.get('/settings/info').then((r) => r.data);

// CRM
export const getCRMStatus = () => api.get('/crm/status').then((r) => r.data);
export const connectCRM = (data: { crm_type: string; subdomain?: string; access_token?: string; consent?: boolean }) =>
  api.post('/crm/connect', data).then((r) => r.data);
export const syncCRM = () => api.post('/crm/sync').then((r) => r.data);
