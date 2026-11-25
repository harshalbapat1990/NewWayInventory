<template>
  <div class="create-new-user">
    <h1 class="text-xl font-bold mb-4">Manage Users</h1>
    <form @submit.prevent="createUser" class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <input v-model.trim="form.username" placeholder="Username" required autocomplete="off" />
      <input v-model.trim="form.first_name" placeholder="First name" required />
      <input v-model.trim="form.last_name" placeholder="Last name" required />
      <input v-model="form.password" type="password" placeholder="Temporary password (12+ characters)" minlength="12" required autocomplete="new-password" />
      <select v-model="form.role" required><option value="user">User</option><option value="editor">Editor</option><option value="accountant">Accountant</option><option value="admin">Admin</option></select>
      <button type="submit">Create User</button>
    </form>
    <p v-if="message" role="status">{{ message }}</p>
    <table class="min-w-full mt-8">
      <thead><tr><th>Username</th><th>Name</th><th>Role</th><th>Status</th><th></th></tr></thead>
      <tbody><tr v-for="user in users" :key="user.id"><td>{{ user.username }}</td><td>{{ user.first_name }} {{ user.last_name }}</td><td>{{ user.role }}</td><td>{{ user.is_active ? 'Active' : 'Disabled' }}</td><td><button v-if="user.is_active" @click="deactivate(user)">Disable</button></td></tr></tbody>
    </table>
  </div>
</template>

<script>
import axios from '../../axios';
export default {
  data: () => ({ users: [], message: '', form: { username: '', first_name: '', last_name: '', password: '', role: 'user' } }),
  methods: {
    async fetchUsers() { try { this.users = (await axios.get('/users')).data; } catch (_) { this.message = 'Unable to load users'; } },
    async createUser() {
      try { await axios.post('/users', this.form); this.form = { username: '', first_name: '', last_name: '', password: '', role: 'user' }; this.message = 'User created'; await this.fetchUsers(); }
      catch (e) { this.message = e.response?.data?.message || 'Unable to create user'; }
    },
    async deactivate(user) { try { await axios.delete(`/users/${user.id}`); await this.fetchUsers(); } catch (_) { this.message = 'Unable to disable user'; } }
  },
  mounted() { this.fetchUsers(); }
};
</script>
