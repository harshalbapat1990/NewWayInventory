<template>
  <div class="register-page flex items-center justify-center h-screen bg-gray-100">
    <div class="bg-white p-8 rounded-md shadow-md w-full max-w-md">
      <h2 class="text-2xl font-bold mb-4">Register</h2>
      <form @submit.prevent="register">
        <div class="mb-4">
          <label for="firstName" class="block text-sm font-medium text-gray-700">First Name</label>
          <input type="text" id="firstName" v-model="firstName" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="lastName" class="block text-sm font-medium text-gray-700">Last Name</label>
          <input type="text" id="lastName" v-model="lastName" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
          <input type="text" id="username" v-model="username" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <input type="text" id="password" v-model="password" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirm Password</label>
          <input type="password" id="confirmPassword" v-model="confirmPassword" @input="checkPasswords" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
          <span v-if="passwordsMatch" class="text-green-500 text-sm">✔</span>
          <span v-else class="text-red-500 text-sm">✘</span>
        </div>
        <div class="flex justify-center gap-4">
          <button type="submit" :disabled="!passwordsMatch" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Register</button>
          <button type="button" @click="cancel" class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from '../axios';

export default {
  data() {
    return {
      firstName: '',
      lastName: '',
      username: '',
      password: '',
      confirmPassword: '',
      passwordsMatch: false,
      role: 'user' // Default role
    };
  },
  methods: {
    checkPasswords() {
      this.passwordsMatch = this.password === this.confirmPassword;
    },
    async register() {
      // console.log('Registering...');
      // console.log(this.firstName, this.lastName, this.username, this.password, this.role);
      if (!this.passwordsMatch) {
        alert('Passwords do not match.');
        return;
      }
      try {
        // console.log('Postman Data:', {
        //   first_name: this.firstName,
        //   last_name: this.lastName,
        //   username: this.username,
        //   password: this.password,
        //   role: this.role
        // });
        const response = await axios.post('/register', {
          first_name: this.firstName,
          last_name: this.lastName,
          username: this.username,
          password: this.password,
          role: this.role
        });
        alert('Registration successful!');
        this.$router.push('/login');
      } catch (error) {
        alert('Registration failed. Please try again.');
      }
    },
    cancel() {
      this.$router.push('/');
    }
  }
};
</script>