<script setup lang="ts">
import type { WorldBook } from '@/types/world'
import FoldableSection from '@/components/common/FoldableSection.vue'

defineProps<{
  world: WorldBook
}>()
</script>

<template>
  <div class="space-y-0">
    <FoldableSection v-if="world.setting" title="世界观设定">
      {{ world.setting }}
    </FoldableSection>

    <FoldableSection v-if="world.rules" title="世界规则">
      {{ world.rules }}
    </FoldableSection>

    <FoldableSection v-if="world.lore" title="历史与传说">
      {{ world.lore }}
    </FoldableSection>

    <FoldableSection v-if="world.factions?.length" title="势力与阵营">
      <ul class="list-disc list-inside space-y-1">
        <li v-for="faction in world.factions" :key="faction">{{ faction }}</li>
      </ul>
    </FoldableSection>
  </div>
</template>
