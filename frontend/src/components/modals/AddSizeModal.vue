<!-- filepath: frontend/src/components/modals/AddSizeModal.vue -->
<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg w-96 p-6">
      <h2 class="text-lg font-semibold mb-4">Add New Plate Size</h2>
      <form @submit.prevent="saveSize" class="space-y-3">
        <div>
          <label class="block text-sm">Length</label>
          <input v-model.number="length" type="number" required class="input" />
        </div>
        <div>
          <label class="block text-sm">Width</label>
          <input v-model.number="width" type="number" required class="input" />
        </div>
        <div>
          <label class="inline-flex items-center">
            <input type="checkbox" v-model="is_dl" class="mr-2" />
            <span class="text-sm">DL Type</span>
          </label>
        </div>
        <div>
          <label class="block text-sm">Minimum Quantity (optional)</label>
          <input v-model.number="min_quantity" type="number" min="0" class="input" />
        </div>

        <!-- New fields -->
        <div>
          <label class="block text-sm">Prefix (optional)</label>
          <input v-model="prefix" type="text" class="input" placeholder="e.g. PFX" />
        </div>
        <div>
          <label class="block text-sm">Suffix (optional)</label>
          <input v-model="suffix" type="text" class="input" placeholder="e.g. SFX" />
        </div>

        <div class="flex justify-end space-x-2 mt-4">
          <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
          <button :disabled="saving" type="submit" class="btn-primary">
            {{ saving ? 'Saving...' : 'Add Size' }}
          </button>
        </div>
        <p v-if="error" class="text-sm text-red-600 mt-2">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  data() {
    return {
      length: '',
      width: '',
      is_dl: false,
      min_quantity: null,
      prefix: '',
      suffix: '',
      saving: false,
      error: ''
    };
  },
  methods: {
    async saveSize() {
      this.error = '';
      if (!this.length || !this.width) {
        this.error = 'Length and width are required';
        return;
      }
      this.saving = true;
      try {
        const payload = {
          length: this.length,
          width: this.width,
          is_dl: this.is_dl,
          min_quantity: this.min_quantity || null,
          prefix: this.prefix || null,
          suffix: this.suffix || null
        };
        const res = await axios.post('/plate-sizes', payload);
        // Emit created size so parent can optionally append directly
        this.$emit('size-added', res.data);
        this.$emit('close');
      } catch (err) {
        console.error('Error adding size:', err);
        this.error = err.response?.data?.message || 'Failed to add size';
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>

<style scoped>
.input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
}
.btn-primary {
  background: #2563eb;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}
.btn-secondary {
  background: #f3f4f6;
  color: #111827;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}
</style>