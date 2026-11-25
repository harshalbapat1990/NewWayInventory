<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/3">
      <h2 class="text-xl font-semibold mb-4">Export Invoices to Excel</h2>
      <div class="mb-4">
        <label for="export-date" class="block text-sm font-medium text-gray-700 mb-1">Select Date</label>
        <input id="export-date" :value="exportDate" type="date"
          class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          required @input="$emit('update:export-date', $event.target.value)" />
      </div>
      <div class="mb-4">
        <label for="export-invoice-number" class="block text-sm font-medium text-gray-700 mb-1">
          Export Specific Invoice Number
        </label>
        <input id="export-invoice-number" :value="exportInvoiceNumber" type="text"
          class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter Invoice Number" @input="$emit('update:export-invoice-number', $event.target.value)" />
      </div>
      <div class="mb-4">
        <p class="text-sm text-gray-600">
          This will export all invoices created on the selected date in Tally-compatible format.
        </p>
      </div>
      <div class="flex justify-end space-x-3 mt-6">
        <button @click="$emit('close')" class="btn-secondary">Cancel</button>
        <button @click="$emit('export-date')" class="btn-primary" :disabled="!exportDate || isExporting">
          {{ isExporting ? 'Exporting...' : 'Export' }}
        </button>
        <button @click="$emit('export-invoice')" class="btn-primary"
          :disabled="!exportInvoiceNumber || isExporting">
          {{ isExporting ? 'Exporting...' : 'Export Specific Invoice' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InvoiceExportModal',
  props: {
    exportDate: { type: String, default: '' },
    exportInvoiceNumber: { type: String, default: '' },
    isExporting: { type: Boolean, default: false },
  },
  emits: ['close', 'export-date', 'export-invoice', 'update:export-date', 'update:export-invoice-number'],
};
</script>
