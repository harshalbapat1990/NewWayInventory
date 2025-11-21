<template>
  <div class="purchase p-6 bg-gray-50 rounded-lg shadow-md" v-if="purchases">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Purchase Data</h1>
    <form @submit.prevent="addPurchase" class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
      </div>
      <div class="col-span-2">
        <input
          type="date"
          id="date"
          v-model="date"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        />
      </div>

      <div class="col-span-1">
        <label for="size" class="block text-sm font-medium text-gray-700">Size</label>
      </div>
      <div class="col-span-1">
        <ComboBox
          :options="sizes"
          v-model="selectedSize"
          enable-search
        />
      </div>
      <div class="col-span-1">
        <button
          type="button"
          @click="showAddSizeModal = true"
          class="btn-add"
        >
          Add New Size
        </button>
      </div>
      <div class="col-span-1">
        <label for="quantity" class="block text-sm font-medium text-gray-700">Quantity</label>
      </div>
      <div class="col-span-2">
        <input
          type="number"
          id="quantity"
          v-model="quantity"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          min="1"
          step="1"
          required
        />
      </div>

      <div class="col-span-3 flex justify-end">
        <button
          type="submit"
          class="btn-primary"
        >
          Add Purchase
        </button>
      </div>
    </form>

    <table class="table">
      <thead>
        <tr>
          <th>Purchase Date</th>
          <th>Size</th>
          <th>Quantity</th>
          <th 
            v-if="userRole === 'admin'">
            Actions
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(purchase, index) in purchases" :key="index">
          <td>{{ formatDate(purchase.date) }}</td>
          <td>{{ getSizeName(purchase.size_id) }}</td>
          <td>{{ purchase.quantity }}</td>
          <td
            v-if="userRole === 'admin'">
            <button              
              @click="deletePurchase(purchase.id)"
              class="btn-danger"
            >
              <TrashIcon class="h-5 w-5" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <AddSizeModal
      v-if="showAddSizeModal"
      @close="showAddSizeModal = false"
      @size-added="fetchSizes"
    />
  </div>
</template>

<script>
import axios from '../../axios';
import AddSizeModal from '../modals/AddSizeModal.vue';
import ComboBox from '../common/ComboBox.vue';
import { TrashIcon } from '@heroicons/vue/24/outline';

export default {
  components: {
    AddSizeModal,
    ComboBox,
    TrashIcon,
  },
  data() {
    return {
      item: '',
      quantity: '',
      date: new Date().toISOString().split('T')[0],
      purchases: [],
      sizes: [],
      sizesData: null,
      selectedSize: '',
      showAddSizeModal: false,
      userRole: '',
    };
  },
  methods: {
    async fetchPurchases() {
      try {
        const response = await axios.get('/purchases');
        this.purchases = response.data.sort((a, b) => {
          const dateComparison = new Date(b.date) - new Date(a.date);
          if (dateComparison !== 0) {
            return dateComparison;
          }
          return b.id - a.id;
        });
      } catch (error) {
        console.error('Error fetching purchases:', error);
      }
    },
    async fetchSizes(newSize = null) {
      try {
        const response = await axios.get('/plate-sizes');
        this.sizesData = response.data;
        this.sizes = response.data.map(size => {
          let sizeText = `${size.length} x ${size.width}`;
          if (size.is_dl) sizeText += ' - DL';
          const prefix = size.prefix ? `${size.prefix} ` : '';
          const suffix = size.suffix ? ` ${size.suffix}` : '';
          return `${prefix}${sizeText}${suffix}`.trim();
        });

        if (newSize) {
          const newSizeText = `${newSize.prefix ? newSize.prefix + ' ' : ''}${newSize.length} x ${newSize.width}${newSize.is_dl ? ' - DL' : ''}${newSize.suffix ? ' ' + newSize.suffix : ''}`;
          // don't push — server response already contains the new size. just select it.
          this.selectedSize = newSizeText;
        }
      } catch (error) {
        console.error('Error fetching sizes:', error);
      }
    },
    async addPurchase() {
      // Find selected size by comparing the full display string including prefix/suffix/DL
      const selectedSizeObj = this.sizesData.find(size => {
        const prefix = size.prefix ? `${size.prefix} ` : '';
        const suffix = size.suffix ? ` ${size.suffix}` : '';
        const sizeText = `${prefix}${size.length} x ${size.width}${size.is_dl ? ' - DL' : ''}${suffix}`.trim();
        return sizeText === (this.selectedSize || '').trim();
      });

      if (!selectedSizeObj) {
        alert('Please select a valid size.');
        return;
      }

      const newPurchase = {
        date: this.date,
        size_id: selectedSizeObj.id,
        quantity: this.quantity,
      };

      try {
        await axios.post('/purchases', newPurchase);
        // Refresh the purchases table from server to ensure consistency
        await this.fetchPurchases();
        // Reset form
        this.quantity = '';
        this.date = new Date().toISOString().split('T')[0];
        this.selectedSize = '';
      } catch (error) {
        console.error('Error adding purchase:', error);
      }
    },

    async deletePurchase(id) {
      if (!confirm('Are you sure you want to delete this purchase?')) return;
      try {
        await axios.delete(`/purchases/${id}`);
        // Refresh the purchases table from server so UI stays in sync
        await this.fetchPurchases();
      } catch (error) {
        console.error('Error deleting purchase:', error);
      }
    },
    formatDate(date) {
      const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(date).toLocaleDateString('en-US', options);
    },
    getSizeName(sizeId) {
      const size = this.sizesData.find(size => size.id === sizeId);
      if (!size) {
        return 'Unknown Size';
      }
      let sizeText = `${size.length} x ${size.width}`;
      if (size.is_dl) {
        sizeText += ' - DL';
      }
      const prefix = size.prefix ? `${size.prefix} ` : '';
      const suffix = size.suffix ? ` ${size.suffix}` : '';
      return `${prefix}${sizeText}${suffix}`.trim();
    },
  },
  async mounted() {
    this.userRole = this.$store.state.user.role;
    await this.fetchSizes();
    await this.fetchPurchases();
  },
};
</script>