<!-- filepath: frontend/src/components/menu/WastePlates.vue -->
<template>
  <div class="waste-plates p-6 bg-gray-50 rounded-lg shadow-md" v-if="wastePlates">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Waste Plates</h1>
    <form @submit.prevent="addWastePlate" class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
      </div>
      <div class="col-span-2">
        <input type="date" id="date" v-model="date"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required />
      </div>

      <div class="col-span-1">
        <label for="size" class="block text-sm font-medium text-gray-700">Size</label>
      </div>
      <div class="col-span-1">
        <select id="size" v-model="selectedSize"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required>
          <option v-for="size in sizes" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </div>
      <div class="col-span-1">
        <button type="button" @click="showAddSizeModal = true" class="btn-add">
          Add New Size
        </button>
      </div>

      <div class="col-span-1">
        <label for="quantity" class="block text-sm font-medium text-gray-700">Quantity</label>
      </div>
      <div class="col-span-2">
        <input type="number" id="quantity" v-model="quantity" :max="availablePlates" min="1"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required />
      </div>

      <div class="col-span-1">
        <label for="availablePlates" class="block text-sm font-medium text-gray-700">Available Plates</label>
      </div>
      <div class="col-span-2">
        <span class="block text-sm font-medium text-gray-700">{{ availablePlates }}</span>
      </div>

      <div class="col-span-3 flex justify-end">
        <button type="submit" class="btn-primary">
          Add Waste Plate
        </button>
      </div>
    </form>

    <table class="table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Size</th>
          <th>Quantity</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(wastePlate, index) in wastePlates" :key="index">
          <td>{{ formatDate(wastePlate.waste_date) }}</td>
          <td>{{ getSizeName(wastePlate.size_id) }}</td>
          <td>{{ wastePlate.quantity_wasted }}</td>
          <td>
            <button v-if="userRole === 'admin'" @click="deleteWastePlate(wastePlate.id)" class="btn-danger">
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <AddSizeModal v-if="showAddSizeModal" @close="showAddSizeModal = false" @size-added="fetchSizes" />
  </div>
</template>

<script>
import axios from '../../axios';
import AddSizeModal from '../modals/AddSizeModal.vue';

export default {
  components: {
    AddSizeModal,
  },
  data() {
    return {
      date: new Date().toISOString().split('T')[0],
      wastePlates: [],
      sizes: [],
      sizesData: null,
      selectedSize: '',
      quantity: '',
      availablePlates: 0,
      showAddSizeModal: false,
      userRole: '', // Add userRole to the data
    };
  },
  methods: {
    async fetchWastePlates() {
      try {
        const response = await axios.get('/waste-plates');
        this.wastePlates = response.data.sort((a, b) => {
          const dateComparison = new Date(b.waste_date) - new Date(a.waste_date);
          if (dateComparison !== 0) {
        return dateComparison;
          }
          return b.id - a.id;
        });
      } catch (error) {
        console.error('Error fetching waste plates:', error);
      }
    },
    async fetchSizes() {
      try {
        const response = await axios.get('/plate-sizes');
        this.sizesData = response.data;
        this.sizes = response.data.map(size => {
          let sizeText = `${size.length} x ${size.width}`;
          if (size.is_dl) {
            sizeText += ' - DL';
          }
          return sizeText;
        });
      } catch (error) {
        console.error('Error fetching sizes:', error);
      }
    },
    async fetchAvailablePlates() {
      const selectedSizeId = this.sizesData.find(size => `${size.length} x ${size.width}${size.is_dl ? ' - DL' : ''}` === this.selectedSize)?.id || '';
      try {
        const response = await axios.get('/plate-summary', {
          params: {
            size_id: selectedSizeId,
          },
        });
        this.availablePlates = response.data[0]?.available_quantity || 0;
      } catch (error) {
        console.error('Error fetching available plates:', error);
      }
    },
    async addWastePlate() {
      const selectedSizeObj = this.sizesData.find(size => `${size.length} x ${size.width}${size.is_dl ? ' - DL' : ''}` === this.selectedSize);
      const newWastePlate = {
        waste_date: this.date,
        size_id: selectedSizeObj.id,
        quantity_wasted: this.quantity,
      };

      try {
        const response = await axios.post('/waste-plates', newWastePlate);
        this.wastePlates.push(response.data);
        this.quantity = '';
        this.date = new Date().toISOString().split('T')[0];
        this.selectedSize = '';
        this.availablePlates = 0;
      } catch (error) {
        console.error('Error adding waste plate:', error);
      }
    },
    async deleteWastePlate(id) {
      try {
        await axios.delete(`/waste-plates/${id}`);
        this.wastePlates = this.wastePlates.filter(wastePlate => wastePlate.id !== id);
      } catch (error) {
        console.error('Error deleting waste plate:', error);
      }
    },
    formatDate(date) {
      const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(date).toLocaleDateString('en-US', options);
    },
    getSizeName(sizeId) {
      const size = this.sizesData.find(size => size.id === sizeId);
      if (!size) return '';
      let sizeText = `${size.length} x ${size.width}`;
      if (size.is_dl) {
      sizeText += ' - DL';
      }
      return sizeText;
    },
  },
  watch: {
    selectedSize: 'fetchAvailablePlates',
  },
  mounted() {
    this.userRole = this.$store.state.user.role; // Fetch userRole from Vuex store
    this.fetchSizes();
    this.fetchWastePlates();
  },
};
</script>

<style scoped>
/* Add any styles here */
</style>