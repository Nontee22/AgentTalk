<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'

const route = useRoute()
const showHeader = computed(() => !route.meta.guest)
</script>

<template>
  <div class="min-h-screen bg-bg-base">
    <AppHeader v-if="showHeader" />
    <RouterView />
    <ToastContainer />
  </div>
</template>
