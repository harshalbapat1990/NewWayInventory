<template>
  <div class="p-6 bg-gray-50 rounded-lg shadow-md">
    <h1 class="text-2xl font-bold mb-2 text-gray-800">Archive Manager</h1>
    <p class="text-sm text-gray-500 mb-6">
      Archive all records (challans, invoices, purchases, waste) for a past financial year.
      Archived records are hidden from normal views but can be restored at any time.
    </p>

    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <p class="mt-2 text-gray-600">Loading...</p>
    </div>

    <div v-else>
      <div v-if="years.length === 0" class="text-gray-500 py-8 text-center">
        No financial year data found.
      </div>

      <table v-else class="table-auto w-full border-collapse border border-gray-300 text-sm">
        <thead>
          <tr class="bg-gray-200">
            <th class="border border-gray-300 px-4 py-2 text-left">Financial Year</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Challans</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Invoices</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Purchases</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Waste Plates</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Status</th>
            <th class="border border-gray-300 px-4 py-2 text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in years" :key="row.financial_year"
              :class="row.is_archived ? 'bg-orange-50' : 'bg-white'">
            <td class="border border-gray-300 px-4 py-2 font-semibold">
              {{ fyLabel(row.financial_year) }}
            </td>
            <td class="border border-gray-300 px-4 py-2 text-center">
              {{ row.challans }}
              <span v-if="row.is_archived" class="text-xs text-orange-600 ml-1">({{ row.archived_challans }} archived)</span>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-center">
              {{ row.invoices }}
              <span v-if="row.is_archived" class="text-xs text-orange-600 ml-1">({{ row.archived_invoices }} archived)</span>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-center">{{ row.purchases }}</td>
            <td class="border border-gray-300 px-4 py-2 text-center">{{ row.waste_plates }}</td>
            <td class="border border-gray-300 px-4 py-2 text-center">
              <span v-if="row.is_archived"
                class="bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                Archived
              </span>
              <span v-else
                class="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                Active
              </span>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-center">
              <button v-if="!row.is_archived"
                @click="confirmArchive(row)"
                :disabled="actionLoading === row.financial_year"
                class="btn-danger mr-2">
                {{ actionLoading === row.financial_year ? 'Archiving...' : 'Archive' }}
              </button>
              <button v-else
                @click="confirmRestore(row)"
                :disabled="actionLoading === row.financial_year"
                class="btn-primary">
                {{ actionLoading === row.financial_year ? 'Restoring...' : 'Restore' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="confirmModal.show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-bold mb-3 text-gray-800">{{ confirmModal.title }}</h2>
        <p class="text-sm text-gray-600 mb-6">{{ confirmModal.message }}</p>
        <div class="flex justify-end gap-3">
          <button @click="confirmModal.show = false" class="btn-secondary">Cancel</button>
          <button @click="executeAction" :class="confirmModal.isArchive ? 'btn-danger' : 'btn-primary'">
            {{ confirmModal.isArchive ? 'Archive' : 'Restore' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Un-invoiced Warning Modal -->
    <div v-if="warningModal.show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg">
        <h2 class="text-lg font-bold mb-2 text-orange-700">⚠ Un-invoiced Challans Found</h2>
        <p class="text-sm text-gray-700 mb-3">{{ warningModal.warning }}</p>
        <p class="text-sm text-gray-600 mb-2">The following challans have no invoice yet:</p>
        <div class="bg-orange-50 border border-orange-200 rounded p-3 mb-4 max-h-40 overflow-y-auto text-xs font-mono text-orange-900">
          <div v-for="c in warningModal.uninvoicedChallans" :key="c">{{ c }}</div>
        </div>
        <p class="text-xs text-gray-500 mb-4">
          You can still generate invoices for these challans from <strong>Customer Summary</strong> after archiving (archived challans are always included in invoice generation). Or cancel and generate invoices first.
        </p>
        <div class="flex justify-end gap-3">
          <button @click="warningModal.show = false" class="btn-secondary">Cancel — Generate Invoices First</button>
          <button @click="forceArchive" class="btn-danger">Archive Anyway</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../../axios';

export default {
  name: 'ArchiveManager',
  data() {
    return {
      years: [],
      loading: false,
      actionLoading: null,
      confirmModal: {
        show: false,
        title: '',
        message: '',
        fy: null,
        isArchive: true,
        force: false
      },
      warningModal: {
        show: false,
        fy: null,
        warning: '',
        uninvoicedChallans: []
      }
    };
  },
  methods: {
    fyLabel(fy) {
      if (!fy || fy.length !== 4) return fy;
      return `20${fy.slice(0, 2)}-20${fy.slice(2)}`;
    },
    async fetchYears() {
      this.loading = true;
      try {
        const response = await axios.get('/archive/years');
        this.years = response.data;
      } catch (e) {
        console.error('Error fetching archive years:', e);
        alert('Failed to load financial year data.');
      } finally {
        this.loading = false;
      }
    },
    confirmArchive(row) {
      this.confirmModal = {
        show: true,
        title: `Archive FY ${this.fyLabel(row.financial_year)}?`,
        message: `This will archive ${row.challans} challan(s), ${row.invoices} invoice(s), ${row.purchases} purchase(s) and ${row.waste_plates} waste record(s) for ${this.fyLabel(row.financial_year)}. They will be hidden from all standard views but can be restored at any time.`,
        fy: row.financial_year,
        isArchive: true
      };
    },
    confirmRestore(row) {
      this.confirmModal = {
        show: true,
        title: `Restore FY ${this.fyLabel(row.financial_year)}?`,
        message: `This will restore all archived records for ${this.fyLabel(row.financial_year)} and make them visible in standard views again.`,
        fy: row.financial_year,
        isArchive: false
      };
    },
    async executeAction() {
      const { fy, isArchive, force } = this.confirmModal;
      this.confirmModal.show = false;
      this.actionLoading = fy;
      try {
        const url = isArchive
          ? `/archive/${fy}${force ? '?force=true' : ''}`
          : `/archive/${fy}/restore`;
        const response = await axios.post(url);
        alert(response.data.message);
        await this.fetchYears();
      } catch (e) {
        if (e.response && e.response.status === 409) {
          // Un-invoiced challans warning
          const data = e.response.data;
          this.warningModal = {
            show: true,
            fy,
            warning: data.warning,
            uninvoicedChallans: data.uninvoiced_challans || []
          };
        } else {
          console.error('Archive action failed:', e);
          alert('Action failed. Please try again.');
        }
      } finally {
        this.actionLoading = null;
      }
    },
    forceArchive() {
      const { fy } = this.warningModal;
      this.warningModal.show = false;
      this.confirmModal = {
        show: false,
        title: '',
        message: '',
        fy,
        isArchive: true,
        force: true
      };
      // Execute directly with force
      this.actionLoading = fy;
      axios.post(`/archive/${fy}?force=true`)
        .then(r => {
          alert(r.data.message);
          return this.fetchYears();
        })
        .catch(e => {
          console.error('Force archive failed:', e);
          alert('Archive failed. Please try again.');
        })
        .finally(() => { this.actionLoading = null; });
    }
  },
  mounted() {
    this.fetchYears();
  }
};
</script>

<style scoped>
.btn-primary {
  background-color: #007bff;
  color: white;
  padding: 0.4rem 0.9rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.8rem;
}
.btn-primary:hover:not(:disabled) { background-color: #0056b3; }
.btn-danger {
  background-color: #dc3545;
  color: white;
  padding: 0.4rem 0.9rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.8rem;
}
.btn-danger:hover:not(:disabled) { background-color: #a71d2a; }
.btn-secondary {
  background-color: #6c757d;
  color: white;
  padding: 0.4rem 0.9rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.8rem;
}
.btn-secondary:hover:not(:disabled) { background-color: #545b62; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
