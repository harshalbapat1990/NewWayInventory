<!-- filepath: frontend/src/components/menu/AdjustStockReview.vue -->
<template>
  <div class="adjust-stock-review">
    <h1 class="text-xl font-bold mb-4">Adjust Stock Review</h1>
    <form @submit.prevent="adjustStock">
      <div class="mb-4">
        <label for="item" class="block text-sm font-medium text-gray-700">Item</label>
        <input type="text" id="item" v-model="item" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="quantity" class="block text-sm font-medium text-gray-700">Quantity</label>
        <input type="number" id="quantity" v-model="quantity" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Adjust Stock</button>
    </form>
    <table class="min-w-full divide-y divide-gray-200 mt-8">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(stock, index) in stockAdjustments" :key="index">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ stock.item }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ stock.quantity }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      item: '',
      quantity: '',
      stockAdjustments: []
    };
  },
  methods: {
    async fetchStockAdjustments() {
      try {
        const response = await axios.get('/api/stock-adjustments');
        this.stockAdjustments = response.data;
      } catch (error) {
        console.error('Error fetching stock adjustments:', error);
      }
    },
    async adjustStock() {
      const stockAdjustment = {
        item: this.item,
        quantity: this.quantity
      };
      try {
        const response = await axios.post('/api/stock-adjustments', stockAdjustment);
        const index = this.stockAdjustments.findIndex(stock => stock.item === this.item);
        if (index !== -1) {
          this.stockAdjustments.splice(index, 1, response.data);
        } else {
          this.stockAdjustments.push(response.data);
        }
        this.item = '';
        this.quantity = '';
      } catch (error) {
        console.error('Error adjusting stock:', error);
      }
    }
  },
  mounted() {
    this.fetchStockAdjustments();
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>