<template>
  <div class="customer-summary p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Customer Summary</h1>
    <form @submit.prevent="filterSummary" class="grid grid-cols-3 gap-6 bg-white p-6 rounded-lg shadow-md">
      <div class="col-span-1">
        <label for="customer" class="block text-sm font-medium text-gray-700">Select Customer</label>
      </div>
      <div class="col-span-2">
        <select id="customer" v-model="selectedCustomerId"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.company_name }}
          </option>
        </select>
      </div>

      <div class="col-span-1">
        <label for="startDate" class="block text-sm font-medium text-gray-700">Start Date</label>
      </div>
      <div class="col-span-2">
        <input type="date" id="startDate" v-model="startDate"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required />
      </div>

      <div class="col-span-1">
        <label for="endDate" class="block text-sm font-medium text-gray-700">End Date</label>
      </div>
      <div class="col-span-2">
        <input type="date" id="endDate" v-model="endDate"
          class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required />
      </div>

      <div class="col-span-3 flex justify-end">
        <div class="flex-1 flex justify-start space-x-4">
          <button 
            type="button" 
            class="btn-soft" 
            @click="setLastWeekDates"
          >
            Last Week
          </button>
          <button 
            v-if="userRole === 'accountant'"
            type="button" 
            class="btn-secondary" 
            @click="openBulkInvoiceModal"
          >
            Generate All Invoices
          </button>
        </div>
        <button type="submit" class="btn-primary">
          Generate Summary
        </button>
        <button type="button" class="btn-print ml-4" @click="printSummary">
          Print Summary
        </button>
        <button 
          v-if="userRole === 'accountant'" 
          type="button" 
          class="btn-secondary ml-4" 
          @click="printTaxInvoice"
        >
          Print Tax Invoice
        </button>
      </div>
    </form>

    <!-- Modal for Tax Invoice Number Confirmation -->
    <div v-if="showInvoiceModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 shadow-lg w-2/3 max-h-[85vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4">Generate Tax Invoice</h2>
        <p class="mb-4">You are about to generate a tax invoice with the following details:</p>

        <div class="mb-6 bg-gray-100 p-4 rounded">
          <div class="grid grid-cols-2 gap-2">
            <div class="font-semibold">Invoice Number:</div>
            <div class="flex items-center">
              <span class="p-1 bg-gray-200 border border-gray-300 rounded-l">{{ invoicePrefix }}</span>
              <input 
                v-model="invoiceSequence"
                type="text" 
                class="w-1/4 p-1 border border-gray-300 rounded-r"
                maxlength="5"
                :class="{'border-red-500': !isValidSequence}"
              />
            </div>
            <div v-if="!isValidSequence" class="col-span-2 text-red-500 text-sm mt-1">
              Invoice sequence must be a number
            </div>
            <div class="font-semibold">Invoice Date:</div>
            <div>
              <input 
                type="date" 
                v-model="previewInvoiceData.invoice_date"
                class="w-full p-1 border border-gray-300 rounded"
              />
            </div>
            <div class="font-semibold">Customer:</div>
            <div>{{ selectedCustomer.company_name }}</div>
            <div class="font-semibold">Date Range:</div>
            <div>{{ startDate }} to {{ endDate }}</div>
          </div>
        </div>

        <!-- Summary Table (as in summary, with rate for each item) -->
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
                            <!-- Editable rate input -->
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              class="w-20 border border-gray-300 rounded px-1 py-0.5"
                              :value="findJobRateBinding(plateGroup.size, colourGroup.colour, job.job_id)"
                              @input="onJobRateInput(plateGroup.size, colourGroup.colour, job.job_id, $event.target.value)"
                            />
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
          <button @click="cancelInvoiceGeneration" class="btn-secondary">
            Cancel
          </button>
          <button 
            @click="confirmInvoiceGeneration" 
            class="btn-primary"
            :disabled="!isValidInvoiceNumber"
          >
            Confirm & Print
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk Invoice Generation Modal -->
    <div v-if="showBulkInvoiceModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-lg shadow-lg w-2/3 max-h-[80vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4">Generate Invoices for Selected Customers</h2>
        
        <div class="grid grid-cols-2 gap-4 mb-6">
          <!-- Date inputs -->
          <div>
            <div class="font-semibold mb-2">Start Date:</div>
            <input 
              type="date" 
              v-model="bulkInvoiceStartDate"
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <div class="font-semibold mb-2">End Date:</div>
            <input 
              type="date" 
              v-model="bulkInvoiceEndDate"
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <div class="font-semibold mb-2">Invoice Date:</div>
            <input 
              type="date" 
              v-model="bulkInvoiceDate"
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <div class="font-semibold mb-2">Starting Invoice Number:</div>
            <div class="flex items-center">
              <span class="p-2 bg-gray-200 border border-gray-300 rounded-l">{{ invoicePrefix }}</span>
              <input 
                v-model="invoiceSequence"
                type="text" 
                class="w-1/4 p-2 border border-gray-300 rounded-r"
                maxlength="5"
                :class="{'border-red-500': !isValidSequence}"
              />
            </div>
          </div>
        </div>

        <!-- Customer selection -->
        <div class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <h3 class="font-semibold">Select Customers</h3>
            <div class="space-x-2">
              <button @click="selectAllCustomers" class="text-sm text-blue-600 hover:text-blue-800">
                Select All
              </button>
              <span class="text-gray-400">|</span>
              <button @click="deselectAllCustomers" class="text-sm text-blue-600 hover:text-blue-800">
                Deselect All
              </button>
            </div>
          </div>
          <div class="border border-gray-200 rounded max-h-60 overflow-y-auto p-2">
            <div 
              v-for="customer in customers" 
              :key="customer.id"
              class="flex items-center p-2 hover:bg-gray-50"
            >
              <input
                type="checkbox"
                :id="'customer-' + customer.id"
                v-model="selectedCustomersForBulk"
                :value="customer.id"
                class="h-4 w-4 text-blue-600 rounded border-gray-300"
              />
              <label :for="'customer-' + customer.id" class="ml-2 cursor-pointer flex-1">
                {{ customer.company_name }}
              </label>
            </div>
          </div>
        </div>

        <div class="flex justify-end space-x-4">
          <button @click="showBulkInvoiceModal = false" class="btn-secondary">
            Cancel
          </button>
          <button 
            @click="generateBulkInvoices" 
            class="btn-primary"
            :disabled="!isValidBulkDateRange || !isValidInvoiceNumber || selectedCustomersForBulk.length === 0 || isBulkGenerating"
          >
            {{ isBulkGenerating ? 'Generating...' : 'Generate Invoices' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="groupedChallans.length > 0" class="mt-8">
      <div class="grid grid-cols-50 font-bold border-b border-gray-800 pb-2 text-lg">
        <div class="col-span-5">Size</div>
        <div class="col-span-3">Clr</div>
        <div class="col-span-3">DC</div>
        <div class="col-span-5">Job ID</div>
        <div class="col-span-3">Sets</div>
        <div class="col-span-26">Job Name</div>
        <div class="col-span-5">Remark</div>
      </div>
      <div v-for="(plateGroup, plateIndex) in groupedChallans" :key="plateIndex">
        <div class="grid grid-cols-50 gap-4">
          <div class="font-bold col-span-5">{{ plateGroup.size }}</div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
        <div v-for="(colourGroup, colourIndex) in plateGroup.colours" :key="colourIndex">
          <div class="grid grid-cols-50 gap-4">
            <div></div>
            <div class="font-medium col-span-3 col-start-6">{{ colourGroup.colour }}</div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
          </div>
          <div v-for="(challanGroup, challanIndex) in colourGroup.challans" :key="challanIndex">
            <div class="grid grid-cols-50 gap-4">
              <div></div>
              <div></div>
              <div class="font-medium col-span-3 col-start-9">{{ challanGroup.challan_no }}</div>
              <div></div>
              <div></div>
              <div></div>
              <div></div>
            </div>
            <div v-for="(job, jobIndex) in challanGroup.jobs" :key="jobIndex" class="grid grid-cols-50 gap-4">
              <div></div>
              <div></div>
              <div></div>
              <div class="font-medium col-span-5 col-start-12">{{ job.job_id }}</div>
              <div class="font-medium col-span-3 col-start-17">{{ job.quantity }}</div>
              <div class="font-medium col-span-26 col-start-20">{{ job.job_name }}</div>
              <div class="font-medium col-span-5 col-start-46">{{ job.remark }}</div>
            </div>
          </div>
          <div class="grid grid-cols-50 font-bold">
            <div class="col-span-45 col-start-6 border-t border-dashed border-gray-800"></div>
            <div></div>
            <div class="col-span-5 col-start-9 font-bold">Total Sets</div>
            <div></div>
            <div class="col-span-3 col-start-17 font-bold">
              {{ colourGroup.challans.reduce((sum, challanGroup) => sum + challanGroup.jobs.reduce((jobSum, job) => jobSum + job.quantity, 0), 0) }}
            </div>
            <div></div>
            <div 
              :class="{
                'col-span-45 col-start-6 border-t border-gray-800': colourIndex !== plateGroup.colours.length - 1,
                'col-span-50 col-start-1 border-t border-gray-800': colourIndex === plateGroup.colours.length - 1
              }">
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="mt-8">
      <p class="text-gray-500">No job orders found for the selected customer and date range.</p>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';
import { printCustomerSummary } from '../../utils/printCustomerSummary';
import { printTaxInvoice } from '../../utils/printTaxInvoice';

export default {
  data() {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);

    return {
      customers: [], // List of customers
      plateSizes: [], // List of plate sizes
      selectedCustomerId: '', // Selected customer ID
      startDate: oneMonthAgo.toISOString().split('T')[0], // Default to 1 month ago
      endDate: today.toISOString().split('T')[0], // Default to today
      groupedChallans: [], // Grouped challans data
      customerRates: [], // Rates for the selected customer
      userRole: '', // User role
      showInvoiceModal: false, // Control the modal visibility
      invoicePrefix: '', // e.g., "2526/GST/"
      invoiceSequence: '', // e.g., "34"
      previewItemsData: [], // Store the items data for preview
      previewInvoiceData: {}, // Store the invoice data for preview
      latestInvoiceNumber: '', // Store the latest invoice number
      latestSequenceNumber: 0, // Store the latest sequence number
      currentFinancialYear: '', // Store the current financial year
      showBulkInvoiceModal: false,
      bulkInvoiceStartDate: '',
      bulkInvoiceEndDate: '',
      bulkInvoiceDate: '', // For storing invoice date for bulk generation
      isBulkGenerating: false,
      selectedCustomersForBulk: [], // Array to store selected customer IDs
    };
  },
  computed: {
    selectedCustomer() {
      return this.customers.find(customer => customer.id === this.selectedCustomerId) || {};
    },
    previewItemCount() {
      return this.previewItemsData.length;
    },
    formattedInvoiceNumber() {
      return `${this.invoicePrefix}${this.invoiceSequence.padStart(2, '0')}`;
    },
    isValidSequence() {
      return /^\d+$/.test(this.invoiceSequence);
    },
    isValidInvoiceNumber() {
      return this.isValidSequence; // Remove the isNumberTooSmall check
    },
    isValidBulkDateRange() {
      return this.bulkInvoiceStartDate && this.bulkInvoiceEndDate && 
             this.bulkInvoiceStartDate <= this.bulkInvoiceEndDate;
    }
  },
  methods: {
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data.sort((a, b) => a.company_name.localeCompare(b.company_name));
      } catch (error) {
        console.error('Error fetching customers:', error);
      }
    },
    async fetchPlateSizes() {
      try {
        const response = await axios.get('/plate-summary');
        if (!response.data || !Array.isArray(response.data)) {
          throw new Error('Invalid plate sizes data received');
        }
        this.plateSizes = response.data;
        return response.data;
      } catch (error) {
        console.error('Error fetching plate sizes:', error);
        throw new Error('Failed to load plate sizes. Please try again.');
      }
    },
    async filterSummary() {
      if (!this.selectedCustomerId) {
        alert('Please select a customer.');
        return;
      }

      try {
        const response = await axios.get('/challans', {
          params: {
            customer_id: this.selectedCustomerId,
            start_date: this.startDate,
            end_date: this.endDate,
          },
        });
        const challans = response.data;
        // console.log('Fetched Challans:', challans);

        // Group challans by plate size, colours, and challan_code
        const grouped = [];
        challans.forEach((challan) => {
          challan.jobs.forEach((job) => {
            const plateSize = this.plateSizes.find(plate => plate.size_id === job.plate_size_id);
            if (!plateSize) {
              console.warn(`Plate size not found for job ${job.job_id}, size_id: ${job.plate_size_id}`);
              return; // Skip this job if plate size not found
            }
            const size = `${plateSize.length}x${plateSize.width}${plateSize.is_dl ? '-DL' : ''}`;
            let plateGroup = grouped.find(group => group.size === size);
            if (!plateGroup) {
              plateGroup = { 
                size, 
                sizeId: plateSize ? plateSize.size_id : 0, // Store the size_id directly in the group
                colours: [] 
              };
              grouped.push(plateGroup);
            }

            let colourGroup = plateGroup.colours.find(group => group.colour === job.colour);
            if (!colourGroup) {
              colourGroup = { colour: job.colour, challans: [] };
              plateGroup.colours.push(colourGroup);
            }
            const challanCodeFormatted = challan.challan_code.split('-')[1] || challan.challan_code;

            let challanGroup = colourGroup.challans.find(group => group.challan_no === challanCodeFormatted);
            if (!challanGroup) {
              challanGroup = { challan_no: challanCodeFormatted, jobs: [] };
              colourGroup.challans.push(challanGroup);
            }

            challanGroup.jobs.push({
              job_id: job.job_id,
              quantity: job.quantity,
              job_name: job.job_name,
              remark: job.remark,
            });
          });
        });

        this.groupedChallans = grouped;
        // console.log('Grouped Challans:', this.groupedChallans);
      } catch (error) {
        console.error('Error fetching challans:', error);
      }
    },
    printSummary() {
      if (!this.groupedChallans.length) {
        alert('No data available to print.');
        return;
      }

      const customerName = this.customers.find(customer => customer.id === this.selectedCustomerId)?.company_name || 'Unknown';
      printCustomerSummary(this.groupedChallans, customerName, this.startDate, this.endDate);
    },
    async printTaxInvoice() {
      if (!this.groupedChallans.length) {
        alert('No data available to generate tax invoice.');
        return;
      }

      try {
        if (!this.customerRates.length) {
          await this.fetchCustomerRates(this.selectedCustomerId);
        }

        // Generate formatted invoice number based on financial year and sequence
        await this.generateFormattedInvoiceNumber();

        // Prepare items data
        this.previewItemsData = [];
        this.groupedChallans.forEach(plateGroup => {
          plateGroup.colours.forEach(colourGroup => {
            // Filter billable jobs
            const billableJobs = colourGroup.challans.map(challan => ({
              ...challan,
              jobs: challan.jobs.filter(job => 
                !job.remark || 
                !(job.remark.toLowerCase().includes('no bill') || 
                  job.remark.toLowerCase().includes('consult'))
              )
            })).filter(challan => challan.jobs.length > 0);
            
            if (billableJobs.length === 0) return;
            
            const sizeId = plateGroup.sizeId;
            const customerRate = this.customerRates.find(rate => 
              rate.plate_size_id === sizeId
            );
            
            // Default to plate_rate, but store both rates
            const plateRate = customerRate?.plate_rate || 0;
            const bakingRate = customerRate?.baking_rate || 0;
            
            // Separate regular jobs and baking jobs
            const regularJobs = [];
            const bakingJobs = [];
            
            billableJobs.forEach(challan => {
              challan.jobs.forEach(job => {
                const hasBaking = job.remark && job.remark.toLowerCase().includes('baking');
                if (hasBaking) {
                  bakingJobs.push({ ...job, challan_no: challan.challan_no });
                } else {
                  regularJobs.push({ ...job, challan_no: challan.challan_no });
                }
              });
            });
            
            // Create regular jobs invoice item if any exist
            if (regularJobs.length > 0) {
              const regularQuantity = regularJobs.reduce((sum, job) => sum + job.quantity, 0);
              const regularJobIds = regularJobs.map(job => job.job_id);
              
              if (regularQuantity > 0) {
                this.previewItemsData.push({
                  plateSize: plateGroup.size,
                  plateSizeId: sizeId,
                  colours: colourGroup.colour,
                  jobIds: regularJobIds,
                  quantity: regularQuantity,
                  rateType: 'plate_rate',
                  plateRate: plateRate,
                  bakingRate: bakingRate,
                  rate: plateRate,
                  amount: regularQuantity * plateRate,
                  jobs: regularJobs // Include the full jobs array with challan numbers
                });
              }
            }
            
            // Create baking jobs invoice item if any exist
            if (bakingJobs.length > 0) {
              const bakingQuantity = bakingJobs.reduce((sum, job) => sum + job.quantity, 0);
              const bakingJobIds = bakingJobs.map(job => job.job_id);
              
              if (bakingQuantity > 0) {
                this.previewItemsData.push({
                  plateSize: plateGroup.size,
                  plateSizeId: sizeId,
                  colours: colourGroup.colour,
                  jobIds: bakingJobIds,
                  quantity: bakingQuantity,
                  rateType: 'baking_rate',
                  plateRate: plateRate,
                  bakingRate: bakingRate,
                  rate: plateRate + bakingRate,
                  amount: bakingQuantity * (plateRate + bakingRate),
                  jobs: bakingJobs // Include the full jobs array with challan numbers
                });
              }
            }
          });
        });
        
        if (this.previewItemsData.length === 0) {
          alert('No billable items found. All jobs are marked as "No bill" or "Consult".');
          return;
        }

        // Prepare delivery challan references
        const deliveryChallanRef = this.groupedChallans.flatMap(plateGroup => 
          plateGroup.colours.flatMap(colorGroup => 
            colorGroup.challans.map(challan => challan.challan_no)
          )
        ).join(', ').substring(0, 30);

        // Store invoice data for preview
        this.previewInvoiceData = {
          invoice_number: this.formattedInvoiceNumber,
          invoice_date: this.endDate,  // Default to end date but can be modified
          due_date: (() => {
            const date = new Date(this.endDate);
            date.setDate(date.getDate() + 30);
            return date.toISOString().split('T')[0];
          })(),
          delivery_challan_ref: deliveryChallanRef
        };

        // Show the confirmation modal
        this.showInvoiceModal = true;
      } catch (error) {
        console.error('Error preparing tax invoice data:', error);
        alert('Error preparing tax invoice data. See console for details.');
      }
    },
    
    updateItemAmount(item) {
      // Update the rate and amount based on the selected rate type
      if (item.rateType === 'plate_rate') {
        item.rate = item.plateRate;
        item.withBaking = false;
      } else if (item.rateType === 'baking_rate') {
        // For baking rate type, use both plate rate and baking rate combined
        item.rate = item.plateRate + item.bakingRate;
        item.withBaking = true;
      }
      item.amount = item.quantity * item.rate;
    },
    
    calculateTotal() {
      // Calculate subtotal based on rate and quantity for each item
      const subtotal = this.previewItemsData.reduce((sum, item) => {
        // Use the per-unit rate
        const amount = item.quantity * item.rate;
        item.amount = amount;
        return sum + amount;
      }, 0);

      // Calculate taxes (9% CGST and 9% SGST)
      const cgst = subtotal * 0.09;
      const sgst = subtotal * 0.09;
      const roundedTotal = Math.round(subtotal + cgst + sgst);

      return {
        subtotal: subtotal.toFixed(2),
        cgst: cgst.toFixed(2),
        sgst: sgst.toFixed(2),
        roundingAdjustment: (roundedTotal - (subtotal + cgst + sgst)).toFixed(2),
        grandTotal: roundedTotal.toFixed(2)
      };
    },
    
    async generateFormattedInvoiceNumber() {
      try {
        // Get the latest invoice number from the API
        const response = await axios.get('/invoices/latest');
        
        // Check if we have a valid invoice data in the response
        if (response.data && response.status === 200) {
          const latestInvoice = response.data;
          
          // Check if we have financial year and sequence information
          let financialYear = '';
          let sequenceNumber = 1;
          
          if (latestInvoice.financial_year) {
            // Use the financial year from the API response
            financialYear = latestInvoice.financial_year;
            
            // Increment the sequence number
            sequenceNumber = (latestInvoice.invoice_sequence || 0) + 1;
            this.latestSequenceNumber = latestInvoice.invoice_sequence || 0;
          } else {
            // Determine the current financial year manually if not provided
            const today = new Date();
            let financialYearStart, financialYearEnd;
            
            // If current month is April or later, financial year is current year to next year
            // Otherwise it's previous year to current year
            if (today.getMonth() >= 3) { // 3 is April (0-indexed months)
              financialYearStart = today.getFullYear();
              financialYearEnd = today.getFullYear() + 1;
            } else {
              financialYearStart = today.getFullYear() - 1;
              financialYearEnd = today.getFullYear();
            }
            
            // Use the last two digits of each year
            financialYear = `${String(financialYearStart).slice(-2)}${String(financialYearEnd).slice(-2)}`;
          }
          
          // Store the prefix and sequence separately for display
          this.currentFinancialYear = financialYear;
          this.invoicePrefix = `${financialYear}/GST/`;
          this.invoiceSequence = sequenceNumber.toString();
        } else {
          // Fallback if response is invalid
          const today = new Date();
          const year = today.getFullYear();
          const nextYear = today.getFullYear() + 1;
          const financialYear = `${year.toString().slice(-2)}${nextYear.toString().slice(-2)}`;
          this.currentFinancialYear = financialYear;
          this.invoicePrefix = `${financialYear}/GST/`;
          this.invoiceSequence = "01";
        }
      } catch (error) {
        console.error('Error generating invoice number:', error);
        // Fallback to a default format if there's an error
        const today = new Date();
        const year = today.getFullYear();
        const nextYear = today.getFullYear() + 1;
        const financialYear = `${year.toString().slice(-2)}${nextYear.toString().slice(-2)}`;
        this.currentFinancialYear = financialYear;
        this.invoicePrefix = `${financialYear}/GST/`;
        this.invoiceSequence = "01";
        this.latestSequenceNumber = 0; // Reset to 0 to avoid validation errors
      }
    },
    
    cancelInvoiceGeneration() {
      this.showInvoiceModal = false;
    },
    
    async confirmInvoiceGeneration() {
      // Validate that invoice sequence is a number
      if (!this.isValidSequence) {
        alert('Please enter a valid invoice sequence number.');
        return;
      }

      try {
        this.showInvoiceModal = false;
        
        // Use the formatted invoice number as entered by user
        let invoiceNumber = this.formattedInvoiceNumber;
        let currentSequence = parseInt(this.invoiceSequence, 10);
        
        // Check if the entered invoice number already exists
        try {
          const existingInvoiceResponse = await axios.get(`/invoices/check-number/${encodeURIComponent(invoiceNumber)}`);
          if (existingInvoiceResponse.data.exists) {
            // If it exists, get the next available number from the API
            const latestResponse = await axios.get('/invoices/latest');
            if (latestResponse.data && latestResponse.status === 200) {
              const nextSequence = (latestResponse.data.invoice_sequence || 0) + 1;
              this.invoiceSequence = nextSequence.toString();
              invoiceNumber = `${this.invoicePrefix}${nextSequence.toString().padStart(2, '0')}`;
              currentSequence = nextSequence;
              
              alert(`Invoice number ${this.formattedInvoiceNumber} already exists. Using next available number: ${invoiceNumber}`);
            } else {
              alert(`Invoice number ${invoiceNumber} already exists. Please use a different sequence number.`);
              // Update the sequence to next available before reopening modal
              try {
                const latestFallbackResponse = await axios.get('/invoices/latest');
                if (latestFallbackResponse.data) {
                  this.invoiceSequence = ((latestFallbackResponse.data.invoice_sequence || 0) + 1).toString();
                }
              } catch (fallbackError) {
                console.error('Error getting fallback sequence:', fallbackError);
              }
              this.showInvoiceModal = true;
              return;
            }
          }
        } catch (checkError) {
          if (checkError.response?.status !== 404) {
            console.error('Error checking invoice number:', checkError);
            alert('Error checking invoice number. Please try again.');
            // Update the sequence to next available before reopening modal
            try {
              const latestFallbackResponse = await axios.get('/invoices/latest');
              if (latestFallbackResponse.data) {
                this.invoiceSequence = ((latestFallbackResponse.data.invoice_sequence || 0) + 1).toString();
              }
            } catch (fallbackError) {
              console.error('Error getting fallback sequence:', fallbackError);
            }
            this.showInvoiceModal = true;
            return;
          }
          // 404 means invoice doesn't exist, which is what we want - proceed with the entered number
        }
        
        // Parse parts for database storage
        const financialYear = this.currentFinancialYear;
        const invoiceSequence = currentSequence;
        
        // Split items by job rate BEFORE calculating totals and saving
        const processedItems = this.splitItemsByJobRate(this.previewItemsData);
        
        // Calculate totals using the processed items with updated rates
        const totals = this.calculateTotalFromProcessedItems(processedItems);

        // Update the preview invoice data with the final invoice number
        this.previewInvoiceData.invoice_number = invoiceNumber;

        // Log the invoice data being saved
        const invoiceToSave = {
          invoice_number: invoiceNumber,
          financial_year: financialYear,
          invoice_sequence: invoiceSequence,
          invoice_date: this.previewInvoiceData.invoice_date,
          due_date: this.previewInvoiceData.due_date,
          customer_id: this.selectedCustomerId,
          total_amount: parseFloat(totals.subtotal),
          cgst_amount: parseFloat(totals.cgst),
          sgst_amount: parseFloat(totals.sgst),
          igst_amount: 0,
          grand_total: parseFloat(totals.grandTotal),
          challan_references: this.previewInvoiceData.delivery_challan_ref,
          status: 'unpaid',
          // Use processed items instead of previewItemsData
          items: processedItems.map(item => ({
            plate_size_id: item.plateSizeId,
            description: `${item.plateSize} PS Plates - ${item.colours} ${item.colours === 1 ? 'colour' : 'colours'}${item.withBaking ? ' with Baking' : ''}`,
            colours: item.colours,
            quantity: item.quantity,
            rate: item.rate * item.colours, // Store rate multiplied by colours for invoice display
            amount: item.amount * item.colours, // Store amount multiplied by colours
            jobs: item.jobs,
            hasBaking: item.jobs.some(job => job.remark && job.remark.toLowerCase().includes('baking'))
          }))
        };

        // Send to API
        const response = await axios.post('/invoices', invoiceToSave);

        // Generate the actual PDF invoice using processed items
        const pdfResult = await printTaxInvoice(
          this.previewInvoiceData,
          this.selectedCustomer,
          processedItems,
          this.customerRates,
          true
        );
        
      } catch (error) {
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          stack: error.stack
        });
        
        // Check if it's a duplicate invoice number error (fallback)
        if (error.response?.status === 409) {
          alert(`Invoice number ${this.formattedInvoiceNumber} already exists. Please use a different sequence number or delete the existing invoice.`);
          // Update the sequence to next available before reopening modal
          try {
            const latestFallbackResponse = await axios.get('/invoices/latest');
            if (latestFallbackResponse.data) {
              this.invoiceSequence = ((latestFallbackResponse.data.invoice_sequence || 0) + 1).toString();
            }
          } catch (fallbackError) {
            console.error('Error getting fallback sequence:', fallbackError);
          }
          this.showInvoiceModal = true; // Reopen modal
        } else {
          alert(`Error generating tax invoice: ${error.message}`);
        }
      }
    },
    
    async fetchCustomerRates(customerId) {
      try {
        const response = await axios.get(`/customer-rates/${customerId}`);
        // Check if response.data is an array and has items
        if (response.data && Array.isArray(response.data) && response.data.length > 0) {
          this.customerRates = response.data;
          return response.data;
        } else {
          console.warn(`No rates configured for customer ID: ${customerId}`);
          return [];
        }
      } catch (error) {
        console.error('Error fetching customer rates:', error);
        return [];
      }
    },
    setLastWeekDates() {
      const today = new Date();
      const lastSaturday = new Date(today);
      
      // Find last Saturday
      while (lastSaturday.getDay() !== 6) { // 6 is Saturday
        lastSaturday.setDate(lastSaturday.getDate() - 1);
      }

      // Create last Monday by copying lastSaturday and subtracting 5 days
      const lastMonday = new Date(lastSaturday);
      lastMonday.setDate(lastSaturday.getDate() - 5);

      // Format dates for input fields (YYYY-MM-DD)
      this.startDate = lastMonday.toISOString().split('T')[0];
      this.endDate = lastSaturday.toISOString().split('T')[0];

      // If customer is selected, trigger the filter
      if (this.selectedCustomerId) {
        // this.filterSummary();
      }
    },
    async generateBulkInvoices() {
      if (!this.isValidBulkDateRange || this.isBulkGenerating || this.selectedCustomersForBulk.length === 0) return;

      try {
        this.isBulkGenerating = true;
        const results = {
          success: [],
          failed: [],
          skipped: []
        };

        // Initialize current sequence from the component data
        let currentSequence = parseInt(this.invoiceSequence, 10);

        // Filter customers based on selection
        const selectedCustomers = this.customers.filter(customer => 
          this.selectedCustomersForBulk.includes(customer.id)
        );

        // Process each selected customer
        for (const customer of selectedCustomers) {
          try {
            // Reset previewItemsData for each customer
            this.previewItemsData = [];

            // Get customer rates first
            const customerRates = await this.fetchCustomerRates(customer.id);
            if (!customerRates || customerRates.length === 0) {
              console.warn(`No rates found for customer ${customer.company_name}`);
              results.skipped.push(`${customer.company_name} (no rates configured)`);
              continue; // Skip to next customer
            }

            // Get customer's summary for the date range
            const response = await axios.get('/challans', {
              params: {
                customer_id: customer.id,
                start_date: this.bulkInvoiceStartDate,
                end_date: this.bulkInvoiceEndDate,
              },
            });

            const challans = response.data;
            if (!challans.length) {
              results.skipped.push(customer.company_name);
              continue;
            }

            // Group challans and prepare items
            const grouped = [];
            challans.forEach((challan) => {
              challan.jobs.forEach((job) => {
                // Skip if plate_size_id is missing
                if (!job.plate_size_id) {
                  console.warn(`Missing plate_size_id for job ${job.job_id}`);
                  return;
                }

                const plateSize = this.plateSizes.find(plate => plate.size_id === job.plate_size_id);
                if (!plateSize) {
                  console.warn(`Plate size not found for job ${job.job_id}, size_id: ${job.plate_size_id}`);
                  return;
                }

                const size = plateSize ? `${plateSize.length}x${plateSize.width}${plateSize.is_dl ? '-DL' : ''}` : 'Unknown';
                
                let plateGroup = grouped.find(group => group.size === size);
                if (!plateGroup) {
                  plateGroup = { 
                    size, 
                    sizeId: plateSize ? plateSize.size_id : 0,
                    colours: [] 
                  };
                  grouped.push(plateGroup);
                }

                let colourGroup = plateGroup.colours.find(group => group.colour === job.colour);
                if (!colourGroup) {
                  colourGroup = { colour: job.colour, challans: [] };
                  plateGroup.colours.push(colourGroup);
                }

                let challanGroup = colourGroup.challans.find(group => 
                  group.challan_no === challan.challan_code.split('-')[1]
                );
                if (!challanGroup) {
                  challanGroup = { 
                    challan_no: challan.challan_code.split('-')[1], 
                    jobs: [] 
                  };
                  colourGroup.challans.push(challanGroup);
                }

                challanGroup.jobs.push({
                  job_id: job.job_id,
                  quantity: job.quantity,
                  job_name: job.job_name,
                  remark: job.remark,
                });
              });
            });

            // Use customerRates from the fetched data
            grouped.forEach(plateGroup => {
              plateGroup.colours.forEach(colourGroup => {
                // Filter billable jobs
                const billableJobs = colourGroup.challans.map(challan => ({
                  ...challan,
                  jobs: challan.jobs.filter(job => 
                    !job.remark || 
                    !(job.remark.toLowerCase().includes('no bill') || 
                      job.remark.toLowerCase().includes('consult'))
                )
                })).filter(challan => challan.jobs.length > 0);
                
                if (billableJobs.length === 0) return;
                
                const sizeId = plateGroup.sizeId;
                const customerRate = customerRates.find(rate => 
                  rate.plate_size_id === sizeId
                );
                
                // Default to plate_rate, but store both rates
                const plateRate = customerRate?.plate_rate || 0;
                const bakingRate = customerRate?.baking_rate || 0;
                
                // Separate regular jobs and baking jobs
                const regularJobs = [];
                const bakingJobs = [];
                
                billableJobs.forEach(challan => {
                  challan.jobs.forEach(job => {
                    const hasBaking = job.remark && job.remark.toLowerCase().includes('baking');
                    if (hasBaking) {
                      bakingJobs.push({ ...job, challan_no: challan.challan_no });
                    } else {
                      regularJobs.push({ ...job, challan_no: challan.challan_no });
                    }
                  });
                });
                
                // Create regular jobs invoice item if any exist
                if (regularJobs.length > 0) {
                  const regularQuantity = regularJobs.reduce((sum, job) => sum + job.quantity, 0);
                  const regularJobIds = regularJobs.map(job => job.job_id);
                  
                  if (regularQuantity > 0) {
                    this.previewItemsData.push({
                      plateSize: plateGroup.size,
                      plateSizeId: sizeId,
                      colours: colourGroup.colour,
                      jobIds: regularJobIds,
                      quantity: regularQuantity,
                      rateType: 'plate_rate',
                      plateRate: plateRate,
                      bakingRate: bakingRate,
                      rate: plateRate,
                      amount: regularQuantity * plateRate,
                      jobs: regularJobs // Include the full jobs array with challan numbers
                    });
                  }
                }
                
                // Create baking jobs invoice item if any exist
                if (bakingJobs.length > 0) {
                  const bakingQuantity = bakingJobs.reduce((sum, job) => sum + job.quantity, 0);
                  const bakingJobIds = bakingJobs.map(job => job.job_id);
                  
                  if (bakingQuantity > 0) {
                    this.previewItemsData.push({
                      plateSize: plateGroup.size,
                      plateSizeId: sizeId,
                      colours: colourGroup.colour,
                      jobIds: bakingJobIds,
                      quantity: bakingQuantity,
                      rateType: 'baking_rate',
                      plateRate: plateRate,
                      bakingRate: bakingRate,
                      rate: plateRate + bakingRate,
                      amount: bakingQuantity * (plateRate + bakingRate),
                      jobs: bakingJobs // Include the full jobs array with challan numbers
                    });
                  }
                }
              });
            });

            if (this.previewItemsData.length === 0) {
              alert('No billable items found. All jobs are marked as "No bill" or "Consult".');
              return;
            }

            // Prepare delivery challan references
            const deliveryChallanRef = this.groupedChallans.flatMap(plateGroup => 
              plateGroup.colours.flatMap(colorGroup => 
                colorGroup.challans.map(challan => challan.challan_no)
              )
            ).join(', ').substring(0, 30);

            // Calculate totals using similar logic from calculateTotal method
            const totals = (() => {
              const subtotal = this.previewItemsData.reduce((sum, item) => {
                const baseRate = item.withBaking ? 
                  (item.plateRate + item.bakingRate) : 
                  item.plateRate;
                
                const rateWithColors = baseRate * item.colours;
                const amount = item.quantity * rateWithColors;
                
                item.rate = rateWithColors;
                item.amount = amount;
                
                return sum + amount;
              }, 0);
              
              const cgst = subtotal * 0.09;
              const sgst = subtotal * 0.09;
              const exactTotal = subtotal + cgst + sgst;
              const roundedTotal = Math.round(exactTotal);
              
              return {
                subtotal,
                cgst,
                sgst,
                grandTotal: roundedTotal
              };
            })();

            // Create invoice
            const invoiceToSave = {
              invoice_number: `${this.invoicePrefix}${currentSequence.toString().padStart(2, '0')}`,
              financial_year: this.currentFinancialYear,
              invoice_sequence: currentSequence,
              invoice_date: this.bulkInvoiceDate,
              due_date: (() => {
                const date = new Date(this.bulkInvoiceDate);
                date.setDate(date.getDate() + 30);
                return date.toISOString().split('T')[0];
              })(),
              customer_id: customer.id,
              total_amount: totals.subtotal,
              cgst_amount: totals.cgst,
              sgst_amount: totals.sgst,
              igst_amount: 0,
              grand_total: totals.grandTotal,
              challan_references: deliveryChallanRef,
              status: 'unpaid',
              items: this.previewItemsData.map(item => ({
                plate_size_id: item.plateSizeId,
                description: `${item.plateSize} PS Plates - ${item.colours} ${item.colours === 1 ? 'colour' : 'colours'}${item.withBaking ? ' with Baking' : ''}`,
                colours: item.colours,
                quantity: item.quantity,
                rate: item.rate,
                amount: item.amount,
                jobs: item.jobs, // Include full jobs array with challan numbers
                hasBaking: item.jobs.some(job => job.remark && job.remark.toLowerCase().includes('baking'))
              }))
            };

            await axios.post('/invoices', invoiceToSave);
            results.success.push(customer.company_name);
            
            // Increment the sequence number after successful invoice creation
            currentSequence++;
            
            // Update the component's invoice sequence
            this.invoiceSequence = currentSequence.toString();

          } catch (error) {
            console.error(`Error generating invoice for ${customer.company_name}:`, error);
            results.failed.push(customer.company_name);
          }
        }

        // Show results notification
        let message = `Successfully generated ${results.success.length} invoices.\n`;
        if (results.skipped.length) {
          message += `\nSkipped ${results.skipped.length} customers with no billable items:\n${results.skipped.join(', ')}`;
        }
        if (results.failed.length) {
          message += `\nFailed to generate invoices for ${results.failed.length} customers:\n${results.failed.join(', ')}`;
        }

        alert(message);
        this.showBulkInvoiceModal = false;

      } catch (error) {
        console.error('Error in bulk invoice generation:', error);
        alert('Error generating invoices. Please check console for details.');
      } finally {
        this.isBulkGenerating = false;
      }
    },
    selectAllCustomers() {
      this.selectedCustomersForBulk = this.customers.map(customer => customer.id);
    },

    deselectAllCustomers() {
      this.selectedCustomersForBulk = [];
    },

    async openBulkInvoiceModal() {
      try {
        // Make sure plate sizes are loaded
        await this.fetchPlateSizes();
        
        // Set default dates when opening the modal
        this.bulkInvoiceStartDate = this.startDate;
        this.bulkInvoiceEndDate = this.endDate;
        this.bulkInvoiceDate = this.endDate;
        
        // Generate invoice number
        await this.generateFormattedInvoiceNumber();
        
        // Select all customers by default
        this.selectAllCustomers();
        
        // Show the modal
        this.showBulkInvoiceModal = true;
      } catch (error) {
        console.error('Error preparing bulk invoice generation:', error);
        alert('Error preparing bulk invoice generation. Please try again.');
      }
    },

    // Helper to get the editable rate for a job in the summary modal
    getEditableRate(size, colour, jobId) {
      const item = this.previewItemsData.find(
        i =>
          i.plateSize === size &&
          i.colours == colour &&
          i.jobs.some(j => j.job_id === jobId)
      );
      return item ? item.rate : 0;
    },

    // Handler to update the rate in previewItemsData when edited in the modal
    onRateChange(size, colour, jobId, newRate) {
      const item = this.previewItemsData.find(
        i =>
          i.plateSize === size &&
          i.colours == colour &&
          i.jobs.some(j => j.job_id === jobId)
      );
      if (item) {
        item.rate = parseFloat(newRate) || 0;
        item.amount = item.quantity * item.rate;
      }
    },

    // Find the rate property in previewItemsData for v-model binding
    findJobRateBinding(size, colour, jobId) {
      // Find the item in previewItemsData that contains this job
      const item = this.previewItemsData.find(
        i =>
          i.plateSize === size &&
          i.colours == colour &&
          i.jobs.some(j => j.job_id === jobId)
      );
      if (!item) return 0;
      // Find the job in the jobs array
      const job = item.jobs.find(j => j.job_id === jobId);
      // If you want to allow per-job rate, use job.rate, else use item.rate
      // If job.rate is undefined, fallback to item.rate
      if (job && job.rate !== undefined) return job.rate;
      return item.rate;
    },

    // Update the amount for the item and job when rate changes
    updateJobAmount(size, colour, jobId) {
      const item = this.previewItemsData.find(
        i =>
          i.plateSize === size &&
          i.colours == colour &&
          i.jobs.some(j => j.job_id === jobId)
      );
      if (!item) return;
      const job = item.jobs.find(j => j.job_id === jobId);
      if (job) {
        // If job.rate is undefined, initialize it
        if (job.rate === undefined) job.rate = item.rate;
        // Update the item's amount as the sum of all job quantities * their rates
        item.amount = item.jobs.reduce((sum, j) => sum + (j.quantity * (j.rate !== undefined ? j.rate : item.rate)), 0);
      }
    },

    onJobRateInput(size, colour, jobId, value) {
      const item = this.previewItemsData.find(
        i =>
          i.plateSize === size &&
          i.colours == colour &&
          i.jobs.some(j => j.job_id === jobId)
      );
      if (!item) return;
      const job = item.jobs.find(j => j.job_id === jobId);
      if (job) {
        job.rate = parseFloat(value) || 0;
        // Update the item's amount as the sum of all job quantities * their rates
        item.amount = item.jobs.reduce((sum, j) => sum + (j.quantity * (j.rate !== undefined ? j.rate : item.rate)), 0);
      }
    },

    // Split previewItemsData so each group has jobs with the same rate
    splitItemsByJobRate(items) {
      const result = [];
      items.forEach(item => {
        // Group jobs by their rate (if set), else use item.rate
        const jobsByRate = {};
        item.jobs.forEach(job => {
          const rate = (job.rate !== undefined ? job.rate : item.rate);
          if (!jobsByRate[rate]) jobsByRate[rate] = [];
          jobsByRate[rate].push(job);
        });
        Object.entries(jobsByRate).forEach(([rate, jobs]) => {
          // Do NOT multiply rate by colours here!
          result.push({
            ...item,
            jobs,
            quantity: jobs.reduce((sum, j) => sum + j.quantity, 0),
            rate: parseFloat(rate), // per-unit rate
            amount: jobs.reduce((sum, j) => sum + (j.quantity * parseFloat(rate)), 0)
          });
        });
      });
      return result;
    },

    calculateTotalFromProcessedItems(processedItems) {
      // Calculate subtotal based on processed items with updated rates
      const subtotal = processedItems.reduce((sum, item) => {
        // Rate is already per-unit, multiply by colours and quantity
        const amount = item.quantity * item.rate * item.colours;
        return sum + amount;
      }, 0);

      // Calculate taxes (9% CGST and 9% SGST)
      const cgst = subtotal * 0.09;
      const sgst = subtotal * 0.09;
      const roundedTotal = Math.round(subtotal + cgst + sgst);

      return {
        subtotal: subtotal.toFixed(2),
        cgst: cgst.toFixed(2),
        sgst: sgst.toFixed(2),
        roundingAdjustment: (roundedTotal - (subtotal + cgst + sgst)).toFixed(2),
        grandTotal: roundedTotal.toFixed(2)
      };
    },
  },
  mounted() {
    this.fetchCustomers();
    this.fetchPlateSizes();
    this.userRole = this.$store.state.user.role;
  },
  watch: {
    selectedCustomerId(newId) {
      if (newId) {
        this.fetchCustomerRates(newId);
      }
    }
  }
};
</script>