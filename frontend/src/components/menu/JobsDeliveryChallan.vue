<!-- filepath: frontend/src/components/menu/JobsDeliveryChallan.vue -->
<template>
  <div class="jobs-delivery-challan p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">{{ isEditing ? 'Edit Delivery Challan' : 'New Delivery Challan' }}
    </h1>
    <form @submit.prevent="saveChallan(false)" novalidate
      class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <!-- Challan Code and Date -->
      <div class="col-span-3 grid grid-cols-2 gap-6">
        <!-- Left Section: Challan Code, Date, and Customer Selection -->
        <div class="space-y-6">
          <div>
            <label for="challanCode" class="block text-sm font-medium text-gray-700">Challan Code</label>
            <p id="challanCode" class="mt-1 w-full border border-gray-300 rounded-md shadow-sm bg-gray-100 text-sm">
              {{ challanCode }}
            </p>
          </div>
          <div>
            <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
            <input type="date" id="date" v-model="date"
              class="mt-1 w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
              required />
          </div>
          <div>
            <label for="customer" class="block text-sm font-medium text-gray-700">Customer</label>
            <select id="customer" v-model="selectedCustomerId" @change="fetchCustomerDetails"
              class="mt-1 w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
              required>
              <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                {{ customer.company_name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Right Section: Customer Details -->
        <div>
          <label class="block text-sm font-medium text-gray-700">Customer Details</label>
          <div class="mt-1 bg-gray-100 p-3 rounded-md text-sm border border-gray-300 space-y-1">
            <p><strong>Address:</strong> {{ customerDetails.address || 'N/A' }}</p>
            <p><strong>Contact:</strong> {{ customerDetails.contact_person || 'N/A' }}</p>
            <p><strong>Phone:</strong> {{ customerDetails.phone || 'N/A' }}</p>
            <p><strong>Mobile:</strong> {{ customerDetails.mobile || 'N/A' }}</p>
            <p><strong>Email:</strong> {{ customerDetails.email || 'N/A' }}</p>
          </div>
        </div>
      </div>

      <!-- Add Jobs -->
      <div class="col-span-3">
        <h2 class="text-lg font-bold mb-4">Add Jobs</h2>
        <div v-for="(job, index) in jobs" :key="index" class="flex flex-wrap items-center gap-2 mb-2">
          <!-- Job Name -->
          <div class="flex-[0_0_45%]">
            <label for="jobName" class="block text-sm font-medium text-gray-700">Job Name</label>
            <input type="text" v-model="job.job_name"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter job name" required />
          </div>
          <!-- Job ID -->
          <div class="flex-[0_0_8%]">
            <label for="jobId" class="block text-sm font-medium text-gray-700">Job ID</label>
            <input type="text" v-model="job.jobId"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              required />
          </div>
          <!-- Plate Size -->
          <div class="flex-[0_0_8%]">
            <label for="plateSize" class="block text-sm font-medium text-gray-700">Plate Size</label>
            <select v-model="job.plate_size_id"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              required>
              <option v-for="size in plateSizes" :key="size.size_id" :value="size.size_id">
                {{ getSizeDisplay(size) }}
              </option>
            </select>
          </div>
          <!-- Colour -->
          <div class="flex-[0_0_5%]">
            <label for="colour" class="block text-sm font-medium text-gray-700">Colour</label>
            <select v-model="job.colour" @change="calculatePlates(job)"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              required>
              <option v-for="colour in [1, 2, 3, 4, 5, 6, 7, 8]" :key="colour" :value="colour">
                {{ colour }}
              </option>
            </select>
          </div>
          <!-- Quantity -->
          <div class="flex-[0_0_5%]">
            <label for="quantity" class="block text-sm font-medium text-gray-700">Quantity</label>
            <input type="number" v-model="job.quantity" @input="calculatePlates(job)"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              min="1" required />
          </div>
          <!-- No. of Plates -->
          <div class="flex-[0_0_8%]">
            <label for="plates" class="block text-sm font-medium text-gray-700">No. of Plates</label>
            <p class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm bg-gray-100 sm:text-sm">
              {{ job.plates }}
            </p>
          </div>
          <!-- Remark -->
          <div class="flex-[0_0_15%]">
            <label for="remark" class="block text-sm font-medium text-gray-700">Remark</label>
            <input list="remarkOptions" v-model="job.remark"
              class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter or select a remark" />
            <datalist id="remarkOptions">
              <option value="No bill"></option>
              <option value="New with changes"></option>
              <option value="Repeat set"></option>
              <option value="Baking"></option>
              <option value="Consult"></option>
            </datalist>
          </div>
          <!-- Delete Button -->
          <div class="flex items-center self-end mb-1">
            <TrashIcon @click="deleteJob(index)" class="h-5 w-5 text-red-500 cursor-pointer" />
          </div>
        </div>
        <button type="button" @click="addJob" class="btn-add">Add Another Job</button>
      </div>

      <!-- Special Instructions -->
      <div class="col-span-3">
        <div class="flex flex-col">
          <label for="specialInstructions" class="block text-sm font-medium text-gray-700">Special Instructions</label>
          <textarea
            id="specialInstructions"
            v-model="specialInstructions"
            rows="3"
            class="mt-1 w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            placeholder="Enter any special instructions or notes"
          ></textarea>
        </div>
      </div>

      <!-- Submit and Cancel Buttons -->
      <div class="col-span-3 flex justify-end space-x-4">
        <button type="button" @click="saveChallan(false)" class="btn-primary">
          Save Challan
        </button>
        <button type="button" @click="saveChallan(true)" class="btn-secondary">
          Save and Print Challan
        </button>
        <button v-if="isEditing" type="button" @click="cancelEdit" class="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from '../../axios';
import moment from 'moment';
import { TrashIcon } from '@heroicons/vue/24/outline';
import { printChallan } from '../../utils/printChallan';

export default {
  components: {
    TrashIcon,
  },
  data() {
    return {
      challanCode: '',
      date: '',
      selectedCustomerId: null,
      customers: [],
      customerDetails: {
        address: '',
        contact_person: '',
        phone: '',
        mobile: '',
        email: '',
      },
      plateSizes: [],
      jobs: [
        {
          job_name: '',
          jobId: '',
          plate_size_id: '',
          colour: '',
          quantity: 1,
          plates: 0,
          remark: '',
        },
      ],
      specialInstructions: '',
      isEditing: false,
      challanId: null,
    };
  },
  methods: {
    async saveChallan(printAfterSave) {
      if (!this.validateForm()) {
        return;
      }

      const challan = {
        challan_code: this.challanCode,
        date: this.date,
        customer_id: this.selectedCustomerId,
        special_instructions: this.specialInstructions,
        jobs: this.jobs.map(job => ({
          job_name: job.job_name,
          job_id: job.jobId,
          plate_size_id: job.plate_size_id,
          colour: job.colour,
          quantity: job.quantity,
          plates: job.plates,
          remark: job.remark,
        })),
      };

      try {
        if (this.isEditing) {
          // console.log(challan);
          await axios.put(`/challans/${this.challanId}`, challan);
          alert('Challan updated successfully!');
        } else {
          await axios.post('/challans', challan);
          alert('Challan submitted successfully!');
        }

        if (printAfterSave) {
          const customer = this.customers.find(c => c.id === challan.customer_id) || {};
          printChallan(challan, customer, this.plateSizes);
        }

        this.resetForm();
        this.$router.push('/challan-list');
      } catch (error) {
        console.error('Error saving challan:', error);
      }
    },
    validateForm() {
      if (!this.date) {
        alert('Date is required.');
        return false;
      }
      if (!this.selectedCustomerId) {
        alert('Customer is required.');
        return false;
      }
      for (const job of this.jobs) {
        if (!job.job_name) {
          alert('Job Name is required.');
          return false;
        }
        if (!job.jobId) {
          alert('Job ID is required.');
          return false;
        }
        if (!job.plate_size_id) {
          alert('Plate Size is required.');
          return false;
        }
        if (!job.colour) {
          alert('Colour is required.');
          return false;
        }
        if (!job.quantity || job.quantity < 1) {
          alert('Quantity must be at least 1.');
          return false;
        }
      }
      return true;
    },
    async fetchPlateSizes() {
      try {
        const response = await axios.get('/plate-summary');
        this.plateSizes = response.data.filter(plate => plate.available_quantity > 0);
        console.log('Fetched plate sizes:', this.plateSizes);
      } catch (error) {
        console.error('Error fetching plate sizes:', error);
      }
    },
    addJob() {
      this.jobs.push({
        job_name: '',
        jobId: '',
        plate_size_id: '',
        colour: '',
        quantity: 1,
        plates: 0,
        remark: '',
      });
    },
    deleteJob(index) {
      this.jobs.splice(index, 1);
    },
    calculatePlates(job) {
      job.plates = job.colour * job.quantity;
    },
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data;
      } catch (error) {
        console.error('Error fetching customers:', error);
      }
    },
    async fetchCustomerDetails() {
      const customer = this.customers.find(c => c.id === this.selectedCustomerId);
      if (customer) {
        this.customerDetails = {
          address: customer.address,
          contact_person: customer.contact_person,
          phone: customer.phone,
          mobile: customer.mobile,
          email: customer.email,
        };
      }
    },
    async generateChallanCode() {
      try {
        const response = await axios.get('/challan-code');
        this.challanCode = response.data.challan_code;
      } catch (error) {
        console.error('Error generating challan code:', error);
      }
    },
    async loadChallan(challanId) {
      try {
        const response = await axios.get(`/challans/${challanId}`);
        const challan = response.data;

        this.challanCode = challan.challan_code;
        this.date = challan.date;
        this.selectedCustomerId = challan.customer_id;

        // Fetch customer details after setting selectedCustomerId
        this.fetchCustomerDetails();

        this.jobs = challan.jobs.map(job => ({
          job_name: job.job_name,
          jobId: job.job_id,
          plate_size_id: job.plate_size_id,
          colour: job.colour,
          quantity: job.quantity,
          plates: job.plates,
          remark: job.remark || '',
        }));
        this.specialInstructions = challan.special_instructions || '';
        this.isEditing = true;
        this.challanId = challanId;
      } catch (error) {
        console.error('Error loading challan:', error);
      }
    },
    resetForm() {
      this.date = moment().format('YYYY-MM-DD');
      this.selectedCustomerId = null;
      this.jobs = [
        {
          job_name: '',
          jobId: '',
          plate_size_id: '',
          colour: '',
          quantity: 1,
          plates: 0,
          remark: '',
        },
      ];
      this.specialInstructions = '';
      this.isEditing = false;
      this.challanId = null;
      this.generateChallanCode();
    },
    cancelEdit() {
      this.$router.push('/challan-list');
    },
    getSizeDisplay(size) {
      const prefix = size.prefix ? `${size.prefix} ` : '';
      const base = `${size.length} x ${size.width}`;
      const dl = size.is_dl ? ' - DL' : '';
      const suffix = size.suffix ? ` ${size.suffix}` : '';
      return `${prefix}${base}${dl}${suffix}`.trim();
    },
  },
  mounted() {
    this.date = moment().format('YYYY-MM-DD');
    this.fetchCustomers();
    this.fetchPlateSizes();

    const challanId = this.$route.query.challanId;
    if (challanId) {
      this.loadChallan(challanId);
    } else {
      this.generateChallanCode();
    }
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
</style>