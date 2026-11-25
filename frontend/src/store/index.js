import { createStore } from 'vuex';
import axios from '../axios';

// Clear credentials written by older releases before cookie-based sessions.
['token', 'accessToken', 'refreshToken', 'tokenExpiry', 'user'].forEach(key => localStorage.removeItem(key));

export default createStore({
  state: { user: null, plateUsage: [] },
  getters: { isAuthenticated: state => !!state.user },
  mutations: {
    setUser(state, user) { state.user = user; },
    clearSession(state) { state.user = null; },
    setPlateUsage(state, data) { state.plateUsage = data; },
  },
  actions: {
    async login({ commit }, credentials) {
      try {
        const { data } = await axios.post('/login', credentials);
        commit('setUser', data.user);
        return { success: true };
      } catch (error) {
        return { success: false, message: error.response?.data?.message || 'Login failed' };
      }
    },
    async logout({ commit }) {
      try { await axios.post('/logout'); } finally { commit('clearSession'); }
    },
    async checkAuth({ state, commit }) {
      if (state.user) return true;
      try {
        const { data } = await axios.get('/user-details');
        commit('setUser', data);
        return true;
      } catch (_) {
        commit('clearSession');
        return false;
      }
    }
  }
});
