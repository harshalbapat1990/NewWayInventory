// filepath: frontend/src/axios.js
import axios from 'axios';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

instance.interceptors.request.use(
  config => {
    const method = (config.method || 'get').toLowerCase();
    if (!['get', 'head', 'options'].includes(method)) {
      const cookieName = config.url?.includes('/refresh') ? 'csrf_refresh_token' : 'csrf_access_token';
      const csrf = document.cookie.split('; ').find(row => row.startsWith(`${cookieName}=`))?.split('=').slice(1).join('=');
      if (csrf) config.headers['X-CSRF-TOKEN'] = decodeURIComponent(csrf);
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
instance.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config;
    const url = original?.url || '';
    if (error.response?.status === 401 && original && !original._retry && !['/login', '/refresh', '/logout'].some(path => url.endsWith(path))) {
      original._retry = true;
      try {
        await instance.post('/refresh');
        return instance(original);
      } catch (_) {
        if (!window.location.pathname.startsWith('/login')) window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
