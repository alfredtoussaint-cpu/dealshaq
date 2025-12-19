import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't redirect on login/register endpoints
    const isAuthEndpoint = error.config?.url?.includes('/auth/login') || 
                          error.config?.url?.includes('/auth/register');
    
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;

export const auth = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  requestPasswordReset: (data) => api.post('/auth/password-reset/request', data),
  confirmPasswordReset: (data) => api.post('/auth/password-reset/confirm', data),
};

export const charities = {
  list: () => api.get('/charities'),
  create: (data) => api.post('/charities', data),
};

export const rshd = {
  list: (category) => api.get('/rshd/items', { params: { category } }),
  myItems: () => api.get('/rshd/my-items'),
  create: (data) => api.post('/rshd/items', data),
  update: (id, data) => api.put(`/rshd/items/${id}`, data),
  delete: (id) => api.delete(`/rshd/items/${id}`),
};

export const favorites = {
  list: () => api.get('/favorites'),
  create: (data) => api.post('/favorites', data),
  delete: (id) => api.delete(`/favorites/${id}`),
};

// Item-level favorites (Enhanced DACFI-List)
export const favoriteItems = {
  list: () => api.get('/favorites/items'),
  create: (data) => api.post('/favorites/items', data),
  delete: (itemName) => api.post('/favorites/items/delete', { item_name: itemName }),
};

// User settings
export const userSettings = {
  updateAutoThreshold: (data) => api.put('/users/settings/auto-threshold', data),
};

// DAC Retailers (DACDRLP-List management)
export const dacRetailers = {
  list: () => api.get('/dac/retailers'),
  add: (drlpId) => api.post(`/dac/retailers/add?drlp_id=${drlpId}`),
  remove: (drlpId) => api.delete(`/dac/retailers/${drlpId}`),
  updateDacsai: (radius, deliveryLocation = null) => {
    let url = `/dac/dacsai?dacsai_rad=${radius}`;
    if (deliveryLocation) {
      return api.put(url, deliveryLocation);
    }
    return api.put(url);
  },
  updateLocation: (deliveryLocation) => api.put('/dac/location', deliveryLocation),
};

export const notifications = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.put(`/notifications/${id}/read`),
};

export const orders = {
  list: () => api.get('/orders'),
  create: (data) => api.post('/orders', data),
};

export const drlp = {
  locations: () => api.get('/drlp/locations'),
  myLocation: () => api.get('/drlp/my-location'),
  createLocation: (data) => api.post('/drlp/locations', data),
};

export const admin = {
  stats: () => api.get('/admin/stats'),
  users: () => api.get('/admin/users'),
  items: () => api.get('/admin/items'),
};

export const categories = {
  list: () => api.get('/categories'),
};
