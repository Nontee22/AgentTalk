<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
</script>

<template>
  <div class="min-h-screen bg-bg-base">
    <AppHeader />
    <RouterView />
    <ToastContainer />
  </div>
</template>
