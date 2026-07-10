import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  },
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
};

export const objectsApi = {
  list: () => api.get('/construction-objects').then((r) => r.data),
  create: (body: unknown) => api.post('/construction-objects', body).then((r) => r.data),
  update: (id: number, body: unknown) => api.patch(`/construction-objects/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/construction-objects/${id}`),
};

export const scenariosApi = {
  list: (includeArchived = false) =>
    api.get('/scenarios', { params: { include_archived: includeArchived } }).then((r) => r.data),
  get: (id: number) => api.get(`/scenarios/${id}`).then((r) => r.data),
  create: (body: unknown) => api.post('/scenarios', body).then((r) => r.data),
  recalculate: (id: number) => api.post(`/scenarios/${id}/recalculate`).then((r) => r.data),
  compare: (a: number, b: number) =>
    api.get('/scenarios/compare', { params: { version_a: a, version_b: b } }).then((r) => r.data),
};

export const cashFlowApi = {
  list: (scenarioId: number) =>
    api.get('/cash-flow-lines', { params: { scenario_id: scenarioId } }).then((r) => r.data),
  update: (id: number, body: { base_amount?: number; adjustment?: number }) =>
    api.patch(`/cash-flow-lines/${id}`, body).then((r) => r.data),
};

export const resultsApi = {
  list: (scenarioId: number, objectId?: number) =>
    api
      .get('/financial-results', {
        params: { scenario_id: scenarioId, construction_object_id: objectId },
      })
      .then((r) => r.data),
  consolidated: (scenarioId: number) =>
    api.get('/financial-results/consolidated', { params: { scenario_id: scenarioId } }).then((r) => r.data),
};

export const reportsApi = {
  generate: (body: { scenario_id: number; type: string; format: 'excel' | 'pdf' }) =>
    api.post('/reports/generate', body).then((r) => r.data),
  downloadUrl: (id: number) => `${API_URL}/reports/${id}/download`,
};

export const importApi = {
  validate: (file_path: string) => api.post('/import/validate', { file_path }).then((r) => r.data),
  run: (scenario_id: number, file_path: string) =>
    api.post('/import/import', { scenario_id, file_path }).then((r) => r.data),
};

export const factApi = {
  trigger: () => api.post('/fact-loading/trigger').then((r) => r.data),
  log: () => api.get('/fact-loading/log').then((r) => r.data),
};

export const usersApi = {
  list: () => api.get('/users').then((r) => r.data),
};

export function money(n: number) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(n || 0);
}
