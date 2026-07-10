import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
};

export const scenariosApi = {
  list: (includeArchived = false) =>
    api.get('/scenarios', { params: { include_archived: includeArchived } }).then((r) => r.data),
  create: (data: object) => api.post('/scenarios', data).then((r) => r.data),
  recalculate: (id: string) => api.post(`/scenarios/${id}/recalculate`).then((r) => r.data),
  compare: (a: string, b: string) =>
    api.get('/scenarios/compare', { params: { version_a: a, version_b: b } }).then((r) => r.data),
  compareChart: (a: string, b: string) =>
    api.get('/scenarios/compare/chart', { params: { version_a: a, version_b: b } }).then((r) => r.data),
};

export const objectsApi = {
  list: () => api.get('/construction-objects').then((r) => r.data),
  create: (data: object) => api.post('/construction-objects', data).then((r) => r.data),
};

export const cashFlowApi = {
  grid: (scenarioId: string) =>
    api.get('/cash-flow-lines/grid', { params: { scenario_id: scenarioId } }).then((r) => r.data),
  update: (id: string, data: object) =>
    api.patch(`/cash-flow-lines/${id}`, data).then((r) => r.data),
};

export const financialApi = {
  consolidated: (scenarioId: string) =>
    api.get('/financial-results/consolidated', { params: { scenario_id: scenarioId } }).then((r) => r.data),
  byObject: (scenarioId: string) =>
    api.get('/financial-results/by-object', { params: { scenario_id: scenarioId } }).then((r) => r.data),
  summary: (scenarioId: string) =>
    api.get('/financial-results/summary', { params: { scenario_id: scenarioId } }).then((r) => r.data),
};

export const reportsApi = {
  generate: (data: object) => api.post('/reports/generate', data).then((r) => r.data),
  list: () => api.get('/reports').then((r) => r.data),
};

export const importApi = {
  validate: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/import/validate', form).then((r) => r.data);
  },
  import: (scenarioId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/import/${scenarioId}`, form).then((r) => r.data);
  },
};

export const factApi = {
  trigger: () => api.post('/fact-loading/trigger').then((r) => r.data),
  log: () => api.get('/fact-loading/log').then((r) => r.data),
};

export default api;
