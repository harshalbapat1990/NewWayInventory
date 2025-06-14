<template>
    <div class="relative">
        <input
            type="text"
            v-model="searchQuery"
            :placeholder="placeholder"
            class="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            @focus="dropdownOpen = true"
            @input="dropdownOpen = true"
            @blur="handleBlur"
        />
        <ul
            v-if="dropdownOpen && filteredOptions.length"
            class="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto sm:text-sm"
        >
            <li
                v-for="option in filteredOptions"
                :key="option"
                @mousedown.prevent="selectOption(option)"
                class="cursor-pointer px-3 py-2 hover:bg-indigo-500 hover:text-white"
            >
                {{ option }}
            </li>
        </ul>
    </div>
</template>

<script>
export default {
    name: "ComboBox",
    props: {
        options: {
            type: Array,
            required: true,
        },
        modelValue: {
            type: [String, Number],
            required: true,
        },
        placeholder: {
            type: String,
            default: "Select or search...", // Default placeholder value
        },
    },
    data() {
        return {
            searchQuery: "",
            dropdownOpen: false,
        };
    },
    computed: {
        filteredOptions() {
            if (!this.searchQuery) {
                return this.options;
            }
            return this.options.filter((option) =>
                option.toString().toLowerCase().includes(this.searchQuery.toLowerCase())
            );
        },
    },
    watch: {
        modelValue(newValue) {
            this.searchQuery = newValue;
        },
    },
    methods: {
        selectOption(option) {
            this.searchQuery = option;
            this.$emit("update:modelValue", option);
            this.dropdownOpen = false;
        },
        handleBlur() {
            // Delay closing the dropdown to allow click events on options to register
            setTimeout(() => {
                this.dropdownOpen = false;
            }, 200);
        },
    },
    mounted() {
        this.searchQuery = this.modelValue;
    },
};
</script>

<style scoped>
/* Add any custom styles here if needed */
</style>