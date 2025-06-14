<template>
    <div class="login-page flex items-center justify-center h-screen bg-gray-100">
        <div class="bg-white p-8 rounded-md shadow-md w-full max-w-md">
            <h2 class="text-2xl font-bold mb-4">Login</h2>
            <form @submit.prevent="user_login">
                <div class="mb-4">
                    <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
                    <input
                        type="text"
                        id="username"
                        v-model="username"
                        class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        required
                    />
                </div>
                <div class="mb-4">
                    <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                    <input
                        type="password"
                        id="password"
                        v-model="password"
                        class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        required
                    />
                </div>
                <div class="flex justify-center gap-4">
                    <button
                        type="submit"
                        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Login
                    </button>
                    <button
                        type="button"
                        @click="cancel"
                        class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Cancel
                    </button>
                </div>
            </form>
            <div class="mt-4 text-center">
                <a href="/reset-password" class="text-sm text-indigo-600 hover:underline">Forgot Password?</a>
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
    data() {
        return {
            username: '',
            password: ''
        };
    },
    methods: {
        ...mapActions(['login']),
        async user_login() {
            try {
                const response = await this.login({ username: this.username, password: this.password });
                if (response.success) {
                    this.$router.push('/home');
                } else {
                    alert('Login failed. Please check your credentials and try again.');
                }
            } catch (error) {
                alert('Login failed. Please check your credentials and try again.');
            }
        },
        cancel() {
            this.$router.push('/'); // Redirect to the base URL
        }
    }
};
</script>

<style scoped>
.login-page {
    background-color: #f7fafc;
}
</style>