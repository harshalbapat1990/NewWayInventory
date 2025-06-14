<!-- filepath: frontend/src/components/menu/JobEdition.vue -->
<template>
  <div class="job-edition">
    <h1 class="text-xl font-bold mb-4">Job Edition</h1>
    <form @submit.prevent="addJob">
      <div class="mb-4">
        <label for="jobName" class="block text-sm font-medium text-gray-700">Job Name</label>
        <input type="text" id="jobName" v-model="jobName" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <div class="mb-4">
        <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
        <textarea id="description" v-model="description" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required></textarea>
      </div>
      <div class="mb-4">
        <label for="date" class="block text-sm font-medium text-gray-700">Date</label>
        <input type="date" id="date" v-model="date" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" required>
      </div>
      <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Add Job</button>
    </form>
    <table class="min-w-full divide-y divide-gray-200 mt-8">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Name</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="(job, index) in jobs" :key="index">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ job.jobName }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ job.description }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ job.date }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      jobName: '',
      description: '',
      date: '',
      jobs: []
    };
  },
  methods: {
    async fetchJobs() {
      try {
        const response = await axios.get('/api/jobs');
        this.jobs = response.data;
      } catch (error) {
        console.error('Error fetching jobs:', error);
      }
    },
    async addJob() {
      const newJob = {
        jobName: this.jobName,
        description: this.description,
        date: this.date
      };
      try {
        const response = await axios.post('/api/jobs', newJob);
        this.jobs.push(response.data);
        this.jobName = '';
        this.description = '';
        this.date = '';
      } catch (error) {
        console.error('Error adding job:', error);
      }
    }
  },
  mounted() {
    this.fetchJobs();
  }
};
</script>

<style scoped>
/* Add any styles here */
</style>