<!-- filepath: frontend/src/components/menu/PurchaseEdition.vue -->
<template>
  <div class="purchase-edition">
    <h1 class="text-xl font-bold mb-4">Purchase Edition</h1>
    <form @submit.prevent="editPurchase">
      <div class="mb-4">
        <label for="purchaseId" class="block text-sm font-medium text-gray-700">Purchase ID</label>
        <input type="text" id="purchaseId" v-model="purchaseId" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="item" class="block text-sm font-medium text-gray-700">Item</label>
        <input type="text" id="item" v-model="item" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="quantity" class="block text-sm font-medium text-gray-700">Quantity</label>
        <input type="number" id="quantity" v-model="quantity" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
        <input type="date" id="date" v-model="date" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Edit Purchase</button>
    </form>
    <table class="min-w-full divide-y divide-gray-200 mt-8">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purchase ID</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(purchase, index) in purchases" :key="index">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ purchase.purchaseId }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ purchase.item }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ purchase.quantity }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ purchase.date }}</td>
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
      purchaseId: '',
      item: '',
      quantity: '',
      date: '',
      purchases: []
    };
  },
  methods: {
    async fetchPurchases() {
      try {
        const response = await axios.get('/api/purchases');
        this.purchases = response.data;
      } catch (error) {
        console.error('Error fetching purchases:', error);
      }
    },
    async editPurchase() {
      const updatedPurchase = {
        purchaseId: this.purchaseId,
        item: this.item,
        quantity: this.quantity,
        date: this.date
      };
      try {
        const response = await axios.put(`/api/purchases/${this.purchaseId}`, updatedPurchase);
        const index = this.purchases.findIndex(purchase => purchase.purchaseId === this.purchaseId);
        if (index !== -1) {
          this.purchases.splice(index, 1, response.data);
          this.purchaseId = '';
          this.item = '';
          this.quantity = '';
          this.date = '';
        } else {
          alert('Purchase ID not found');
        }
      } catch (error) {
        console.error('Error editing purchase:', error);
      }
    }
  },
  mounted() {
    this.fetchPurchases();
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>