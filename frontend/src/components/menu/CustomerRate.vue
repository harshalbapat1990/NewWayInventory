<template>
  <div class="customer-rate p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Customer Rate Management</h1>
    
    <form class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="customer" class="block text-base font-medium text-gray-700">Select Customer</label>
      </div>
      <div class="col-span-2">
        <select 
          id="customer"
          v-model="selectedCustomerId"
          @change="fetchCustomerRates"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-base focus:ring-blue-500 focus:border-blue-500"
          required
        >
          <option value="">Select a customer</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.company_name }}
          </option>
        </select>
      </div>
    </form>

    <div v-if="selectedCustomerId && plateSizes.length > 0" class="mt-8">
      <div class="flex flex-col items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-800 text-center">Rate Card for {{ selectedCustomerName }}</h2>
        <button
          @click="saveRates"
          class="btn-primary mt-2 ml-auto"
          :disabled="isSaving"
        >
          {{ isSaving ? 'Saving...' : 'Save Rates' }}
        </button>
      </div>
      
      <div class="overflow-x-auto bg-white p-6 rounded-lg shadow-md">
        <table class="min-w-full">
          <thead>
            <tr class="border-b border-gray-800 pb-2">
              <th class="px-6 py-3 text-base font-bold text-gray-800">Plate Size</th>
              <th class="px-6 py-3 text-base font-bold text-gray-800">Plate Rate (₹)</th>
              <th class="px-6 py-3 text-base font-bold text-gray-800">Baking Rate (₹)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(rate, index) in customerRates" :key="index" class="border-b border-gray-200">
              <td class="px-6 py-4 whitespace-nowrap">
                {{ rate.length }}x{{ rate.width }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <input
                  type="number"
                  v-model="rate.plate_rate"
                  class="block mx-auto w-1/2 border border-gray-300 rounded-md shadow-sm text-base focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center">
                <input
                  type="number"
                  v-model="rate.baking_rate"
                  class="block mx-auto w-1/2 border border-gray-300 rounded-md shadow-sm text-base focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div v-else-if="selectedCustomerId" class="mt-8 text-center p-6 bg-white rounded-lg shadow-md">
      <p class="text-gray-500">Loading plate sizes...</p>
    </div>
    
    <div v-if="message" class="mt-6 p-4 rounded-lg" :class="messageType === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
      {{ message }}
    </div>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  name: 'CustomerRate',
  data() {
    return {
      customers: [],
      selectedCustomerId: '',
      selectedCustomerName: '',
      plateSizes: [],
      customerRates: [],
      isSaving: false,
      message: '',
      messageType: 'success'
    };
  },
  created() {
    this.fetchCustomers();
    this.fetchPlateSizes();
  },
  methods: {
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data;
      } catch (error) {
        console.error('Error fetching customers:', error);
        this.showMessage('Error fetching customers', 'error');
      }
    },
    async fetchPlateSizes() {
      try {
        const response = await axios.get('/plate-sizes');
        this.plateSizes = response.data;
        
        // Initialize customer rates with all plate sizes if a customer is already selected
        if (this.selectedCustomerId) {
          this.fetchCustomerRates();
        }
      } catch (error) {
        console.error('Error fetching plate sizes:', error);
        this.showMessage('Error fetching plate sizes', 'error');
      }
    },
    async fetchCustomerRates() {
      if (!this.selectedCustomerId) return;
      
      try {
        const selectedCustomer = this.customers.find(c => c.id === this.selectedCustomerId);
        if (selectedCustomer) {
          this.selectedCustomerName = selectedCustomer.company_name;
        }

        // First get all existing rates for this customer
        const response = await axios.get(`/customer-rates/${this.selectedCustomerId}`);
        const existingRates = response.data || [];
        
        // Initialize rates for all plate sizes, ensuring we include ALL plate sizes
        this.customerRates = this.plateSizes.map(plateSize => {
          // Find existing rate for this plate size if it exists
          const existingRate = existingRates.find(r => r.plate_size_id === plateSize.id);
          
          return {
            customer_id: this.selectedCustomerId,
            plate_size_id: plateSize.id,
            plate_size_name: plateSize.name,
            length: plateSize.length,
            width: plateSize.width,
            plate_rate: existingRate ? existingRate.plate_rate : 0,
            baking_rate: existingRate ? existingRate.baking_rate : 0
          };
        });
      } catch (error) {
        console.error('Error fetching customer rates:', error);
        this.showMessage('Error fetching customer rates', 'error');
      }
    },
    async saveRates() {
      this.isSaving = true;
      try {
        await axios.post('/customer-rates', {
          customer_id: this.selectedCustomerId,
          rates: this.customerRates.map(rate => ({
            plate_size_id: rate.plate_size_id,
            plate_rate: parseFloat(rate.plate_rate),
            baking_rate: parseFloat(rate.baking_rate)
          }))
        });
        
        this.showMessage('Rates saved successfully', 'success');
      } catch (error) {
        console.error('Error saving rates:', error);
        this.showMessage('Error saving rates', 'error');
      } finally {
        this.isSaving = false;
      }
    },
    showMessage(message, type) {
      this.message = message;
      this.messageType = type;
      
      setTimeout(() => {
        this.message = '';
      }, 5000);
    }
  }
};
</script>

<style scoped>
/* .btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline;
}

.btn-print {
  @apply bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline;
} */
</style>
