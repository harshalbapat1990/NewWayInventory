<!-- filepath: frontend/src/components/HomePage.vue -->
<template>
  <div class="home-page flex items-center justify-center h-screen bg-gray-100 relative overflow-hidden">
    <img
      src="../assets/NewWayLogoBG.svg"
      alt="New Way Logo"
      class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1/2 object-contain opacity-50 pointer-events-none"
    />
    <h1 class="text-2xl font-bold z-10">Select an option from the top menu</h1>
  </div>
</template>

<script>
export default {
  name: 'HomePage'
};
</script>

<style scoped>
.home-page {
  background-color: #f7fafc;
}
</style>