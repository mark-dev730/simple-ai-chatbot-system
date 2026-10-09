import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (username, email, password) =>
    api.post('/api/auth/register', { username, email, password }),
  
  login: (username, password) =>
    api.post('/api/auth/login/json', { username, password }),
  
  getCurrentUser: () =>
    api.get('/api/auth/me'),
  
  verifyToken: () =>
    api.get('/api/auth/verify'),
};

// Session API
export const sessionAPI = {
  list: (activeOnly = true) =>
    api.get('/api/sessions', { params: { active_only: activeOnly } }),
  
  create: (sessionName) =>
    api.post('/api/sessions', { session_name: sessionName }),
  
  get: (sessionId) =>
    api.get(`/api/sessions/${sessionId}`),
  
  update: (sessionId, data) =>
    api.put(`/api/sessions/${sessionId}`, data),
  
  delete: (sessionId) =>
    api.delete(`/api/sessions/${sessionId}`),
  
  deletePermanent: (sessionId) =>
    api.delete(`/api/sessions/${sessionId}/permanent`),
};

// Admin API
export const adminAPI = {
  getUsersCount: () =>
    api.get('/api/users/count'),
  
  listUsers: (skip = 0, limit = 100) =>
    api.get('/api/users/list', { params: { skip, limit } }),
  
  getStats: () =>
    api.get('/api/stats'),
  
  toggleUserStatus: (userId) =>
    api.patch(`/api/users/${userId}/toggle`),
  
  updateUserAccess: (userId, accessLevel) =>
    api.patch(`/api/users/${userId}/access`, null, { params: { access_level: accessLevel } }),
};

// Chat API
export const chatAPI = {
  sendMessage: (sessionId, content, modelName = 'gemma2:2b', enableRAG = false, ragTable = null) =>
    api.post(`/api/chat/send?session_id=${sessionId}`, {
      content,
      model_name: modelName,
      enable_rag: enableRAG,
      rag_table: ragTable,
    }),
  
  getHistory: (sessionId, skip = 0, limit = 100) =>
    api.get(`/api/chat/history/${sessionId}`, { params: { skip, limit } }),
  
  deleteMessage: (messageId) =>
    api.delete(`/api/chat/message/${messageId}`),
  
  listModels: () =>
    api.get('/api/chat/models'),
  
  listOllamaModels: () =>
    api.get('/api/chat/models/ollama'),
  
  checkOllamaStatus: () =>
    api.get('/api/chat/ollama/status'),
};

// RAG API
export const ragAPI = {
  getSchemaContext: (tableName = null) =>
    api.get('/api/rag/schema', { params: { table_name: tableName } }),
  
  searchData: (tableName, searchTerm = null, filters = null, limit = 10) =>
    api.post('/api/rag/search', {
      table_name: tableName,
      search_term: searchTerm,
      filters,
      limit,
    }),
  
  executeQuery: (sql, params = null) =>
    api.post('/api/rag/query', {
      sql,
      params,
    }),
  
  getStatistics: (tableName) =>
    api.get(`/api/rag/statistics/${tableName}`),
  
  listTables: () =>
    api.get('/api/rag/tables'),
  
  getColumns: (tableName) =>
    api.get(`/api/rag/columns/${tableName}`),
};

export default api;
