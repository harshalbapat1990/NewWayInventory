<template>
  <main class="mx-auto max-w-xl p-6">
    <h2 class="mb-4 text-2xl font-semibold">SMTP Settings</h2>
    <p v-if="status" class="mb-4">{{ status.configured ? `Configured as ${status.username}` : 'No SMTP credentials configured' }}</p>
    <form class="space-y-4" @submit.prevent="save">
      <label class="block">SMTP username
        <input v-model.trim="username" required maxlength="254" autocomplete="username" class="mt-1 block w-full rounded border p-2" />
      </label>
      <label class="block">New SMTP password
        <input v-model="password" required type="password" maxlength="512" autocomplete="new-password" class="mt-1 block w-full rounded border p-2" />
      </label>
      <button :disabled="saving" class="rounded bg-blue-700 px-4 py-2 text-white">{{ saving ? 'Checking…' : 'Verify and replace' }}</button>
    </form>
    <p v-if="message" role="status" class="mt-4">{{ message }}</p>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import api from '../../axios';

const status = ref(null);
const username = ref('');
const password = ref('');
const message = ref('');
const saving = ref(false);

onMounted(async () => {
  try {
    const response = await api.get('/settings/smtp');
    status.value = response.data;
    username.value = response.data.username || '';
  } catch {
    message.value = 'SMTP settings could not be loaded.';
  }
});

async function save() {
  saving.value = true;
  message.value = '';
  try {
    const response = await api.put('/settings/smtp', { username: username.value, password: password.value });
    status.value = response.data;
    password.value = '';
    message.value = 'SMTP settings verified and replaced.';
  } catch (error) {
    message.value = error.response?.data?.message || 'SMTP settings could not be verified; saved settings were kept.';
  } finally {
    saving.value = false;
  }
}
</script>
