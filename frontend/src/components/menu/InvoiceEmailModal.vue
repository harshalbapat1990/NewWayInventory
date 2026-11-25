<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/2">
      <h2 class="text-xl font-semibold mb-4">Email Invoice</h2>

      <div v-if="!customerEmail" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <strong>Error:</strong> This customer doesn't have an email address.
        <a @click="$emit('go-to-customer-edit')" class="text-blue-600 underline cursor-pointer">
          Update email address
        </a>
      </div>

      <div v-else>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Invoice</label>
          <div class="text-gray-800">{{ invoice?.invoice_number }}</div>
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Customer</label>
          <div class="text-gray-800">{{ customerName }}</div>
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Email To</label>
          <div class="text-gray-800">{{ customerEmail }}</div>
        </div>
        <div class="mb-4">
          <label for="email-subject" class="block text-sm font-medium text-gray-700 mb-1">Subject</label>
          <input id="email-subject" :value="emailData.subject" type="text"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            @input="updateField('subject', $event.target.value)" />
        </div>
        <div class="mb-4">
          <label for="email-message" class="block text-sm font-medium text-gray-700 mb-1">Message</label>
          <textarea id="email-message" :value="emailData.message" rows="9"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            @input="updateField('message', $event.target.value)"></textarea>
        </div>
        <div class="mb-4">
          <label class="inline-flex items-center">
            <input type="checkbox" :checked="emailData.includePdf" class="form-checkbox h-5 w-5 text-blue-600"
              @change="updateField('includePdf', $event.target.checked)">
            <span class="ml-2 text-gray-700">Attach invoice PDF</span>
          </label>
        </div>
        <div v-if="invoice?.summary_start_date && invoice?.summary_end_date" class="mb-4">
          <label class="inline-flex items-center">
            <input type="checkbox" :checked="emailData.includeSummaryPdf" class="form-checkbox h-5 w-5 text-blue-600"
              @change="updateField('includeSummaryPdf', $event.target.checked)">
            <span class="ml-2 text-gray-700">Attach customer summary PDF</span>
          </label>
        </div>
      </div>

      <div class="flex justify-end space-x-3 mt-6">
        <button @click="$emit('close')" class="btn-secondary">Cancel</button>
        <button @click="$emit('send')" class="btn-primary" :disabled="isSending || !customerEmail">
          {{ isSending ? 'Sending...' : 'Send Email' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InvoiceEmailModal',
  props: {
    invoice: { type: Object, default: null },
    customerName: { type: String, default: '' },
    customerEmail: { type: String, default: '' },
    emailData: { type: Object, required: true },
    isSending: { type: Boolean, default: false },
  },
  emits: ['close', 'send', 'go-to-customer-edit', 'update:email-data'],
  methods: {
    updateField(key, value) {
      this.$emit('update:email-data', { ...this.emailData, [key]: value });
    },
  },
};
</script>
