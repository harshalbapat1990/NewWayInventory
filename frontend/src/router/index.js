import { createRouter, createWebHistory } from 'vue-router';
import store from '../store';
import LandingPage from '../components/LandingPage.vue';
import Login from '../components/Login.vue';
import Register from '../components/Register.vue';
import HomePage from '../components/HomePage.vue';
import Purchase from '../components/menu/Purchase.vue';
import WastePlates from '../components/menu/WastePlates.vue';
import AvailablePlates from '../components/menu/AvailablePlates.vue';
import StockSummary from '../components/menu/StockSummary.vue';
import DateWiseUsedPlates from '../components/menu/DateWiseUsedPlates.vue';
import JobEdition from '../components/menu/JobEdition.vue';
import PurchaseEdition from '../components/menu/PurchaseEdition.vue';
import AddEditCustomer from '../components/menu/AddEditCustomer.vue';
import AdjustStockReview from '../components/menu/AdjustStockReview.vue';
import DeliveryChallan from '../components/menu/DeliveryChallan.vue';
import CreateNewUser from '../components/menu/CreateNewUser.vue';
import NewJob from '../components/menu/NewJob.vue';
import JobsDeliveryChallan from '../components/menu/JobsDeliveryChallan.vue';
import CustomerSummary from '../components/menu/CustomerSummary.vue';
import UserInfo from '../components/menu/UserInfo.vue';
import JobOrderList from '../components/menu/JobOrderList.vue';
import ChallanList from '../components/menu/ChallanList.vue';
import AddEditPlateSize from '../components/menu/AddEditPlateSize.vue';
import CustomerRate from '../components/menu/CustomerRate.vue';
import PastInvoiceList from '../components/menu/PastInvoiceList.vue';

const routes = [
  { path: '/', component: LandingPage },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/home', component: HomePage, meta: { requiresAuth: true } },
  { path: '/purchase', component: Purchase, meta: { requiresAuth: true } },
  { path: '/waste-plates', component: WastePlates, meta: { requiresAuth: true } },
  { path: '/available-plates', component: AvailablePlates, meta: { requiresAuth: true } },
  { path: '/stock-summary', component: StockSummary, meta: { requiresAuth: true } },
  { path: '/date-wise-used-plates', component: DateWiseUsedPlates, meta: { requiresAuth: true } },
  { path: '/job-edition', component: JobEdition, meta: { requiresAuth: true } },
  { path: '/purchase-edition', component: PurchaseEdition, meta: { requiresAuth: true } },
  { path: '/add-edit-customer', component: AddEditCustomer, meta: { requiresAuth: true } },
  { path: '/adjust-stock-review', component: AdjustStockReview, meta: { requiresAuth: true } },
  { path: '/delivery-challan', component: DeliveryChallan, meta: { requiresAuth: true } },
  { path: '/create-new-user', component: CreateNewUser, meta: { requiresAuth: true } },
  { path: '/new-job', component: NewJob, meta: { requiresAuth: true } },
  { path: '/jobs-delivery-challan', component: JobsDeliveryChallan, meta: { requiresAuth: true } },
  { path: '/customer-summary', component: CustomerSummary, meta: { requiresAuth: true } },
  { path: '/user-profile', component: UserInfo, meta: { requiresAuth: true } },
  { path: '/job-orders', component: JobOrderList, meta: { requiresAuth: true } },
  { path: '/challan-list', component: ChallanList, meta: { requiresAuth: true } },
  { path: '/add-edit-plate-sizes', name: 'AddEditPlateSize', component: AddEditPlateSize },
  { path: '/customer-rate', component: CustomerRate, meta: { requiresAuth: true } },
  { path: '/past-invoices', component: PastInvoiceList, meta: { requiresAuth: true } }
  
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // If the route requires authentication
  if (to.meta.requiresAuth) {
    // Use the new checkAuth method that checks both token presence and expiration
    const isAuthenticated = await store.dispatch('checkAuth');
    if (!isAuthenticated) {
      next('/login'); // Redirect to login if not authenticated
    } else {
      // Reset the token expiry timer with the longer duration
      if (store.state.token) {
        const tokenExpiry = Date.now() + (7 * 24 * 60 * 60 * 1000);
        localStorage.setItem('tokenExpiry', tokenExpiry);
        store.state.tokenExpiry = tokenExpiry;
      }
      next();
    }
  } else {
    next();
  }
});

export default router;