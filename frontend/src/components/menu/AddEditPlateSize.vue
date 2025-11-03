<template>
  <div class="plate-size p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Plate Size Management</h1>
    <form @submit.prevent="addPlateSize" class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="length" class="block text-sm font-medium text-gray-700">Length</label>
      </div>
      <div class="col-span-2">
        <input
          type="number"
          id="length"
          v-model="length"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="width" class="block text-sm font-medium text-gray-700">Width</label>
      </div>
      <div class="col-span-2">
        <input
          type="number"
          id="width"
          v-model="width"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="min_quantity" class="block text-sm font-medium text-gray-700">Minimum Quantity</label>
      </div>
      <div class="col-span-2">
        <input
          type="number"
          id="min_quantity"
          v-model="min_quantity"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>

      <div class="col-span-1">
        <label for="prefix" class="block text-sm font-medium text-gray-700">Prefix</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="prefix"
          v-model="prefix"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Optional prefix for plate"
        />
      </div>

      <div class="col-span-1">
        <label for="suffix" class="block text-sm font-medium text-gray-700">Suffix</label>
      </div>
      <div class="col-span-2">
        <input
          type="text"
          id="suffix"
          v-model="suffix"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Optional suffix for plate"
        />
      </div>

      <div class="col-span-1">
        <label for="is_dl" class="block text-sm font-medium text-gray-700">DL Type</label>
      </div>
      <div class="col-span-2">
        <input
          type="checkbox"
          id="is_dl"
          v-model="is_dl"
          class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <span class="ml-2 text-sm text-gray-600">This is a DL type plate</span>
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

    <table class="table mt-6">
      <thead>
        <tr>
          <th>Length</th>
          <th>Width</th>
          <th>Minimum Quantity</th>
          <th>Prefix</th>
          <th>Suffix</th>
          <th>Type</th>
          <th v-if="userRole === 'admin'">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(plateSize, index) in plateSizes" :key="index">
          <td>{{ plateSize.length }}</td>
          <td>{{ plateSize.width }}</td>
          <td>{{ plateSize.min_quantity || 'N/A' }}</td>
          <td>{{ plateSize.prefix || '' }}</td>
          <td>{{ plateSize.suffix || '' }}</td>
          <td>{{ plateSize.is_dl ? 'DL Type' : 'Standard' }}</td>
          <td v-if="userRole === 'admin'">
            <button class="btn-edit" @click="editPlateSize(index)">Edit</button>
            <button class="btn-danger" @click="deletePlateSize(plateSize.id)">Delete</button>
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
      length: '',
      width: '',
      min_quantity: 20,
      is_dl: false,
      prefix: '',
      suffix: '',
      plateSizes: [],
      saveButtonText: 'Add',
      plateSizeId: '',
      userRole: '',
    };
  },
  methods: {
    async fetchPlateSizes() {
      try {
        const response = await axios.get('/plate-sizes');
        this.plateSizes = response.data;
      } catch (error) {
        console.error('Error fetching plate sizes:', error);
      }
    },
    async addPlateSize() {
      // Check for duplicate plate size
      if (this.isDuplicatePlateSize()) {
        if (this.is_dl) {
          alert(`A plate size of ${this.length} x ${this.width} with DL type enabled already exists.`);
        } else {
          alert(`A plate size of ${this.length} x ${this.width} already exists.`);
        }
        return;
      }

      const plateSize = {
        length: this.length,
        width: this.width,
        min_quantity: this.min_quantity || null,
        is_dl: this.is_dl,
        prefix: this.prefix,
        suffix: this.suffix
      };

      try {
        if (this.saveButtonText === 'Save') {
          const response = await axios.put(`/plate-sizes/${this.plateSizeId}`, plateSize);
          const index = this.plateSizes.findIndex(p => p.id === this.plateSizeId);
          if (index !== -1) {
            this.plateSizes.splice(index, 1, response.data);
          } else {
            // If not found locally, refresh the list
            await this.fetchPlateSizes();
          }
        } else {
          const response = await axios.post('/plate-sizes', plateSize);
          // If API returns newly created plate, push it; otherwise refresh
          if (response && response.data && response.data.id) {
            this.plateSizes.push(response.data);
          } else {
            await this.fetchPlateSizes();
          }
        }
        this.resetForm();
        await this.fetchPlateSizes(); // Refresh the plate size list to keep UI consistent
      } catch (error) {
        console.error('Error saving plate size:', error);
      }
    },
    async deletePlateSize(id) {
      if (!confirm('Are you sure you want to delete this plate size? This action cannot be undone.')) {
        return;
      }
      try {
        await axios.delete(`/plate-sizes/${id}`);
        // Refresh list after successful delete
        await this.fetchPlateSizes();
      } catch (error) {
        console.error('Error deleting plate size:', error);
        const msg = error.response?.data?.message || 'Failed to delete plate size';
        alert(msg);
      }
    },
    editPlateSize(index) {
      const plateSize = this.plateSizes[index];
      this.length = plateSize.length;
      this.width = plateSize.width;
      this.min_quantity = plateSize.min_quantity;
      this.is_dl = plateSize.is_dl;
      this.prefix = plateSize.prefix || '';
      this.suffix = plateSize.suffix || '';
      this.saveButtonText = 'Save';
      this.plateSizeId = plateSize.id;

      // Scroll to top of the form so user can edit immediately
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
      this.length = '';
      this.width = '';
      this.min_quantity = 20;
      this.is_dl = false;
      this.prefix = '';
      this.suffix = '';
      this.saveButtonText = 'Add';
      this.plateSizeId = '';
    },
    isDuplicatePlateSize() {
      // When editing, ignore the current plate being edited
      return this.plateSizes.some(
        plate =>
          plate.id !== this.plateSizeId &&
          (
            ((plate.length === this.length && plate.width === this.width) ||
            (plate.length === this.width && plate.width === this.length))
          ) &&
          plate.is_dl === this.is_dl
      );
    },
  },
  mounted() {
    this.userRole = this.$store.state.user.role;
    this.fetchPlateSizes();
  },
};
</script>

<style scoped>
/* Add any additional styles here */
</style>