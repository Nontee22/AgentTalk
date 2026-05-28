<script setup lang="ts">
defineProps<{
  label: string
  variant?: 'default' | 'accent'
}>()
</script>

<template>
  <span
    class="inline-block rounded-full px-2.5 py-0.5 text-xs"
    :class="
      variant === 'accent'
        ? 'bg-accent-dim text-accent'
        : 'bg-white/[0.06] text-text-secondary'
    "
  >
    {{ label }}
  </span>
</template>
