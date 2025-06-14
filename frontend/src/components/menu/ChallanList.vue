<!-- filepath: frontend/src/components/menu/ChallanList.vue -->
<template>
  <div class="challan-list p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Challans</h1>

    <!-- Filters -->
    <div class="filters mb-4 flex flex-wrap gap-4 items-end">
      <div>
        <label for="challanNumber" class="block text-sm font-medium text-gray-700">Challan Number</label>
        <input id="challanNumber" v-model="filters.challanCode" type="text"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          placeholder="Enter Challan Number" />
      </div>
      <div>
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
        <input id="date" v-model="filters.date" type="date"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>
      <div>
        <label for="customer" class="block text-sm font-medium text-gray-700">Customer</label>
        <select id="customer" v-model="filters.customerId"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option value="">All Customers</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.company_name }}
          </option>
        </select>
      </div>
      <div>
        <label for="printStatus" class="block text-sm font-medium text-gray-700">Print Status</label>
        <select id="printStatus" v-model="filters.printed"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option value="">All</option>
          <option value="true">Printed</option>
          <option value="false">Not Printed</option>
        </select>
      </div>
      <div class="ml-auto flex gap-2">
        <button @click="applyFilters" class="btn-primary">
          Apply Filters
        </button>
        <button @click="clearFilters" class="btn-secondary">
          Clear Filters
        </button>
      </div>
    </div>

    <!-- Challan Table -->
    <table class="table-auto w-full border-collapse border border-gray-300">
      <thead>
        <tr class="bg-gray-200">
          <th class="border border-gray-300 px-4 py-2 w-1/10">Challan Code</th>
          <th class="border border-gray-300 px-4 py-2 w-1/10">Date</th>
          <th class="border border-gray-300 px-4 py-2 w-3/20">Customer</th>
          <th class="border border-gray-300 px-4 py-2 w-1/10">Print Status</th>
          <th class="border border-gray-300 px-4 py-2 w-3/20">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="challan in challans" :key="challan.id" :class="{'bg-gray-100': challan.printed}">
          <td class="border border-gray-300 px-4 py-2 w-1/10">{{ challan.challan_code }}</td>
          <td class="border border-gray-300 px-4 py-2 w-1/10">{{ formatDate(challan.date) }}</td>
          <td class="border border-gray-300 px-4 py-2 w-3/20">{{ getCustomerName(challan.customer_id) }}</td>
          <td class="border border-gray-300 px-4 py-2 w-1/10">
            <span 
              :class="challan.printed 
                ? 'bg-green-100 text-green-800 px-2 py-1 rounded-full' 
                : 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full'"
            >
              {{ challan.printed ? 'Printed' : 'Not Printed' }}
            </span>
          </td>
          <td class="border border-gray-300 px-4 py-2 w-3/20">
            <button @click="editChallan(challan)" class="btn-primary mr-2" v-if="userRole === 'admin' || userRole === 'accountant'">Edit</button>
            <button @click="deleteChallan(challan.id)" class="btn-danger mr-2" v-if="userRole === 'admin'">Delete</button>
            <button @click="printChallan(challan)" class="btn-print mr-2" :disabled="challan.printed">Print</button>
            <button @click="togglePrintStatus(challan)" class="btn-secondary">
              {{ challan.printed ? 'Mark Not Printed' : 'Mark Printed' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from '../../axios';
import moment from 'moment';
import { printChallan } from '../../utils/printChallan';

export default {
  data() {
    return {
      challans: [],
      customers: [],
      plateSizes: [],
      filters: {
        challanCode: '',
        date: '',
        customerId: '',
        printed: ''
      },
      userRole: '', // Role of the logged-in user
    };
  },
  methods: {
    async fetchChallans() {
      try {
        const queryParams = new URLSearchParams();
        
        if (this.filters.challanCode) queryParams.append('challan_code', this.filters.challanCode);
        if (this.filters.date) queryParams.append('date', this.filters.date);
        if (this.filters.customerId) queryParams.append('customer_id', this.filters.customerId);
        if (this.filters.printed !== '') queryParams.append('printed', this.filters.printed);
        
        const url = `/challans${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        const response = await axios.get(url);
        this.challans = response.data.sort((a, b) => b.challan_code.localeCompare(a.challan_code));
      } catch (error) {
        console.error('Error fetching challans:', error);
      }
    },
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data;
      } catch (error) {
        console.error('Error fetching customers:', error);
      }
    },
    async fetchPlateSizes() {
      try {
        const response = await axios.get('/plate-summary');
        this.plateSizes = response.data.filter(plate => plate.available_quantity > 0);
      } catch (error) {
        console.error('Error fetching plate sizes:', error);
      }
    },
    formatDate(dateString) {
      return moment(dateString).format('DD MMM YYYY');
    },
    getCustomerName(customerId) {
      const customer = this.customers.find(c => c.id === customerId);
      return customer ? customer.company_name : 'Unknown';
    },
    applyFilters() {
      this.fetchChallans();
    },
    clearFilters() {
      this.filters = {
        challanCode: '',
        date: '',
        customerId: '',
        printed: ''
      };
      this.fetchChallans();
    },
    editChallan(challan) {
      this.$router.push({ path: '/jobs-delivery-challan', query: { challanId: challan.id } });
    },
    async printChallan(challan) {
      try {
        const customer = this.customers.find(c => c.id === challan.customer_id) || {};
        printChallan(challan, customer, this.plateSizes);
        // Refresh the list after printing
        setTimeout(() => this.fetchChallans(), 1000);
      } catch (error) {
        console.error('Error printing challan:', error);
      }
    },
    async togglePrintStatus(challan) {
      try {
        if (challan.printed) {
          await axios.put(`/challans/${challan.id}/mark-not-printed`);
        } else {
          await axios.put(`/challans/${challan.id}/mark-printed`);
        }
        // Refresh the list
        this.fetchChallans();
      } catch (error) {
        console.error('Error toggling print status:', error);
      }
    },
    async deleteChallan(id) {
      if (confirm('Are you sure you want to delete this challan?')) {
        try {
          await axios.delete(`/challans/${id}`);
          alert('Challan deleted successfully!');
          this.fetchChallans();
        } catch (error) {
          console.error('Error deleting challan:', error);
        }
      }
    },
  },
  mounted() {
    this.userRole = this.$store?.state?.user?.role || 'admin'; // Fetch user role from Vuex store with fallback
    this.fetchChallans();
    this.fetchCustomers();
    this.fetchPlateSizes();
  },
};
</script>

<style scoped>
.btn-primary {
  background-color: #007bff;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-danger:hover {
  background-color: #a71d2a;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.btn-secondary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
</style>