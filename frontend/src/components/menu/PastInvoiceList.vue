<template>
  <div class="invoice-list p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-6 text-gray-800">Past Invoices</h1>

    <!-- Filters -->
    <div class="filters mb-4 flex flex-wrap gap-4 items-end">
      <div>
        <label for="invoiceNumber" class="block text-sm font-medium text-gray-700">Invoice Number</label>
        <input id="invoiceNumber" v-model="filters.invoiceNumber" type="text"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          placeholder="Enter Invoice Number" />
      </div>
      <div>
        <label for="invoiceDate" class="block text-sm font-medium text-gray-700">Invoice Date</label>
        <input id="invoiceDate" v-model="filters.invoiceDate" type="date"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
      </div>
      <div>
        <label for="customer" class="block text-sm font-medium text-gray-700">Customer</label>
        <select id="customer" v-model="filters.customerId"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option value="">All Customers</option>
          <option v-for="customer in customers" :key="customer.id" :value="customer.id">
            {{ customer.company_name }}
          </option>
        </select>
      </div>
      <div>
        <label for="status" class="block text-sm font-medium text-gray-700">Status</label>
        <select id="status" v-model="filters.status"
          class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
          <option value="">All</option>
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="ml-auto flex gap-2">
        <button @click="applyFilters" class="btn-primary">
          Apply Filters
        </button>
        <button @click="clearFilters" class="btn-secondary">
          Clear Filters
        </button>
        <button @click="openExportModal" class="btn-export">
          <i class="fas fa-file-excel mr-1"></i> Export to Excel
        </button>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="loading" class="text-center py-4">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <p class="mt-2 text-gray-600">Loading invoices...</p>
    </div>

    <!-- Invoice Table -->
    <div v-else>
      <!-- Pagination Info -->
      <div class="mb-4 flex justify-between items-center">
        <div class="text-sm text-gray-700">
          Showing {{ ((pagination.page - 1) * pagination.per_page) + 1 }} to 
          {{ Math.min(pagination.page * pagination.per_page, pagination.total) }} of 
          {{ pagination.total }} invoices
        </div>
        <div class="text-sm text-gray-700">
          Page {{ pagination.page }} of {{ pagination.pages }}
        </div>
      </div>

      <table class="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr class="bg-gray-200">
            <th class="border border-gray-300 px-4 py-2">Invoice Number</th>
            <th class="border border-gray-300 px-4 py-2">Date</th>
            <th class="border border-gray-300 px-4 py-2">Customer</th>
            <th class="border border-gray-300 px-4 py-2">Total Amount</th>
            <th class="border border-gray-300 px-4 py-2">Status</th>
            <th class="border border-gray-300 px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="invoice in invoices" :key="invoice.id" :class="{
            'bg-green-50': invoice.status === 'paid',
            'bg-red-50': invoice.status === 'cancelled',
            'bg-yellow-50': invoice.status === 'unpaid'
          }">
            <td class="border border-gray-300 px-4 py-2">{{ invoice.invoice_number }}</td>
            <td class="border border-gray-300 px-4 py-2">{{ formatDate(invoice.invoice_date) }}</td>
            <td class="border border-gray-300 px-4 py-2">{{ invoice.customer_name }}</td>
            <td class="border border-gray-300 px-4 py-2">₹{{ formatAmount(invoice.grand_total) }}</td>
            <td class="border border-gray-300 px-4 py-2">
              <span :class="{
                'bg-green-100 text-green-800': invoice.status === 'paid',
                'bg-red-100 text-red-800': invoice.status === 'cancelled',
                'bg-yellow-100 text-yellow-800': invoice.status === 'unpaid'
              }" class="px-2 py-1 rounded-full">
                {{ capitalizeFirstLetter(invoice.status) }}
              </span>
            </td>
            <td class="border border-gray-300 px-4 py-2">
              <button @click="viewInvoice(invoice)" class="btn-primary mr-2">View</button>
              <button @click="printInvoice(invoice)" class="btn-print mr-2">Print</button>
              <button @click="showEmailModal(invoice)" class="btn-email mr-2">
                <i class="fas fa-envelope mr-1"></i> Email
              </button>
              <button @click="updateStatus(invoice)" class="btn-secondary mr-2"
                v-if="userRole === 'admin' || userRole === 'accountant'">
                {{ invoice.status === 'paid' ? 'Mark Unpaid' : 'Mark Paid' }}
              </button>
              <button @click="deleteInvoice(invoice)" class="btn-danger" v-if="userRole === 'accountant'">
                Delete
              </button>
            </td>
          </tr>
          <tr v-if="invoices.length === 0">
            <td class="border border-gray-300 px-4 py-2 text-center" colspan="6">No invoices found</td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination Controls -->
      <div class="mt-6 flex justify-between items-center">
        <div class="flex gap-2">
          <button 
            @click="goToPage(1)"
            :disabled="!pagination.has_prev"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            First
          </button>
          <button 
            @click="goToPage(pagination.prev_num)"
            :disabled="!pagination.has_prev"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
        </div>

        <!-- Page numbers -->
        <div class="flex gap-1">
          <button 
            v-for="page in visiblePageNumbers" 
            :key="page"
            @click="goToPage(page)"
            :class="{
              'bg-blue-500 text-white': page === pagination.page,
              'bg-white hover:bg-gray-50': page !== pagination.page
            }"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            {{ page }}
          </button>
        </div>

        <div class="flex gap-2">
          <button 
            @click="goToPage(pagination.next_num)"
            :disabled="!pagination.has_next"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
          <button 
            @click="goToPage(pagination.pages)"
            :disabled="!pagination.has_next"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Last
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Email Invoice Modal -->
  <div v-if="showEmailModalFlag" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/2">
      <h2 class="text-xl font-semibold mb-4">Email Invoice</h2>

      <div v-if="!selectedCustomerEmail" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <strong>Error:</strong> This customer doesn't have an email address.
        <a @click="goToCustomerEdit" class="text-blue-600 underline cursor-pointer">
          Update email address
        </a>
      </div>

      <div v-else>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Invoice</label>
          <div class="text-gray-800">{{ selectedInvoice?.invoice_number }}</div>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Customer</label>
          <div class="text-gray-800">{{ selectedCustomerName }}</div>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Email To</label>
          <div class="text-gray-800">{{ selectedCustomerEmail }}</div>
        </div>

        <div class="mb-4">
          <label for="email-subject" class="block text-sm font-medium text-gray-700 mb-1">Subject</label>
          <input id="email-subject" v-model="emailData.subject" type="text"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
        </div>

        <div class="mb-4">
          <label for="email-message" class="block text-sm font-medium text-gray-700 mb-1">Message</label>
          <textarea id="email-message" v-model="emailData.message" rows="9"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"></textarea>
        </div>

        <div class="mb-4">
          <label class="inline-flex items-center">
            <input type="checkbox" v-model="emailData.includePdf" class="form-checkbox h-5 w-5 text-blue-600">
            <span class="ml-2 text-gray-700">Attach invoice PDF</span>
          </label>
        </div>
      </div>

      <div class="flex justify-end space-x-3 mt-6">
        <button @click="closeEmailModal" class="btn-secondary">
          Cancel
        </button>
        <button @click="sendEmail" class="btn-primary" :disabled="isSending || !selectedCustomerEmail">
          {{ isSending ? 'Sending...' : 'Send Email' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Export Invoices Modal -->
  <div v-if="showExportModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-lg w-1/3">
      <h2 class="text-xl font-semibold mb-4">Export Invoices to Excel</h2>
      
      <div class="mb-4">
        <label for="export-date" class="block text-sm font-medium text-gray-700 mb-1">Select Date</label>
        <input 
          id="export-date" 
          v-model="exportDate" 
          type="date"
          class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          required
        />
      </div>
      
      <div class="mb-4">
        <p class="text-sm text-gray-600">
          This will export all invoices created on the selected date in Tally-compatible format.
        </p>
      </div>

      <div class="flex justify-end space-x-3 mt-6">
        <button @click="closeExportModal" class="btn-secondary">
          Cancel
        </button>
        <button 
          @click="exportToExcel" 
          class="btn-primary" 
          :disabled="!exportDate || isExporting"
        >
          {{ isExporting ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';
import moment from 'moment';
import { printTaxInvoice } from '../../utils/printTaxInvoice';
import * as XLSX from 'xlsx';

export default {
  data() {
    return {
      invoices: [],
      customers: [],
      filters: {
        invoiceNumber: '',
        invoiceDate: '',
        customerId: '',
        status: ''
      },
      pagination: {
        page: 1,
        pages: 1,
        per_page: 50,
        total: 0,
        has_prev: false,
        has_next: false,
        prev_num: null,
        next_num: null
      },
      userRole: '',
      loading: false,
      showEmailModalFlag: false,
      showExportModal: false,
      selectedInvoice: null,
      selectedCustomerEmail: '',
      selectedCustomerName: '',
      emailData: {
        subject: '',
        message: '',
        includePdf: true
      },
      exportDate: '',
      isSending: false,
      isExporting: false
    };
  },
  computed: {
    visiblePageNumbers() {
      const current = this.pagination.page;
      const total = this.pagination.pages;
      const delta = 2; // Number of pages to show on each side of current page
      
      let start = Math.max(1, current - delta);
      let end = Math.min(total, current + delta);
      
      // Adjust if we're near the beginning or end
      if (current <= delta) {
        end = Math.min(total, 2 * delta + 1);
      }
      if (current > total - delta) {
        start = Math.max(1, total - 2 * delta);
      }
      
      const pages = [];
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      return pages;
    }
  },
  methods: {
    async fetchInvoices(page = 1) {
      this.loading = true;
      try {
        const queryParams = new URLSearchParams();

        // Add pagination parameters
        queryParams.append('page', page.toString());
        queryParams.append('per_page', '50');

        // Clean and validate invoice number filter
        if (this.filters.invoiceNumber && this.filters.invoiceNumber.trim()) {
          queryParams.append('invoice_number', this.filters.invoiceNumber.trim());
        }

        // Validate date filter
        if (this.filters.invoiceDate) {
          const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
          if (dateRegex.test(this.filters.invoiceDate)) {
            queryParams.append('date', this.filters.invoiceDate);
          } else {
            console.error(`Invalid date format: ${this.filters.invoiceDate}`);
          }
        }

        // Add other filters
        if (this.filters.customerId) {
          queryParams.append('customer_id', this.filters.customerId);
        }

        if (this.filters.status) {
          queryParams.append('status', this.filters.status);
        }

        const url = `/invoices${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        const response = await axios.get(url);
        
        this.invoices = response.data.invoices;
        this.pagination = response.data.pagination;

      } catch (error) {
        console.error('Error fetching invoices:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
      } finally {
        this.loading = false;
      }
    },

    goToPage(page) {
      if (page && page !== this.pagination.page && page >= 1 && page <= this.pagination.pages) {
        this.fetchInvoices(page);
      }
    },

    applyFilters() {
      // Perform validation before fetching
      if (this.filters.invoiceDate) {
        try {
          const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
          if (!dateRegex.test(this.filters.invoiceDate)) {
            alert('Please enter a valid date in YYYY-MM-DD format');
            return;
          }
        } catch (e) {
          alert('Please enter a valid date');
          return;
        }
      }
      // Reset to page 1 when applying filters
      this.fetchInvoices(1);
    },

    clearFilters() {
      this.filters = {
        invoiceNumber: '',
        invoiceDate: '',
        customerId: '',
        status: ''
      };
      // Reset to page 1 when clearing filters
      this.fetchInvoices(1);
    },
    async fetchCustomers() {
      try {
        const response = await axios.get('/customers');
        this.customers = response.data;
      } catch (error) {
        console.error('Error fetching customers:', error);
      }
    },
    formatDate(dateString) {
      return moment(dateString).format('DD MMM YYYY');
    },
    formatAmount(amount) {
      return amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    async viewInvoice(invoice) {
      try {
        this.loading = true;

        // Add debug logs

        const [customerData, invoiceDetails, customerRates] = await Promise.all([
          this.getCustomerById(invoice.customer_id),
          this.getInvoiceDetails(invoice.id),
          this.getCustomerRates(invoice.customer_id)
        ]);

        // Process invoice items
        const itemsData = invoiceDetails.items.map(item => {
          // Add debug log for each item

          const customerRate = customerRates.find(rate =>
            rate.plate_size_id === item.plate_size_id
          );

          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;
          const hasBaking = item.description.toLowerCase().includes('baking');

          // Use stored rate from database if available, otherwise calculate from customer rates
          let finalRate;
          if (item.rate && item.rate > 0) {
            // Use the stored rate from the database (this is the rate * colours that was saved)
            finalRate = item.rate;
          } else {
            // Fall back to calculating from customer rates
            finalRate = hasBaking ? plateRate + bakingRate : plateRate;
          }

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: finalRate, // Use the finalRate (either stored or calculated)
            amount: item.amount,
            description: item.description,
            withBaking: hasBaking,
            // Add flag to indicate this is from stored data
            useStoredRate: !!(item.rate && item.rate > 0)
          };
        });

        // Format invoice data
        const formattedInvoiceData = {
          invoice_number: invoiceDetails.invoice_number,
          invoice_date: invoiceDetails.invoice_date,
          due_date: invoiceDetails.due_date,
          delivery_challan_ref: invoiceDetails.delivery_challan_ref,
          subtotal: invoiceDetails.subtotal,
          cgst: invoiceDetails.cgst,
          sgst: invoiceDetails.sgst,
          grand_total: invoiceDetails.grand_total
        };

        const transformData = async (itemsData) => {
          // Assuming you have a function to fetch job details by job_id
          const getJobDetails = async (jobId) => {
            // Replace this with your actual API call or database query
            return {
              job_id: jobId,
              quantity: 1,
              job_name: "Job Name", // This should come from your database
              remark: "",
              challan_no: jobId // This should come from your database
            };
          };

          const transformedData = await Promise.all(itemsData.map(async (item) => {
            // Fetch job details for each job ID
            const jobPromises = item.jobIds.map(jobId => getJobDetails(jobId));
            const jobs = await Promise.all(jobPromises);

            // Remove .0 from plateSize if present
            const plateSize = item.plateSize.replace('.0', '');

            return {
              ...item,
              plateSize,
              jobs
            };
          }));

          return transformedData;
        };

        const finalData = await transformData(itemsData);

        // Generate PDF without auto-printing
        await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          finalData,
          customerRates,
          false // Don't auto-print
        );

      } catch (error) {
        console.error('Error viewing invoice:', error);
        alert('Error viewing invoice. Please try again.');
      } finally {
        this.loading = false;
      }
    },
    async printInvoice(invoice) {
      try {
        this.loading = true;

        // Fetch required data
        const [customerData, invoiceDetails, customerRates] = await Promise.all([
          this.getCustomerById(invoice.customer_id),
          this.getInvoiceDetails(invoice.id),
          this.getCustomerRates(invoice.customer_id)
        ]);

        // Process invoice items similar to generateTaxInvoice
        const itemsData = invoiceDetails.items.map(item => {
          // Find customer rate for this plate size
          const customerRate = customerRates.find(rate =>
            rate.plate_size_id === item.plate_size_id
          );

          // Get base rates for fallback
          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;
          const hasBaking = item.description.toLowerCase().includes('baking');

          // Use stored rate from database if available, otherwise calculate from customer rates
          let finalRate;
          if (item.rate && item.rate > 0) {
            // Use the stored rate from the database (this is the rate * colours that was saved)
            finalRate = item.rate;
          } else {
            // Fall back to calculating from customer rates
            finalRate = hasBaking ? plateRate + bakingRate : plateRate;
          }

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: finalRate, // Use the finalRate (either stored or calculated)
            amount: item.amount,
            description: item.description,
             withBaking: hasBaking,
            // Add flag to indicate this is from stored data  
            useStoredRate: !!(item.rate && item.rate > 0)
          };
        });

        // Format invoice data
        const formattedInvoiceData = {
          invoice_number: invoiceDetails.invoice_number,
          invoice_date: invoiceDetails.invoice_date,
          due_date: invoiceDetails.due_date,
          delivery_challan_ref: invoiceDetails.delivery_challan_ref,
          subtotal: invoiceDetails.subtotal,
          cgst: invoiceDetails.cgst,
          sgst: invoiceDetails.sgst,
          grand_total: invoiceDetails.grand_total
        };

        const transformData = async (itemsData) => {
          // Assuming you have a function to fetch job details by job_id
          const getJobDetails = async (jobId) => {
            // Replace this with your actual API call or database query
            return {
              job_id: jobId,
              quantity: 1,
              job_name: "Job Name", // This should come from your database
              remark: "",
              challan_no: jobId // This should come from your database
            };
          };

          const transformedData = await Promise.all(itemsData.map(async (item) => {
            // Fetch job details for each job ID
            const jobPromises = item.jobIds.map(jobId => getJobDetails(jobId));
            const jobs = await Promise.all(jobPromises);

            // Remove .0 from plateSize if present
            const plateSize = item.plateSize.replace('.0', '');

            return {
              ...item,
              plateSize,
              jobs
            };
          }));

          return transformedData;
        };

        const finalData = await transformData(itemsData);

        // Generate PDF with auto-printing enabled
        await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          finalData,
          customerRates,
          true // Auto-print enabled
        );

      } catch (error) {
        console.error('Error printing invoice:', error);
        alert('Error printing invoice. Please try again.');
      } finally {
        this.loading = false;
      }
    },
    // Helper methods
    async getCustomerById(customerId) {
      // First check if we already have the customer data locally
      const customer = this.customers.find(c => c.id === customerId);
      if (customer) {
        return customer;
      }

      // Otherwise fetch from API
      try {
        const response = await axios.get(`/customers/${customerId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching customer:', error);
        return { company_name: 'Unknown Customer' };
      }
    },
    async getInvoiceDetails(invoiceId) {
      try {
        const response = await axios.get(`/invoices/${invoiceId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching invoice details:', error);
        throw error;
      }
    },
    async getCustomerRates(customerId) {
      try {
        const response = await axios.get(`/customer-rates/${customerId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching customer rates:', error);
        return [];
      }
    },
    async updateStatus(invoice) {
      try {
        const newStatus = invoice.status === 'paid' ? 'unpaid' : 'paid';

        // Use the new PATCH endpoint
        await axios.patch(`/invoices/${invoice.id}/status`, {
          status: newStatus
        });

        this.fetchInvoices();
      } catch (error) {
        console.error('Error updating invoice status:', error);
      }
    },
    async deleteInvoice(invoice) {
      if (confirm(`Are you sure you want to delete invoice ${invoice.invoice_number}? This action cannot be undone.`)) {
        try {
          this.loading = true;
          await axios.delete(`/invoices/${invoice.id}`);
          alert('Invoice deleted successfully.');
          // Refresh the list
          this.fetchInvoices();
        } catch (error) {
          console.error('Error deleting invoice:', error);
          alert('Error deleting invoice. Please try again.');
        } finally {
          this.loading = false;
        }
      }
    },
    showEmailModal(invoice) {
      this.selectedInvoice = invoice;

      // Get customer details
      this.getCustomerById(invoice.customer_id).then(customer => {
        this.selectedCustomerName = customer.company_name;
        this.selectedCustomerEmail = customer.email || '';

        // Pre-populate email data
        this.emailData = {
          subject: `Invoice ${invoice.invoice_number} from New Way Typesetters and Processors`,
          message: `Dear ${customer.contact_person || 'Customer'},\n\nPlease find attached invoice ${invoice.invoice_number} for your records.\n\nThank you for your business.\n\nRegards,\nAccounts Department\nNew Way Typesetters and Processors`,
          includePdf: true
        };

        this.showEmailModalFlag = true;
      });
    },
    closeEmailModal() {
      this.showEmailModalFlag = false;
      this.selectedInvoice = null;
      this.selectedCustomerName = '';
      this.selectedCustomerEmail = '';
      this.emailData = {
        subject: '',
        message: '',
        includePdf: true
      };
    },
    async sendEmail() {
      try {
        this.isSending = true;

        // Fetch required data
        const [customerData, invoiceDetails, customerRates] = await Promise.all([
          this.getCustomerById(this.selectedInvoice.customer_id),
          this.getInvoiceDetails(this.selectedInvoice.id),
          this.getCustomerRates(this.selectedInvoice.customer_id)
        ]);

        // Process invoice items
        const itemsData = invoiceDetails.items.map(item => {
          // Find customer rate for this plate size
          const customerRate = customerRates.find(rate =>
            rate.plate_size_id === item.plate_size_id
          );

          // Get base rates for fallback
          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;
          const hasBaking = item.description.toLowerCase().includes('baking');

          // Use stored rate from database if available, otherwise calculate from customer rates
          let finalRate;
          if (item.rate && item.rate > 0) {
            // Use the stored rate from the database (this is the rate * colours that was saved)
            finalRate = item.rate;
          } else {
            // Fall back to calculating from customer rates
            finalRate = hasBaking ? plateRate + bakingRate : plateRate;
          }

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: finalRate, // Use the finalRate (either stored or calculated)
            amount: item.amount,
            description: item.description,
            withBaking: hasBaking,
            // Add flag to indicate this is from stored data
            useStoredRate: !!(item.rate && item.rate > 0)
          };
        });

        // Format invoice data
        const formattedInvoiceData = {
          invoice_number: invoiceDetails.invoice_number,
          invoice_date: invoiceDetails.invoice_date,
          due_date: invoiceDetails.due_date,
          delivery_challan_ref: invoiceDetails.delivery_challan_ref,
          subtotal: invoiceDetails.subtotal,
          cgst: invoiceDetails.cgst,
          sgst: invoiceDetails.sgst,
          grand_total: invoiceDetails.grand_total
        };

        const transformData = async (itemsData) => {
          // Assuming you have a function to fetch job details by job_id
          const getJobDetails = async (jobId) => {
            // Replace this with your actual API call or database query
            return {
              job_id: jobId,
              quantity: 1,
              job_name: "Job Name", // This should come from your database
              remark: "",
              challan_no: jobId // This should come from your database
            };
          };

          const transformedData = await Promise.all(itemsData.map(async (item) => {
            // Fetch job details for each job ID
            const jobPromises = item.jobIds.map(jobId => getJobDetails(jobId));
            const jobs = await Promise.all(jobPromises);

            // Remove .0 from plateSize if present
            const plateSize = item.plateSize.replace('.0', '');

            return {
              ...item,
              plateSize,
              jobs
            };
          }));

          return transformedData;
        };

        const finalData = await transformData(itemsData);

        // Generate PDF
        const pdfBlob = await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          finalData,
          customerRates,
          false // Don't auto-print
        );

        // Create FormData with the PDF
        const formData = new FormData();
        formData.append('invoice_id', this.selectedInvoice.id);
        formData.append('email', this.selectedCustomerEmail);
        formData.append('subject', this.emailData.subject);
        formData.append('message', this.emailData.message);
        if (this.emailData.includePdf) {
          formData.append('pdf', pdfBlob, 'invoice.pdf');
        }

        // Send email with PDF attachment
        const response = await axios.post('/send-invoice-email', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        alert('Email sent successfully!');
        this.closeEmailModal();
      } catch (error) {
        console.error('Email error details:', error.response?.data);
        alert('Error sending email. Please try again.');
      } finally {
        this.isSending = false;
      }
    },
    goToCustomerEdit() {
      if (this.selectedInvoice && this.selectedInvoice.customer_id) {
        this.$router.push(`/customers/edit/${this.selectedInvoice.customer_id}`);
      }
    },
    openExportModal() {
      this.exportDate = moment().format('YYYY-MM-DD'); // Default to today
      this.showExportModal = true;
    },
    closeExportModal() {
      this.showExportModal = false;
      this.exportDate = '';
      this.isExporting = false;
    },
    async exportToExcel() {
      try {
        this.isExporting = true;
        
        // Fetch invoices for the selected date
        const queryParams = new URLSearchParams();
        queryParams.append('date', this.exportDate);
        queryParams.append('per_page', '1000'); // Get all invoices for the date
        
        const response = await axios.get(`/invoices?${queryParams.toString()}`);
        let invoices = response.data.invoices;
        
        if (invoices.length === 0) {
          alert('No invoices found for the selected date.');
          return;
        }
        
        // Sort invoices by invoice number in ascending order
        invoices = invoices.sort((a, b) => {
          // Extract numeric part from invoice numbers for proper sorting
          const numA = parseInt(a.invoice_number.replace(/\D/g, '')) || 0;
          const numB = parseInt(b.invoice_number.replace(/\D/g, '')) || 0;
          return numA - numB;
        });
        
        // Process each invoice to get detailed data
        const exportData = [];
        
        for (const invoice of invoices) {
          const [customerData, invoiceDetails] = await Promise.all([
            this.getCustomerById(invoice.customer_id),
            this.getInvoiceDetails(invoice.id)
          ]);
          
          // Map invoice data to Tally format
          const mappedData = this.mapInvoiceToTallyFormat(invoice, customerData, invoiceDetails);
          exportData.push(...mappedData);
        }
        
        // Create Excel file
        this.createExcelFile(exportData);
        
        this.closeExportModal();
        
      } catch (error) {
        console.error('Error exporting to Excel:', error);
        alert('Error exporting invoices. Please try again.');
      } finally {
        this.isExporting = false;
      }
    },
    
    mapInvoiceToTallyFormat(invoice, customer, invoiceDetails) {
      console.log(invoice)
      const exportRows = [];
      const invoiceDate = moment(invoice.invoice_date).format('DD-MM-YYYY');
      const customerAddress = `${customer.address || ''}, ${customer.city || ''}, ${customer.state || ''} ${customer.pin_code || ''}`.replace(/^,\s*|,\s*$/, '');
      
      // Calculate actual subtotal from items
      const actualSubtotal = invoiceDetails.items.reduce((sum, item) => sum + item.amount, 0);
      const cgst = invoice.cgst_amount || 0;
      const sgst = invoice.sgst_amount || 0;
      const calculatedTotal = actualSubtotal + cgst + sgst;
      const roundingAdjustment = invoice.grand_total - calculatedTotal;
      
      // 1. Main customer debit entry
      exportRows.push({
        'Voucher Date': invoiceDate,
        'Voucher Type Name': 'Sales',
        'Voucher Number': invoice.invoice_number,
        'Buyer/Supplier - Address': customerAddress,
        'Ledger Name': customer.company_name,
        'Ledger Amount': invoice.grand_total, // Total invoice value
        'Ledger Amount Dr/Cr': 'Dr', // Positive for debit (customer owes us)
        'Item Allocations - Godown Name': 'Main Location',
        'Item Name': '',
        'Item Description': '',
        'Billed Quantity': '',
        'Item Rate': '',
        'Item Rate per': '',
        'Item Amount': '',
        'Change Mode': 'Item Invoice'
      });
      
      // 2. Individual item sales entries (credits)
      invoiceDetails.items.forEach(item => {
        // Use job_ids (challan IDs) as Item Description
        const challanIds = item.job_ids || '';
        
        exportRows.push({
          'Voucher Date': invoiceDate,
          'Voucher Type Name': 'Sales',
          'Voucher Number': invoice.invoice_number,
          'Buyer/Supplier - Address': customerAddress,
          'Ledger Name': 'CTP SALE @18% GST',
          'Ledger Amount': item.amount, // Item amount (will be negative for credit)
          'Ledger Amount Dr/Cr': 'Cr', // Negative for credit (sales)
          'Item Allocations - Godown Name': 'Main Location',
          'Item Name': item.description,
          'Item Description': challanIds, // Using challan IDs instead of description
          'Billed Quantity': item.quantity,
          'Item Rate': item.rate,
          'Item Rate per': 'NO',
          'Item Amount': item.amount,
          'Change Mode': 'Item Invoice'
        });
      });
      
      // 3. CGST Entry (credit)
      if (invoice.cgst_amount > 0) {
        exportRows.push({
          'Voucher Date': invoiceDate,
          'Voucher Type Name': 'Sales',
          'Voucher Number': invoice.invoice_number,
          'Buyer/Supplier - Address': customerAddress,
          'Ledger Name': 'OUTPUT CGST @09% - CENTRAL TAX',
          'Ledger Amount': invoice.cgst_amount,
          'Ledger Amount Dr/Cr': 'Cr', // Credit
          'Item Allocations - Godown Name': 'Main Location',
          'Item Name': '',
          'Item Description': '',
          'Billed Quantity': '',
          'Item Rate': '',
          'Item Rate per': '',
          'Item Amount': '',
          'Change Mode': 'Item Invoice'
        });
      }
      
      // 4. SGST Entry (credit)
      if (invoice.sgst_amount > 0) {
        exportRows.push({
          'Voucher Date': invoiceDate,
          'Voucher Type Name': 'Sales',
          'Voucher Number': invoice.invoice_number,
          'Buyer/Supplier - Address': customerAddress,
          'Ledger Name': 'OUTPUT SGST @09% - STATE TAX',
          'Ledger Amount': invoice.sgst_amount,
          'Ledger Amount Dr/Cr': 'Cr', // Credit
          'Item Allocations - Godown Name': 'Main Location',
          'Item Name': '',
          'Item Description': '',
          'Billed Quantity': '',
          'Item Rate': '',
          'Item Rate per': '',
          'Item Amount': '',
          'Change Mode': 'Item Invoice'
        });
      }
      
      // 5. Round Up entry (if applicable) - Calculate dynamically
      if (Math.abs(roundingAdjustment) > 0.01) { // Only include if rounding is significant (more than 1 paisa)
        exportRows.push({
          'Voucher Date': invoiceDate,
          'Voucher Type Name': 'Sales',
          'Voucher Number': invoice.invoice_number,
          'Buyer/Supplier - Address': customerAddress,
          'Ledger Name': 'ROUND UP',
          'Ledger Amount': Math.abs(roundingAdjustment).toFixed(2),
          'Ledger Amount Dr/Cr': roundingAdjustment > 0 ? 'Cr' : 'Dr',
          'Item Allocations - Godown Name': 'Main Location',
          'Item Name': '',
          'Item Description': '',
          'Billed Quantity': '',
          'Item Rate': '',
          'Item Rate per': '',
          'Item Amount': '',
          'Change Mode': 'Item Invoice'
        });
      }
      
      return exportRows;
    },
    
    createExcelFile(data) {
      // Create a new workbook
      const wb = XLSX.utils.book_new();
      
      // Create worksheet from data
      const ws = XLSX.utils.json_to_sheet(data);
      
      // Set column widths to match the required format
      const colWidths = [
        { wch: 12 }, // Voucher Date
        { wch: 18 }, // Voucher Type Name
        { wch: 18 }, // Voucher Number
        { wch: 35 }, // Buyer/Supplier - Address
        { wch: 30 }, // Ledger Name
        { wch: 15 }, // Ledger Amount
        { wch: 12 }, // Ledger Amount Dr/Cr
        { wch: 20 }, // Item Allocations - Godown Name
        { wch: 25 }, // Item Name
        { wch: 25 }, // Item Description
        { wch: 12 }, // Billed Quantity
        { wch: 12 }, // Item Rate
        { wch: 12 }, // Item Rate per
        { wch: 15 }, // Item Amount
        { wch: 15 }  // Change Mode
      ];
      ws['!cols'] = colWidths;
      
      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Accounting Vouchers');
      
      // Generate filename with selected date
      const selectedDate = moment(this.exportDate).format('DD_MM_YYYY');
      const fileName = `AccountingVouchers_${selectedDate}.xlsx`;
      
      // Trigger download
      XLSX.writeFile(wb, fileName);
    }
  },
  mounted() {
    this.userRole = this.$store?.state?.user?.role || '';
    this.fetchInvoices();
    this.fetchCustomers();
  },
};
</script>
