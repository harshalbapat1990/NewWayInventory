<!-- filepath: frontend/src/components/modals/AddSizeModal.vue -->
<template>
  <div class="fixed inset-0 flex items-center justify-center bg-gray-800 bg-opacity-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/3">
      <h2 class="text-xl font-bold mb-4">Add New Size</h2>
      <form @submit.prevent="addSize">
        <div class="mb-4">
          <label for="length" class="block text-sm font-medium text-gray-700">Length</label>
          <input type="number" id="length" v-model="length" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="width" class="block text-sm font-medium text-gray-700">Width</label>
          <input type="number" id="width" v-model="width" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
        </div>
        <div class="mb-4">
          <label for="is_dl" class="flex items-center text-sm font-medium text-gray-700">
            <input type="checkbox" id="is_dl" v-model="is_dl" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mr-2">
            DL Type Plate
          </label>
        </div>
        <div class="flex justify-end">
          <button type="button" @click="$emit('close')" class="mr-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-gray-700 bg-gray-200 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">Cancel</button>
          <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Add Size</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  data() {
    return {
      length: '',
      width: '',
      is_dl: false  // Added new data property for DL type
    };
  },
  methods: {
    async addSize() {
      try {
        const response = await axios.post('/plate-sizes', {
          length: this.length,
          width: this.width,
          is_dl: this.is_dl  // Include is_dl in the request payload
        });
        const newSize = response.data;
        this.$emit('size-added', newSize);
        this.$emit('close');
      } catch (error) {
        console.error('Error adding size:', error);
      }
    }
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>