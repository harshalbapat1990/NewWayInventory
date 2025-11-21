<template>
  <div class="available-plates p-6 bg-gray-50 rounded-lg shadow-md" v-if="availablePlates.length">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Available Plates</h1>
    <div class="flex justify-end mb-4">
      <button @click="printTable" class="btn-primary">Print Table</button>
    </div>
    <table class="table">
      <thead>
        <tr>
          <th>Size</th>
          <th>Available Quantity</th>
          <th>Min Quantity</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(plate, index) in availablePlates"
          :key="index"
          :class="{ 'low-quantity': plate.available_quantity < plate.min_quantity }"
        >
          <td class="text-right">{{ getSizeName(plate.size_id) }}</td>
          <td>{{ plate.available_quantity }}</td>
          <td>
            <div v-if="editingIndex === index">
              <input
                type="number"
                v-model="plate.min_quantity"
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            <div v-else>
              {{ plate.min_quantity }}
            </div>
          </td>
          <td>
            <button
              v-if="editingIndex === index"
              @click="saveMinQuantity(plate)"
              class="btn-primary"
            >
              Save
            </button>
            <button
              v-else
              @click="editingIndex = index"
              class="btn-add"
            >
              Edit Min Qty
            </button>
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
      availablePlates: [],
      sizes: [],
      editingIndex: null, // Track the row being edited
    };
  },
  methods: {
    async fetchAvailablePlates() {
      try {
        const response = await axios.get('/plate-summary');
        this.availablePlates = response.data;
      } catch (error) {
        console.error('Error fetching available plates:', error);
      }
    },
    async fetchSizes() {
      try {
        const response = await axios.get('/plate-sizes');
        this.sizes = response.data;
      } catch (error) {
        console.error('Error fetching sizes:', error);
      }
    },
    getSizeName(sizeId) {
      const size = this.sizes.find(size => size.id === sizeId);
      if (!size) return '';
      const prefix = size.prefix ? `${size.prefix} ` : '';
      const base = `${size.length} x ${size.width}`;
      const dl = size.is_dl ? ' - DL' : '';
      const suffix = size.suffix ? ` ${size.suffix}` : '';
      return `${prefix}${base}${dl}${suffix}`.trim();
    },
    async saveMinQuantity(plate) {
      try {
        const response = await axios.put(`/plate-sizes/${plate.size_id}/min-quantity`, {
          min_quantity: plate.min_quantity,
        });
        if (response.status === 200) {
          this.editingIndex = null; // Exit edit mode
          alert('Minimum quantity updated successfully!');
        } else {
          alert('Failed to update minimum quantity.');
        }
      } catch (error) {
        console.error('Error updating minimum quantity:', error);
        alert('Failed to update minimum quantity.');
      }
    },
    async printTable() {
      try {
        const headers = ['Size', 'Available Quantity', 'Min Quantity'];

        // Filter rows where available_quantity is greater than 0
        const rows = this.availablePlates
          .filter(plate => plate.available_quantity > 0)
          .map(plate => [
            this.getSizeName(plate.size_id),
            plate.available_quantity,
            plate.min_quantity,
          ]);

        // Check if there are rows to print
        if (rows.length === 0) {
          alert('No plates available to print.');
          return;
        }

        const response = await axios.post(
          '/print-data',
          {
            subtitle: 'Available Plate Summary',
            headers: headers,
            rows: rows,
          },
          { responseType: 'blob' }
        );

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'available_plates.pdf');
        document.body.appendChild(link);
        link.click();
      } catch (error) {
        console.error('Error printing table:', error);
      }
    },
  },
  mounted() {
    this.fetchSizes();
    this.fetchAvailablePlates();
  },
};
</script>

<style scoped>
.low-quantity {
  background-color: #ffcccc; /* Light red background for low quantity */
}
</style>