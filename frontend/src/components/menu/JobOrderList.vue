<!-- filepath: frontend/src/components/menu/JobOrderList.vue -->
<template>
  <div class="job-order-list p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Job Orders</h1>
    <table class="table-auto w-full border-collapse border border-gray-300">
      <thead>
        <tr class="bg-gray-200">
          <th class="border border-gray-300 px-4 py-2">Job Code</th>
          <th class="border border-gray-300 px-4 py-2">Job Date</th>
          <th class="border border-gray-300 px-4 py-2">Customer</th>
          <th class="border border-gray-300 px-4 py-2">Remark</th>
          <th v-if="userRole === 'admin'" class="border border-gray-300 px-4 py-2">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="jobOrder in jobOrders" :key="jobOrder.id">
          <td class="border border-gray-300 px-4 py-2">{{ jobOrder.job_code }}</td>
          <td class="border border-gray-300 px-4 py-2">{{ jobOrder.job_date }}</td>
          <td class="border border-gray-300 px-4 py-2">{{ getCustomerName(jobOrder.customer_id) }}</td>
          <td class="border border-gray-300 px-4 py-2">{{ jobOrder.remark }}</td>
          <td v-if="userRole === 'admin'" class="border border-gray-300 px-4 py-2">
            <button @click="editJobOrder(jobOrder)" class="btn-primary mr-2">Edit</button>
            <button @click="deleteJobOrder(jobOrder.id)" class="btn-danger">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  data() {
    return {
      jobOrders: [],
      customers: [],
      userRole: '', // Role of the logged-in user
    };
  },
  methods: {
    async fetchJobOrders() {
      try {
        const response = await axios.get('/job-orders');
        this.jobOrders = response.data;
      } catch (error) {
        console.error('Error fetching job orders:', error);
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
    getCustomerName(customerId) {
      const customer = this.customers.find(c => c.id === customerId);
      return customer ? customer.company_name : 'Unknown';
    },
    editJobOrder(jobOrder) {
      this.$router.push({ path: '/new-job', query: { jobOrderId: jobOrder.id } });
    },
    async deleteJobOrder(id) {
      if (confirm('Are you sure you want to delete this job order?')) {
        try {
          await axios.delete(`/job-orders/${id}`);
          alert('Job order deleted successfully!');
          this.fetchJobOrders();
        } catch (error) {
          console.error('Error deleting job order:', error);
        }
      }
    },
  },
  mounted() {
    this.userRole = this.$store.state.user.role; // Fetch user role from Vuex store
    this.fetchJobOrders();
    this.fetchCustomers();
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
</style>