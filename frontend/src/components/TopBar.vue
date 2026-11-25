<template>
  <div class="top-bar flex items-center justify-between bg-gray-800 text-white p-4" @click="closeMenu">
    <h1 class="text-xl text-[#7393b3]">New Way - Inventory Management</h1>
    <div v-if="isLoggedIn" class="flex space-x-4">
      <div class="relative" @click.stop>
        <button @click="toggleMenu('inventory')" class="text-[#7393b3]">Inventory Menu</button>
        <ul v-if="activeMenu === 'inventory'" class="absolute bg-white text-black mt-2 rounded shadow-lg">
          <li v-for="(item, index) in inventoryMenuItems" :key="index" @click="navigateTo(item.route)" class="px-4 py-2 hover:bg-gray-200 cursor-pointer">
            {{ item.title }}
          </li>
        </ul>
      </div>
      <div class="relative" @click.stop>
        <button @click="toggleMenu('admin')" class="text-[#7393b3]">Administration Menu</button>
        <ul v-if="activeMenu === 'admin'" class="absolute bg-white text-black mt-2 rounded shadow-lg">
          <li
            v-for="(item, index) in filteredAdminMenuItems"
            :key="index"
            @click="navigateTo(item.route)"
            class="px-4 py-2 hover:bg-gray-200 cursor-pointer"
          >
            {{ item.title }}
          </li>
        </ul>
      </div>
      <div class="relative" @click.stop>
        <button @click="toggleMenu('jobs')" class="text-[#7393b3]">Jobs Menu</button>
        <ul v-if="activeMenu === 'jobs'" class="absolute bg-white text-black mt-2 rounded shadow-lg">
          <li v-for="(item, index) in filteredJobsMenuItems" :key="index" @click="navigateTo(item.route)" class="px-4 py-2 hover:bg-gray-200 cursor-pointer">
            {{ item.title }}
          </li>
        </ul>
      </div>
      <div class="relative" @click.stop>
        <button @click="toggleMenu('user')" class="text-[#7393b3]">User Menu</button>
        <ul v-if="activeMenu === 'user'" class="absolute bg-white text-black mt-2 rounded shadow-lg">
          <li @click="navigateTo('/user-profile')" class="px-4 py-2 hover:bg-gray-200 cursor-pointer">User Profile</li>
          <li @click="user_logout" class="px-4 py-2 hover:bg-gray-200 cursor-pointer">Logout</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapState } from 'vuex';

export default {
  data() {
    return {
      activeMenu: null,
      inventoryMenuItems: [
        { title: 'Purchase', route: '/purchase' },
        { title: 'Waste Plates', route: '/waste-plates' },
        { title: 'Available Plates', route: '/available-plates' },
        { title: 'Date Wise Used Plates', route: '/date-wise-used-plates' } // Uncommented menu item
      ],
      adminMenuItems: [
        { title: 'Add/Edit Customer', route: '/add-edit-customer', roles: ['editor', 'admin'] },
        { title: 'Add/Edit Plate Sizes', route: '/add-edit-plate-sizes', roles: ['editor', 'admin'] },
        { title: 'Add/Edit Customer Rate', route: '/customer-rate', roles: ['accountant', 'admin'] },
        { title: 'SMTP Settings', route: '/smtp-settings', roles: ['accountant', 'admin'] },
        { title: 'Create User', route: '/create-new-user', roles: ['admin'] },
        { title: 'Archive Manager', route: '/archive-manager', roles: ['admin'] },
      ],
      jobsMenuItems: [
        { title: 'New Delivery Challan', route: '/jobs-delivery-challan' },
        { title: 'Challan List', route: '/challan-list' }, // Add Challan List menu item
        { title: 'Customer Summary', route: '/customer-summary' },
        { title: 'Past Invoices', route: '/past-invoices', roles: ['accountant', 'admin'] },
      ]
    };
  },
  computed: {
    ...mapState(['user']),
    isLoggedIn() {
      return !!this.user;
    },
    userRole() { return this.user?.role || ''; },
    filteredAdminMenuItems() {
      // Filter admin menu items based on user role
      return this.adminMenuItems.filter(item => !item.roles || item.roles.includes(this.userRole));
    },
    filteredJobsMenuItems() {
      // Filter jobs menu items based on user role
      return this.jobsMenuItems.filter(item => !item.roles || item.roles.includes(this.userRole));
    }
  },
  methods: {
    ...mapActions(['logout']),
    toggleMenu(menu) {
      this.activeMenu = this.activeMenu === menu ? null : menu;
    },
    navigateTo(route) {
      this.$router.push(route);
      this.activeMenu = null;
    },
    closeMenu() {
      this.activeMenu = null;
    },
    async user_logout() {
      await this.logout(); // Call the Vuex logout action
      this.$router.push('/'); // Redirect to the base URL
    }
  }
};
</script>
