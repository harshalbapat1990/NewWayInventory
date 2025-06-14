// filepath: frontend/src/store/index.js
import { createStore } from 'vuex';
import axios from '../axios';

export default createStore({
  state: {
    user: JSON.parse(localStorage.getItem('user')) || null, // Load user from localStorage
    token: localStorage.getItem('token') || null, // Load token from localStorage
    plateUsage: [], // Store plate usage data
    tokenExpiry: localStorage.getItem('tokenExpiry') || null // Track token expiration time
  },
  getters: {
    isAuthenticated: state => !!state.token,
    isTokenExpired: state => {
      if (!state.tokenExpiry) return true;
      return Date.now() > parseInt(state.tokenExpiry);
    }
  },
  mutations: {
    setUser(state, user) {
      state.user = user;
      localStorage.setItem('user', JSON.stringify(user)); // Save user to localStorage
    },
    setToken(state, token) {
      state.token = token;
      localStorage.setItem('token', token); // Save token to localStorage
      
      // Set token expiry to a much longer time (e.g., 7 days)
      const tokenExpiry = Date.now() + (7 * 24 * 60 * 60 * 1000);
      state.tokenExpiry = tokenExpiry;
      localStorage.setItem('tokenExpiry', tokenExpiry);
    },
    clearSession(state) {
      state.user = null;
      state.token = null;
      state.tokenExpiry = null;
      localStorage.removeItem('user'); // Clear user from localStorage
      localStorage.removeItem('token'); // Clear token from localStorage
      localStorage.removeItem('tokenExpiry'); // Clear token expiry
    },
    setPlateUsage(state, data) {
      state.plateUsage = data; // Update plate usage data
    },
  },
  actions: {
    async login({ commit }, credentials) {
      try {
        const response = await axios.post('/login', credentials);
        const token = response.data.access_token;
        const user = JSON.parse(atob(token.split('.')[1])); // Decode JWT payload
        commit('setUser', user);
        commit('setToken', token);
        return { success: true };
      } catch (error) {
        return { success: false, message: error.response.data.message };
      }
    },
    logout({ commit }) {
      commit('clearSession'); // Clear session on logout
    },
    checkAuth({ state, getters, dispatch }) {
      // First check if we have a token
      if (!state.token) return false;
      
      // Then check if the token is expired
      if (getters.isTokenExpired) {
        dispatch('logout');
        return false;
      }
      
      return true;
    }
  }
});