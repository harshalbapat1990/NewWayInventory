<!-- filepath: frontend/src/components/menu/AddEditCustomer.vue -->
<template>
  <div class="customer p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Customer Management</h1>
    <form @submit.prevent="addCustomer" novalidate class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="company_name" class="block text-sm font-medium text-gray-700">Company Name</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="company_name"
          v-model="company_name"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.company_name}"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="contact_person" class="block text-sm font-medium text-gray-700">Contact Person</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="contact_person"
          v-model="contact_person"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.contact_person}"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="address" class="block text-sm font-medium text-gray-700">Address</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="address"
          v-model="address"
          maxlength="179"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.address}"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="gstin" class="block text-sm font-medium text-gray-700">GSTIN/UIN</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="gstin"
          v-model="gstin"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      <div class="col-span-1">
        <label for="state" class="block text-sm font-medium text-gray-700">State</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="state"
          v-model="state"
          placeholder="Maharashtra"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      <div class="col-span-1">
        <label for="code" class="block text-sm font-medium text-gray-700">State Code</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="code"
          v-model="code"
          placeholder="27"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      <div class="col-span-1">
        <label for="phone" class="block text-sm font-medium text-gray-700">Phone</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="phone"
          v-model="phone"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.phone}"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="mobile" class="block text-sm font-medium text-gray-700">Mobile</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="mobile"
          v-model="mobile"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.mobile}"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="email" class="block text-sm font-medium text-gray-700">Email(s)</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="email"
          v-model="email"
          placeholder="Separate multiple emails with commas"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{'border-red-500': errors.email}"
          required
        />
      </div>

      <div class="col-span-3 flex justify-end space-x-4">
        <button type="submit" class="btn-add">
          {{ saveButtonText }}
        </button>
        <button
          v-if="saveButtonText === 'Save'"
          type="button"
          class="btn-cancel"
          @click="cancelEdit"
        >
          Cancel Edit
        </button>
      </div>
    </form>
    <!-- Search Bar -->
    <div class="my-4 flex items-center">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Search by Company or Contact Person"
        class="w-1/3 border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>
    <table class="table mt-6">
      <thead>
        <tr>
          <th>Company Name</th>
          <th>Contact Person</th>
          <th>Address</th>
          <th>GSTIN</th>
          <th>Phone</th>
          <th>Mobile</th>
          <th>Email</th>
          <th v-if="userRole === 'admin' || userRole === 'accountant'">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(customer, index) in filteredCustomers" :key="index">
          <td>{{ customer.company_name }}</td>
          <td>{{ customer.contact_person }}</td>
          <td>{{ customer.address }}</td>
          <td>{{ customer.gstin || '-' }}</td>
          <td>{{ customer.phone }}</td>
          <td>{{ customer.mobile }}</td>
          <td>{{ customer.email }}</td>
          <td v-if="userRole === 'admin' || userRole === 'accountant'">
            <button class="btn-edit" @click="editCustomer(index)">Edit</button>
            <button class="btn-danger" @click="deleteCustomer(customer.id)">Delete</button>
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
      company_name: '',
      contact_person: '',
      customerId: '',
      address: '',
      gstin: '',
      state: 'Maharashtra',
      code: '27',
      phone: '',
      mobile: '',
      email: '', // comma-separated string in UI
      customers: [],
      saveButtonText: 'Add',
      userRole: '', // Role of the logged-in user
      errors: {}, // Object to store validation errors
      searchQuery: '', // <-- Added for search
    };
  },
  computed: {
    filteredCustomers() {
      if (!this.searchQuery.trim()) {
        return this.customers;
      }
      const query = this.searchQuery.trim().toLowerCase();
      return this.customers.filter(c =>
        (c.company_name && c.company_name.toLowerCase().includes(query)) ||
        (c.contact_person && c.contact_person.toLowerCase().includes(query))
      );
    },
  },
  methods: {
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data;
      } catch (error) {
        console.error('Error fetching customers:', error);
      }
    },
    validateForm() {
      this.errors = {};

      if (!this.company_name) {
        this.errors.company_name = 'Company Name is required.';
        alert(this.errors.company_name);
        return false;
      }
      if (!this.contact_person) {
        this.errors.contact_person = 'Contact Person is required.';
        alert(this.errors.contact_person);
        return false;
      }
      if (!this.address) {
        this.errors.address = 'Address is required.';
        alert(this.errors.address);
        return false;
      }
      if (!this.phone) {
        this.errors.phone = 'Phone is required.';
        alert(this.errors.phone);
        return false;
      }
      if (!this.mobile || !/^\d{10}$/.test(this.mobile)) {
        this.errors.mobile = 'Mobile must be a valid 10-digit number.';
        alert(this.errors.mobile);
        return false;
      }
      const emails = this.email.split(',').map(e => e.trim()).filter(e => e);
      if (!emails.length || !emails.every(e => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e))) {
        this.errors.email = 'Enter valid email addresses, separated by commas.';
        alert(this.errors.email);
        return false;
      }

      return true;
    },
    async addCustomer() {
      if (!this.validateForm()) {
        return;
      }

      const customer = {
        company_name: this.company_name,
        contact_person: this.contact_person,
        address: this.address,
        gstin: this.gstin,
        state: this.state || 'Maharashtra',
        code: this.code || '27',
        phone: this.phone,
        mobile: this.mobile,
        email: this.email.split(',').map(e => e.trim()).filter(e => e),
      };

      try {
        if (this.saveButtonText === 'Save') {
          const response = await axios.put(`/customers/${this.customerId}`, customer);
          const index = this.customers.findIndex(c => c.id === this.customerId);
          if (index !== -1) {
            this.customers.splice(index, 1, response.data);
          }
        } else {
          const response = await axios.post('/customers', customer);
          this.customers.push(response.data);
        }
        this.resetForm();
        await this.fetchCustomers(); // Refresh the customer list
      } catch (error) {
        console.error('Error saving customer:', error);
      }
    },
    async deleteCustomer(id) {
      try {
        await axios.delete(`/customers/${id}`);
        this.customers = this.customers.filter(customer => customer.id !== id);
      } catch (error) {
        console.error('Error deleting customer:', error);
      }
    },
    editCustomer(index) {
      const customer = this.customers[index];
      this.company_name = customer.company_name;
      this.contact_person = customer.contact_person;
      this.address = customer.address;
      this.gstin = customer.gstin || '';
      this.state = customer.state || 'Maharashtra';
      this.code = customer.code || '27';
      this.phone = customer.phone;
      this.mobile = customer.mobile;
      this.email = Array.isArray(customer.email) ? customer.email.join(', ') : customer.email;
      this.saveButtonText = 'Save';
      this.customerId = customer.id;
      // Scroll to top of the form
      this.$nextTick(() => {
        const form = this.$el.querySelector('form');
        if (form) {
          form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    },
    cancelEdit() {
      this.resetForm();
    },
    resetForm() {
      this.company_name = '';
      this.contact_person = '';
      this.address = '';
      this.gstin = '';
      this.state = 'Maharashtra';
      this.code = '27';
      this.phone = '';
      this.mobile = '';
      this.email = '';
      this.saveButtonText = 'Add';
      this.customerId = '';
      this.errors = {};
    },
  },
  mounted() {
    this.userRole = this.$store.state.user.role; // Fetch user role from Vuex store
    this.fetchCustomers();
  },
};
</script>

<style scoped>
/* Add any additional styles here */
</style>