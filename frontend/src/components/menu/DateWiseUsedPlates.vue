<!-- filepath: frontend/src/components/menu/DateWiseUsedPlates.vue -->
<template>
  <div class="date-wise-used-plates p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Date Wise Used Plates</h1>
    <form @submit.prevent="filterPlates" novalidate class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="startDate" class="block text-sm font-medium text-gray-700">Start Date</label>
      </div>
      <div class="col-span-2">
        <input
          type="date"
          id="startDate"
          v-model="startDate"
          @change="filterPlates"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{ 'border-red-500': errors.startDate }"
          required
        />
        <p v-if="errors.startDate" class="text-red-500 text-sm mt-1">{{ errors.startDate }}</p>
      </div>

      <div class="col-span-1">
        <label for="endDate" class="block text-sm font-medium text-gray-700">End Date</label>
      </div>
      <div class="col-span-2">
        <input
          type="date"
          id="endDate"
          v-model="endDate"
          @change="filterPlates"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          :class="{ 'border-red-500': errors.endDate }"
          required
        />
        <p v-if="errors.endDate" class="text-red-500 text-sm mt-1">{{ errors.endDate }}</p>
      </div>

      <div class="col-span-3 flex justify-start space-x-4 mt-4">
        <button
          type="button"
          class="btn-soft"
          @click="setQuickDateRange('last7Days')"
        >
          Last 7 Days
        </button>
        <button
          type="button"
          class="btn-soft"
          @click="setQuickDateRange('pastMonth')"
        >
          Past Month
        </button>
        <button
          type="button"
          class="btn-soft"
          @click="setQuickDateRange('pastQuarter')"
        >
          Past Quarter
        </button>
        <button
          type="button"
          class="btn-soft"
          @click="setQuickDateRange('pastYear')"
        >
          Past Year
        </button>
        <button
          type="button"
          class="btn-soft"
          @click="setQuickDateRange('today')"
        >
          Today
        </button>
      </div>

      <div class="col-span-3 flex justify-end space-x-4">
        <button
          type="button"
          class="btn-print"
          @click="printPlates"
        >
          Print
        </button>
      </div>
    </form>

    <table class="table mt-6">
      <thead>
        <tr>
          <th>Plate Size</th>
          <th>Quantity</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(plate, index) in plateUsage" :key="index">
          <td>{{ plate.item }}</td>
          <td>{{ plate.quantity }}</td>
        </tr>
        <tr v-if="plateUsage.length === 0">
          <td colspan="2" class="text-center text-gray-500">No data available</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from '../../axios';
import { printDateWiseUsedPlates } from '../../utils/printDateWiseUsedPlates';

export default {
  data() {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);

    return {
      startDate: oneMonthAgo.toISOString().split('T')[0],
      endDate: today.toISOString().split('T')[0],
      plateUsage: [],
      errors: {}, // Object to store validation errors
    };
  },
  watch: {
    startDate(newVal, oldVal) {
      this.filterPlates();
    },
    endDate(newVal, oldVal) {
      this.filterPlates();
    },
  },
  mounted() {
    this.filterPlates();
  },
  methods: {
    validateForm() {
      this.errors = {};

      if (!this.startDate) {
        this.errors.startDate = 'Start Date is required.';
      }
      if (!this.endDate) {
        this.errors.endDate = 'End Date is required.';
      } else if (this.startDate > this.endDate) {
        this.errors.endDate = 'End Date must be after Start Date.';
      }

      return Object.keys(this.errors).length === 0;
    },
    async filterPlates() {
      if (!this.validateForm()) {
        return;
      }

      try {
        const response = await axios.get('/used-plates', {
          params: { start_date: this.startDate, end_date: this.endDate },
        });

        // Group data by plate size
        const groupedData = response.data.reduce((acc, plate) => {
          if (!acc[plate.item]) {
            acc[plate.item] = 0;
          }
          acc[plate.item] += plate.quantity;
          return acc;
        }, {});

        // Transform grouped data into an array
        this.plateUsage = Object.entries(groupedData).map(([item, quantity]) => ({ item, quantity }));
      } catch (error) {
        console.error('Error fetching plate usage:', error);
        alert('Failed to fetch data. Please check the console for more details.');
      }
    },
    resetForm() {
      const today = new Date();
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(today.getMonth() - 1);

      this.startDate = oneMonthAgo.toISOString().split('T')[0];
      this.endDate = today.toISOString().split('T')[0];
      this.plateUsage = [];
      this.errors = {};
    },
    printPlates() {
      if (this.plateUsage.length === 0) {
        alert('No data available to print.');
        return;
      }

      printDateWiseUsedPlates(this.plateUsage, this.startDate, this.endDate);
    },
    setQuickDateRange(range) {
      const today = new Date();
      let startDate;
      switch (range) {
        case 'last7Days':
          startDate = new Date(today);
          startDate.setDate(today.getDate() - 7);
          break;
        case 'pastMonth':
          startDate = new Date(today);
          startDate.setMonth(today.getMonth() - 1);
          break;
        case 'pastQuarter':
          startDate = new Date(today);
          startDate.setMonth(today.getMonth() - 3);
          break;
        case 'pastYear':
          startDate = new Date(today);
          startDate.setFullYear(today.getFullYear() - 1);
          break;
        case 'today':
          startDate = new Date(today);
          break;
        default:
          startDate = new Date(today);
      }
      this.startDate = startDate.toISOString().split('T')[0];
      this.endDate = today.toISOString().split('T')[0];
    },
  },
};
</script>

<style scoped>
/* Add any additional styles here */
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.table th {
  background-color: #f4f4f4;
  text-align: left;
}
</style>