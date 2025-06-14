<!-- filepath: frontend/src/components/menu/DeliveryChallan.vue -->
<template>
  <div class="delivery-challan">
    <h1 class="text-xl font-bold mb-4">Delivery Challan</h1>
    <form @submit.prevent="addChallan">
      <div class="mb-4">
        <label for="challanNumber" class="block text-sm font-medium text-gray-700">Challan Number</label>
        <input type="text" id="challanNumber" v-model="challanNumber" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="customerName" class="block text-sm font-medium text-gray-700">Customer Name</label>
        <input type="text" id="customerName" v-model="customerName" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
        <input type="date" id="date" v-model="date" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="items" class="block text-sm font-medium text-gray-700">Items</label>
        <textarea id="items" v-model="items" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required></textarea>
      </div>
      <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Add Challan</button>
    </form>
    <table class="min-w-full divide-y divide-gray-200 mt-8">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Challan Number</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer Name</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(challan, index) in challans" :key="index">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ challan.challanNumber }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ challan.customerName }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ challan.date }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ challan.items }}</td>
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
      challanNumber: '',
      customerName: '',
      date: '',
      items: '',
      challans: []
    };
  },
  methods: {
    async fetchChallans() {
      try {
        const response = await axios.get('/api/challans');
        this.challans = response.data;
      } catch (error) {
        console.error('Error fetching challans:', error);
      }
    },
    async addChallan() {
      const newChallan = {
        challanNumber: this.challanNumber,
        customerName: this.customerName,
        date: this.date,
        items: this.items
      };
      try {
        const response = await axios.post('/api/challans', newChallan);
        this.challans.push(response.data);
        this.challanNumber = '';
        this.customerName = '';
        this.date = '';
        this.items = '';
      } catch (error) {
        console.error('Error adding challan:', error);
      }
    }
  },
  mounted() {
    this.fetchChallans();
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>