<script setup>
import { ref } from 'vue'

defineProps({
  msg: String,
})

const count = ref(0)
</script>

<template>
  <v-container>
    <v-row>
      <v-col>
        <h1>{{ message }}</h1>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      message: 'Welcome to the Inventory Management App'
    };
  }
};
</script>

<style scoped>
h1 {
  font-weight: normal;
}
.read-the-docs {
  color: #888;
}
</style>
