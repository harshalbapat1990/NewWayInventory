<!-- filepath: frontend/src/components/menu/StockSummary.vue -->
<template>
  <div class="stock-summary">
    <h1 class="text-xl font-bold mb-4">Stock Summary</h1>
    <table class="min-w-full divide-y divide-gray-200 mt-8">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(stock, index) in stockSummary" :key="index">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ stock.item }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ stock.quantity }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ stock.date }}</td>
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
      stockSummary: []
    };
  },
  methods: {
    async fetchStockSummary() {
      try {
        const response = await axios.get('/api/stock-summary');
        this.stockSummary = response.data;
      } catch (error) {
        console.error('Error fetching stock summary:', error);
      }
    }
  },
  mounted() {
    this.fetchStockSummary();
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>