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
      </div>
    </div>

    <!-- Invoice Table -->
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
        <tr v-for="invoice in invoices" :key="invoice.id" 
            :class="{
              'bg-green-50': invoice.status === 'paid',
              'bg-red-50': invoice.status === 'cancelled',
              'bg-yellow-50': invoice.status === 'unpaid'
            }">
          <td class="border border-gray-300 px-4 py-2">{{ invoice.invoice_number }}</td>
          <td class="border border-gray-300 px-4 py-2">{{ formatDate(invoice.invoice_date) }}</td>
          <td class="border border-gray-300 px-4 py-2">{{ invoice.customer_name }}</td>
          <td class="border border-gray-300 px-4 py-2">₹{{ formatAmount(invoice.grand_total) }}</td>
          <td class="border border-gray-300 px-4 py-2">
            <span 
              :class="{
                'bg-green-100 text-green-800': invoice.status === 'paid',
                'bg-red-100 text-red-800': invoice.status === 'cancelled',
                'bg-yellow-100 text-yellow-800': invoice.status === 'unpaid'
              }"
              class="px-2 py-1 rounded-full"
            >
              {{ capitalizeFirstLetter(invoice.status) }}
            </span>
          </td>
          <td class="border border-gray-300 px-4 py-2">
            <button @click="viewInvoice(invoice)" class="btn-primary mr-2">View</button>
            <button @click="printInvoice(invoice)" class="btn-print mr-2">Print</button>
            <button @click="showEmailModal(invoice)" class="btn-email mr-2">
              <i class="fas fa-envelope mr-1"></i> Email
            </button>
            <button @click="updateStatus(invoice)" class="btn-secondary mr-2" v-if="userRole === 'admin' || userRole === 'accountant'">
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
          <input
            id="email-subject"
            v-model="emailData.subject"
            type="text"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div class="mb-4">
          <label for="email-message" class="block text-sm font-medium text-gray-700 mb-1">Message</label>
          <textarea
            id="email-message"
            v-model="emailData.message"
            rows="9"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          ></textarea>
        </div>
        
        <div class="mb-4">
          <label class="inline-flex items-center">
            <input type="checkbox" v-model="emailData.includePdf" class="form-checkbox h-5 w-5 text-blue-600">
            <span class="ml-2 text-gray-700">Attach invoice PDF</span>
          </label>
        </div>
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button 
          @click="closeEmailModal" 
          class="btn-secondary"
        >
          Cancel
        </button>
        <button 
          @click="sendEmail" 
          class="btn-primary"
          :disabled="isSending || !selectedCustomerEmail"
        >
          {{ isSending ? 'Sending...' : 'Send Email' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';
import moment from 'moment';
import { printTaxInvoice } from '../../utils/printTaxInvoice';
import { generatePDF } from '../../utils/generatePDF'; // Create this utility function

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
      userRole: '',
      loading: false,
      showEmailModalFlag: false,
      selectedInvoice: null,
      selectedCustomerEmail: '',
      selectedCustomerName: '',
      emailData: {
        subject: '',
        message: '',
        includePdf: true
      },
      isSending: false
    };
  },
  methods: {
    async fetchInvoices() {
      this.loading = true;
      try {
        const queryParams = new URLSearchParams();
        
        // Clean and validate invoice number filter
        if (this.filters.invoiceNumber && this.filters.invoiceNumber.trim()) {
          queryParams.append('invoice_number', this.filters.invoiceNumber.trim());
        }
        
        // Validate date filter
        if (this.filters.invoiceDate) {
          // Ensure date is in YYYY-MM-DD format
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
        
        // Log the full URL with query parameters for debugging
        const url = `/invoices${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        
        const response = await axios.get(url);
        
        // Sort invoices in descending order
        this.invoices = response.data.sort((a, b) => {
          const dateA = new Date(a.invoice_date);
          const dateB = new Date(b.invoice_date);
          
          // First sort by date (newest first)
          if (dateB - dateA !== 0) {
            return dateB - dateA;
          }
          
          // If dates are the same, sort by financial year and sequence (newest first)
          if (a.financial_year !== b.financial_year) {
            return b.financial_year - a.financial_year;
          }
          
          // Finally sort by sequence number
          return b.invoice_sequence - a.invoice_sequence;
        });
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
    applyFilters() {
      // Perform validation before fetching
      if (this.filters.invoiceDate) {
        try {
          // Ensure it's a valid date format (YYYY-MM-DD)
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
      this.fetchInvoices();
    },
    clearFilters() {
      this.filters = {
        invoiceNumber: '',
        invoiceDate: '',
        customerId: '',
        status: ''
      };
      this.fetchInvoices();
    },
    async viewInvoice(invoice) {
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
          
          // Get base rates
          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;

          // Check if item includes baking
          const hasBaking = item.description.toLowerCase().includes('baking');

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: hasBaking ? plateRate + bakingRate : plateRate,
            amount: item.amount,
            description: item.description,
            withBaking: hasBaking
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

        // Generate PDF without auto-printing
        await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          itemsData,
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
          
          // Get base rates
          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;

          // Check if item includes baking
          const hasBaking = item.description.toLowerCase().includes('baking');

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: hasBaking ? plateRate + bakingRate : plateRate,
            amount: item.amount,
            description: item.description,
            withBaking: hasBaking
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

        // Generate PDF with auto-printing enabled
        await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          itemsData,
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
          
          // Get base rates
          const plateRate = customerRate?.plate_rate || 0;
          const bakingRate = customerRate?.baking_rate || 0;

          // Check if item includes baking
          const hasBaking = item.description.toLowerCase().includes('baking');

          return {
            plateSize: item.plate_size,
            plateSizeId: item.plate_size_id,
            colours: parseInt(item.colours),
            jobIds: item.job_ids ? item.job_ids.split(',') : [],
            quantity: item.quantity,
            rateType: hasBaking ? 'baking_rate' : 'plate_rate',
            plateRate: plateRate,
            bakingRate: bakingRate,
            rate: hasBaking ? plateRate + bakingRate : plateRate,
            amount: item.amount,
            description: item.description,
            withBaking: hasBaking
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

        // Generate PDF
        const pdfBlob = await printTaxInvoice(
          formattedInvoiceData,
          customerData,
          itemsData,
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

        console.log("Email response:", response);
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
    }
  },
  mounted() {
    this.userRole = this.$store?.state?.user?.role || ''; 
    this.fetchInvoices();
    this.fetchCustomers();
  },
};
</script>
