<template>
  <div id="app">
    <div style="position: sticky; top: 0; z-index: 1000;">
      <TopBar />
    </div>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script>
import TopBar from './components/TopBar.vue';

export default {
  name: 'App',
  components: {
    TopBar
  }
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  /* margin-top: 60px; */
}
main {
  padding: 20px;
}
</style>
