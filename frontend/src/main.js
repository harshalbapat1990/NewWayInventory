// filepath: frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import router from './router' // Updated import statement
import './assets/main.css'

const app = createApp(App);

// The beforeunload listener is removed to prevent logout on page refresh

app.use(store).use(router).mount('#app')
