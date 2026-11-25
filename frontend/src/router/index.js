import { createRouter, createWebHistory } from 'vue-router';
import store from '../store';
import LandingPage from '../components/LandingPage.vue';
import Login from '../components/Login.vue';
import HomePage from '../components/HomePage.vue';
import Purchase from '../components/menu/Purchase.vue';
import WastePlates from '../components/menu/WastePlates.vue';
import AvailablePlates from '../components/menu/AvailablePlates.vue';
import DateWiseUsedPlates from '../components/menu/DateWiseUsedPlates.vue';
import AddEditCustomer from '../components/menu/AddEditCustomer.vue';
import CreateNewUser from '../components/menu/CreateNewUser.vue';
import JobsDeliveryChallan from '../components/menu/JobsDeliveryChallan.vue';
import CustomerSummary from '../components/menu/CustomerSummary.vue';
import UserInfo from '../components/menu/UserInfo.vue';
import ChallanList from '../components/menu/ChallanList.vue';
import AddEditPlateSize from '../components/menu/AddEditPlateSize.vue';
import CustomerRate from '../components/menu/CustomerRate.vue';
import PastInvoiceList from '../components/menu/PastInvoiceList.vue';
import ArchiveManager from '../components/menu/ArchiveManager.vue';
import SmtpSettings from '../components/menu/SmtpSettings.vue';

const routes = [
  { path: '/', component: LandingPage },
  { path: '/login', component: Login },
  { path: '/home', component: HomePage, meta: { requiresAuth: true } },
  { path: '/purchase', component: Purchase, meta: { requiresAuth: true } },
  { path: '/waste-plates', component: WastePlates, meta: { requiresAuth: true } },
  { path: '/available-plates', component: AvailablePlates, meta: { requiresAuth: true } },
  { path: '/stock-summary', redirect: '/available-plates' },
  { path: '/date-wise-used-plates', component: DateWiseUsedPlates, meta: { requiresAuth: true } },
  { path: '/purchase-edition', redirect: '/purchase' },
  { path: '/add-edit-customer', component: AddEditCustomer, meta: { requiresAuth: true, roles: ['editor', 'admin'] } },
  { path: '/create-new-user', component: CreateNewUser, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/job-edition', redirect: '/jobs-delivery-challan' },
  { path: '/delivery-challan', redirect: '/jobs-delivery-challan' },
  { path: '/new-job', redirect: '/jobs-delivery-challan' },
  { path: '/jobs-delivery-challan', component: JobsDeliveryChallan, meta: { requiresAuth: true } },
  { path: '/customer-summary', component: CustomerSummary, meta: { requiresAuth: true } },
  { path: '/user-profile', component: UserInfo, meta: { requiresAuth: true } },
  { path: '/job-orders', redirect: '/challan-list' },
  { path: '/challan-list', component: ChallanList, meta: { requiresAuth: true } },
  { path: '/add-edit-plate-sizes', name: 'AddEditPlateSize', component: AddEditPlateSize, meta: { requiresAuth: true, roles: ['editor', 'admin'] } },
  { path: '/customer-rate', component: CustomerRate, meta: { requiresAuth: true, roles: ['accountant', 'admin'] } },
  { path: '/past-invoices', component: PastInvoiceList, meta: { requiresAuth: true, roles: ['accountant', 'admin'] } },
  { path: '/archive-manager', component: ArchiveManager, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/smtp-settings', component: SmtpSettings, meta: { requiresAuth: true, roles: ['accountant', 'admin'] } }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // If the route requires authentication
  if (to.meta.requiresAuth) {
    const isAuthenticated = await store.dispatch('checkAuth');
    if (!isAuthenticated) {
      next('/login'); // Redirect to login if not authenticated
    } else {
      if (to.meta.role && store.state.user?.role !== to.meta.role) {
        next('/home');
        return;
      }
      if (to.meta.roles && !to.meta.roles.includes(store.state.user?.role)) {
        next('/home');
        return;
      }
      next();
    }
  } else {
    next();
  }
});

export default router;
