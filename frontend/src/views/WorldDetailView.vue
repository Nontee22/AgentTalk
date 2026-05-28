<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Pencil, Plus } from 'lucide-vue-next'
import { useWorldStore } from '@/stores/worldStore'
import { getCharacter } from '@/api/characters'
import WorldHero from '@/components/world/WorldHero.vue'
import WorldLore from '@/components/world/WorldLore.vue'
import CharacterCard from '@/components/character/CharacterCard.vue'
import CharacterDrawer from '@/components/character/CharacterDrawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { Character } from '@/types/world'

const route = useRoute()
const router = useRouter()
const store = useWorldStore()

const drawerOpen = ref(false)
const selectedCharacter = ref<Character | null>(null)

onMounted(() => {
  store.fetchWorldDetail(route.params.id as string)
})

async function openDrawer(characterId: string) {
  selectedCharacter.value = await getCharacter(characterId)
  drawerOpen.value = true
}
</script>

<template>
  <div v-if="store.currentWorld">
    <WorldHero :world="store.currentWorld" />

    <main class="max-w-5xl mx-auto px-6 py-8">
      <div class="flex items-center justify-between mb-6">
        <button
          class="flex items-center gap-1.5 text-text-secondary text-sm hover:text-text-primary transition-colors"
          @click="router.push({ name: 'worlds' })"
        >
          <ArrowLeft :size="16" />
          返回
        </button>

        <div class="flex gap-2">
          <router-link
            :to="{ name: 'character-create', params: { worldId: store.currentWorld.id } }"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] text-text-secondary text-sm hover:bg-white/[0.1] transition-colors"
          >
            <Plus :size="14" />
            添加角色
          </router-link>
          <router-link
            :to="{ name: 'world-edit', params: { id: store.currentWorld.id } }"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] text-text-secondary text-sm hover:bg-white/[0.1] transition-colors"
          >
            <Pencil :size="14" />
            编辑
          </router-link>
        </div>
      </div>

      <div v-if="store.currentWorld.description" class="mb-8">
        <p class="text-text-secondary text-sm leading-relaxed">
          {{ store.currentWorld.description }}
        </p>
      </div>

      <WorldLore :world="store.currentWorld" class="mb-10" />

      <div>
        <h2 class="font-serif text-lg text-text-primary mb-6">世界中的角色</h2>

        <div
          v-if="store.characters.length"
          class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5"
        >
          <CharacterCard
            v-for="char in store.characters"
            :key="char.id"
            :character="char"
            @click="openDrawer(char.id)"
          />
        </div>

        <EmptyState
          v-else
          message="这个世界还没有角色，添加一个吧"
          action-label="添加角色"
          @action="router.push({ name: 'character-create', params: { worldId: store.currentWorld!.id } })"
        />
      </div>
    </main>

    <CharacterDrawer
      v-if="selectedCharacter"
      :character="selectedCharacter"
      :open="drawerOpen"
      @close="drawerOpen = false"
    />
  </div>

  <div v-else-if="store.loading" class="flex items-center justify-center min-h-[60vh]">
    <div class="text-text-muted text-sm">加载中...</div>
  </div>
</template>
