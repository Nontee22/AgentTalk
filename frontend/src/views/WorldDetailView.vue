<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Pencil, Plus } from 'lucide-vue-next'
import { useWorldStore } from '@/stores/worldStore'
import { useAuthStore } from '@/stores/authStore'
import { useConversationStore } from '@/stores/conversationStore'
import { useToast } from '@/composables/useToast'
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
const auth = useAuthStore()
const conversationStore = useConversationStore()
const { showToast } = useToast()

const drawerOpen = ref(false)
const selectedCharacter = ref<Character | null>(null)
const error = ref(false)

const canEdit = computed(() => {
  const world = store.currentWorld
  if (!world) return false
  if (auth.isAdmin) return true
  return world.created_by === auth.user?.id
})

onMounted(async () => {
  try {
    await store.fetchWorldDetail(route.params.id as string)
  } catch {
    error.value = true
  }
})

async function openDrawer(characterId: string) {
  try {
    selectedCharacter.value = await getCharacter(characterId)
    drawerOpen.value = true
  } catch {
    showToast('加载角色信息失败', 'error')
  }
}

async function handleStartChat(characterId: string) {
  if (!store.currentWorld) return
  try {
    const convId = await conversationStore.createConversation(characterId, store.currentWorld.id)
    router.push({ name: 'chat', params: { conversationId: convId } })
  } catch (err: any) {
    showToast(err.response?.data?.detail || '创建对话失败', 'error')
  }
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

        <div class="flex gap-2" v-if="canEdit">
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
            @start-chat="handleStartChat(char.id)"
          />
        </div>

        <EmptyState
          v-else-if="canEdit"
          message="这个世界还没有角色，添加一个吧"
          action-label="添加角色"
          @action="router.push({ name: 'character-create', params: { worldId: store.currentWorld!.id } })"
        />

        <EmptyState
          v-else
          message="这个世界还没有角色"
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

  <div v-else class="flex flex-col items-center justify-center min-h-[60vh] text-center">
    <p class="text-text-muted text-sm mb-4">{{ error ? '加载失败，请稍后重试' : '世界书不存在' }}</p>
    <button
      class="text-accent text-sm hover:text-accent-hover transition-colors"
      @click="router.push({ name: 'worlds' })"
    >
      返回世界书列表
    </button>
  </div>
</template>
