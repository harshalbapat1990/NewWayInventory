<!-- filepath: frontend/src/components/LandingPage.vue -->
<template>
  <div class="landing-page flex items-center justify-center h-screen bg-gray-100 flex-col">
    <h1 class="text-4xl font-bold mb-4">Welcome to the App</h1>
    <p class="mb-6">Please log in to use the app</p>
    <div class="space-x-4">
      <button @click="navigateToLogin" class="px-4 py-2 bg-indigo-600 text-white rounded-md shadow-md hover:bg-indigo-700">
        Login
      </button>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    navigateToLogin() {
      this.$router.push('/login');
    },
  }
};
</script>

<style scoped>
.landing-page {
  background-color: #f7fafc;
}
</style>
