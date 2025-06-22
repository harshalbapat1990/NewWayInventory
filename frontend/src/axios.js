// filepath: frontend/src/axios.js
import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://192.168.31.230:5000/api',
  // baseURL: 'http://192.168.1.104:5000/api',
  // baseURL: 'http://localhost:5000/api',
});

// Add a request interceptor to include the JWT token
instance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token'); // Ensure the token is stored in localStorage
    if (token) {
      config.headers.Authorization = `Bearer ${token}`; // Add the Authorization header
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
  error => {
    if (error.response && error.response.status === 401) {
      // Redirect to the base URL when login times out
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default instance;