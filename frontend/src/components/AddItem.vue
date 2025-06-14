<template>
  <div class="container mx-auto p-4">
    <div class="flex justify-center">
      <div class="w-full max-w-sm">
        <form @submit.prevent="addItem" class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
          <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
              Item Name
            </label>
            <input v-model="name" id="name" type="text" placeholder="Item Name" required
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>
          <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="quantity">
              Quantity
            </label>
            <input v-model="quantity" id="quantity" type="number" placeholder="Quantity" required
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>
          <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="price">
              Price
            </label>
            <input v-model="price" id="price" type="number" step="0.01" placeholder="Price" required
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>
          <div class="flex items-center justify-between">
            <button type="submit"
              class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
              Add Item
            </button>
          </div>
          <div v-if="error" class="mt-4 text-red-500 text-xs italic">
            {{ error }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  data() {
    return {
      name: '',
      quantity: '',
      price: '',
      error: null
    };
  },
  methods: {
    ...mapActions(['addItem']),
    async addItem() {
      try {
        await this.addItem({ name: this.name, quantity: this.quantity, price: this.price });
        this.$router.push('/inventory');
      } catch (err) {
        this.error = err.message;
      }
    }
  }
};
</script>