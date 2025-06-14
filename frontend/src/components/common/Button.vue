<template>
  <button
    :class="[baseClass, variantClass, sizeClass]"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script>
export default {
  name: 'Button',
  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: (value) => ['primary', 'secondary', 'danger'].includes(value),
    },
    size: {
      type: String,
      default: 'md',
      validator: (value) => ['sm', 'md', 'lg'].includes(value),
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    baseClass() {
      return 'inline-flex items-center px-4 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2';
    },
    variantClass() {
      switch (this.variant) {
        case 'primary':
          return 'text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500';
        case 'secondary':
          return 'text-gray-700 bg-white border-gray-300 hover:bg-gray-50 focus:ring-indigo-500';
        case 'danger':
          return 'text-white bg-red-600 hover:bg-red-700 focus:ring-red-500';
      }
    },
    sizeClass() {
      switch (this.size) {
        case 'sm':
          return 'text-sm';
        case 'md':
          return 'text-base';
        case 'lg':
          return 'text-lg';
      }
    },
  },
};
</script>

<style scoped>
/* Add any additional styles if needed */
</style>