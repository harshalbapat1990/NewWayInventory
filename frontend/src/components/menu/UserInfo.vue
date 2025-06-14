<template>
  <div class="user-details p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-4 text-gray-800">User Details</h1>
    <div v-if="user" class="mb-6">
      <p><strong>Username:</strong> {{ user.username }}</p>
      <p><strong>First Name:</strong> {{ user.first_name }}</p>
      <p><strong>Last Name:</strong> {{ user.last_name }}</p>
      <p><strong>Role:</strong> {{ user.role }}</p>
    </div>

    <h2 class="text-xl font-bold mb-4 text-gray-800">Reset Password</h2>
    <form @submit.prevent="resetPassword" class="grid grid-cols-1 gap-4">
      <div>
        <label for="new-password" class="block text-sm font-medium text-gray-700">New Password</label>
        <input
          type="password"
          id="new-password"
          v-model="newPassword"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        />
      </div>
      <button
        type="submit"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-500 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Reset Password
      </button>
    </form>
    <p v-if="message" class="mt-4 text-sm text-green-600">{{ message }}</p>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  data() {
    return {
      user: null,
      newPassword: '',
      message: '',
    };
  },
  methods: {
    async fetchUserDetails() {
      try {
        const response = await axios.get('/user-details', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        this.user = response.data;
      } catch (error) {
        console.error('Error fetching user details:', error);
      }
    },
    async resetPassword() {
      try {
        const response = await axios.post(
          '/api/reset-password',
          { new_password: this.newPassword },
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        );
        this.message = response.data.message;
        this.newPassword = '';
      } catch (error) {
        console.error('Error resetting password:', error);
        this.message = error.response?.data?.message || 'An error occurred';
      }
    },
  },
  mounted() {
    this.fetchUserDetails();
  },
};
</script>

<style scoped>
/* Add any custom styles here */
</style>