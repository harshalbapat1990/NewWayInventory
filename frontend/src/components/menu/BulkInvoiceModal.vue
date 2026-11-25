<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-2/3 max-h-[80vh] overflow-y-auto">
      <h2 class="text-xl font-bold mb-4">Generate Invoices for Selected Customers</h2>

      <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
          <div class="font-semibold mb-2">Start Date:</div>
          <input type="date" :value="startDate" class="w-full p-2 border border-gray-300 rounded"
            @input="$emit('update:start-date', $event.target.value)" />
        </div>
        <div>
          <div class="font-semibold mb-2">End Date:</div>
          <input type="date" :value="endDate" class="w-full p-2 border border-gray-300 rounded"
            @input="$emit('update:end-date', $event.target.value)" />
        </div>
        <div>
          <div class="font-semibold mb-2">Invoice Date:</div>
          <input type="date" :value="invoiceDate" class="w-full p-2 border border-gray-300 rounded"
            @input="$emit('update:invoice-date', $event.target.value)" />
        </div>
        <div>
          <div class="font-semibold mb-2">Starting Invoice Number:</div>
          <div class="flex items-center">
            <span class="p-2 bg-gray-200 border border-gray-300 rounded-l">{{ invoicePrefix }}</span>
            <input :value="invoiceSequence" type="text" class="w-1/4 p-2 border border-gray-300 rounded-r"
              maxlength="5" :class="{ 'border-red-500': !isValidSequence }"
              @input="$emit('update:invoice-sequence', $event.target.value)" />
          </div>
        </div>
      </div>

      <div class="mb-6">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-semibold">Select Customers</h3>
          <div class="space-x-2">
            <button @click="$emit('select-all')" class="text-sm text-blue-600 hover:text-blue-800">Select All</button>
            <span class="text-gray-400">|</span>
            <button @click="$emit('deselect-all')" class="text-sm text-blue-600 hover:text-blue-800">Deselect All</button>
          </div>
        </div>
        <div class="border border-gray-200 rounded max-h-60 overflow-y-auto p-2">
          <div v-for="customer in customers" :key="customer.id" class="flex items-center p-2 hover:bg-gray-50">
            <input type="checkbox" :id="'customer-' + customer.id"
              :checked="selectedCustomers.includes(customer.id)" class="h-4 w-4 text-blue-600 rounded border-gray-300"
              @change="toggleCustomer(customer.id, $event.target.checked)" />
            <label :for="'customer-' + customer.id" class="ml-2 cursor-pointer flex-1">
              {{ customer.company_name }}
            </label>
          </div>
        </div>
      </div>

      <div class="flex justify-end space-x-4">
        <button @click="$emit('close')" class="btn-secondary">Cancel</button>
        <button @click="$emit('generate')" class="btn-primary"
          :disabled="!isValidDateRange || !isValidInvoiceNumber || selectedCustomers.length === 0 || isGenerating">
          {{ isGenerating ? 'Generating...' : 'Generate Invoices' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BulkInvoiceModal',
  props: {
    startDate: { type: String, default: '' },
    endDate: { type: String, default: '' },
    invoiceDate: { type: String, default: '' },
    invoiceSequence: { type: String, default: '' },
    invoicePrefix: { type: String, default: '' },
    customers: { type: Array, default: () => [] },
    selectedCustomers: { type: Array, default: () => [] },
    isValidSequence: { type: Boolean, default: true },
    isValidDateRange: { type: Boolean, default: false },
    isValidInvoiceNumber: { type: Boolean, default: false },
    isGenerating: { type: Boolean, default: false },
  },
  emits: [
    'close', 'generate', 'select-all', 'deselect-all', 'update:start-date',
    'update:end-date', 'update:invoice-date', 'update:invoice-sequence', 'update:selected-customers',
  ],
  methods: {
    toggleCustomer(customerId, checked) {
      const selected = new Set(this.selectedCustomers);
      if (checked) selected.add(customerId);
      else selected.delete(customerId);
      this.$emit('update:selected-customers', [...selected]);
    },
  },
};
</script>
