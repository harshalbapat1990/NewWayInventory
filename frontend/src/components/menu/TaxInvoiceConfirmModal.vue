<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 shadow-lg w-2/3 max-h-[85vh] overflow-y-auto">
      <h2 class="text-xl font-bold mb-4">Generate Tax Invoice</h2>
      <p class="mb-4">You are about to generate a tax invoice with the following details:</p>

      <div class="mb-6 bg-gray-100 p-4 rounded">
        <div class="grid grid-cols-2 gap-2">
          <div class="font-semibold">Invoice Number:</div>
          <div class="flex items-center">
            <span class="p-1 bg-gray-200 border border-gray-300 rounded-l">{{ invoicePrefix }}</span>
            <input :value="invoiceSequence" type="text" class="w-1/4 p-1 border border-gray-300 rounded-r"
              maxlength="5" :class="{ 'border-red-500': !isValidSequence }"
              @input="$emit('update:invoice-sequence', $event.target.value)" />
          </div>
          <div v-if="!isValidSequence" class="col-span-2 text-red-500 text-sm mt-1">
            Invoice sequence must be a number
          </div>
          <div class="font-semibold">Invoice Date:</div>
          <div>
            <input type="date" :value="invoiceDate" class="w-full p-1 border border-gray-300 rounded"
              @input="$emit('update:invoice-date', $event.target.value)" />
          </div>
          <div class="font-semibold">Customer:</div>
          <div>{{ customer?.company_name }}</div>
          <div class="font-semibold">Date Range:</div>
          <div>{{ startDate }} to {{ endDate }}</div>
        </div>
      </div>

      <div class="mb-6">
        <h3 class="text-lg font-semibold mb-2">Summary</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full border border-gray-300">
            <thead>
              <tr class="bg-gray-100">
                <th class="px-2 py-1 border border-gray-300">Size</th>
                <th class="px-2 py-1 border border-gray-300">Colour</th>
                <th class="px-2 py-1 border border-gray-300">Challan No</th>
                <th class="px-2 py-1 border border-gray-300">Job ID</th>
                <th class="px-2 py-1 border border-gray-300">Sets</th>
                <th class="px-2 py-1 border border-gray-300">Job Name</th>
                <th class="px-2 py-1 border border-gray-300">Remark</th>
                <th class="px-2 py-1 border border-gray-300">Rate (₹)</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(plateGroup, plateIndex) in groupedChallans" :key="plateIndex">
                <template v-for="(colourGroup, colourIndex) in plateGroup.colours" :key="colourIndex">
                  <template v-for="(challanGroup, challanIndex) in colourGroup.challans" :key="challanIndex">
                    <template v-for="(job, jobIndex) in challanGroup.jobs" :key="jobIndex">
                      <tr>
                        <td class="px-2 py-1 border border-gray-300">{{ plateGroup.size }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ colourGroup.colour }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ challanGroup.challan_no }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ job.job_id }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ job.quantity }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ job.job_name }}</td>
                        <td class="px-2 py-1 border border-gray-300">{{ job.remark }}</td>
                        <td class="px-2 py-1 border border-gray-300">
                          <input type="number" min="0" step="0.01" class="w-20 border border-gray-300 rounded px-1 py-0.5"
                            :value="findJobRateBinding(plateGroup.size, colourGroup.colour, job.job_id)"
                            @input="$emit('rate-input', { size: plateGroup.size, colour: colourGroup.colour, jobId: job.job_id, value: $event.target.value })" />
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <div class="flex justify-end space-x-4">
        <button @click="$emit('cancel')" class="btn-secondary">Cancel</button>
        <button @click="$emit('confirm')" class="btn-primary" :disabled="!isValidInvoiceNumber">
          Confirm &amp; Print
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaxInvoiceConfirmModal',
  props: {
    invoicePrefix: { type: String, default: '' },
    invoiceSequence: { type: String, default: '' },
    invoiceDate: { type: String, default: '' },
    customer: { type: Object, default: null },
    startDate: { type: String, default: '' },
    endDate: { type: String, default: '' },
    groupedChallans: { type: Array, default: () => [] },
    isValidSequence: { type: Boolean, default: true },
    isValidInvoiceNumber: { type: Boolean, default: false },
    findJobRateBinding: { type: Function, required: true },
  },
  emits: ['cancel', 'confirm', 'rate-input', 'update:invoice-sequence', 'update:invoice-date'],
};
</script>
