<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { getWorld } from '@/api/worlds'
import { useWorldStore } from '@/stores/worldStore'
import { uploadImage } from '@/api/upload'
import ImageUpload from '@/components/common/ImageUpload.vue'
import TagInput from '@/components/common/TagInput.vue'
import type { WorldBookCreate, WorldBookUpdate } from '@/types/world'

const route = useRoute()
const router = useRouter()
const store = useWorldStore()

const isEdit = computed(() => route.name === 'world-edit')
const worldId = computed(() => route.params.id as string | undefined)
const saving = ref(false)

const form = ref<WorldBookCreate>({
  name: '',
  description: '',
  setting: '',
  rules: '',
  lore: '',
  factions: [],
  tags: [],
  cover_image: undefined,
})

const factionsText = ref('')

onMounted(async () => {
  if (isEdit.value && worldId.value) {
    const world = await getWorld(worldId.value)
    form.value = {
      name: world.name,
      description: world.description || '',
      setting: world.setting || '',
      rules: world.rules || '',
      lore: world.lore || '',
      factions: world.factions || [],
      tags: world.tags || [],
      cover_image: world.cover_image || undefined,
    }
    factionsText.value = (world.factions || []).join('\n')
  }
})

async function handleUpload(file: File) {
  const result = await uploadImage(file, 'covers')
  form.value.cover_image = result.path
}

async function handleSubmit() {
  if (!form.value.name.trim()) return
  saving.value = true

  const data = {
    ...form.value,
    factions: factionsText.value
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean),
  }

  try {
    if (isEdit.value && worldId.value) {
      await store.editWorld(worldId.value, data as WorldBookUpdate)
      router.push({ name: 'world-detail', params: { id: worldId.value } })
    } else {
      const world = await store.addWorld(data)
      router.push({ name: 'world-detail', params: { id: world.id } })
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="max-w-3xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <button
        class="flex items-center gap-1.5 text-text-secondary text-sm hover:text-text-primary transition-colors"
        @click="router.back()"
      >
        <ArrowLeft :size="16" />
        返回
      </button>
      <h1 class="font-serif text-xl text-text-primary">
        {{ isEdit ? '编辑世界书' : '创建世界书' }}
      </h1>
      <div class="w-16" />
    </div>

    <form class="space-y-6" @submit.prevent="handleSubmit">
      <div>
        <label class="block text-sm text-text-secondary mb-2">世界名称 *</label>
        <input
          v-model="form.name"
          type="text"
          required
          maxlength="100"
          placeholder="为你的世界取一个名字"
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">封面图</label>
        <ImageUpload
          :model-value="form.cover_image || null"
          @update:model-value="form.cover_image = $event || undefined"
          @upload="handleUpload"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">简要介绍</label>
        <textarea
          v-model="form.description"
          rows="2"
          placeholder="用一两句话介绍这个世界"
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">世界观设定</label>
        <textarea
          v-model="form.setting"
          rows="6"
          placeholder="详细描述这个世界的背景、历史、社会结构..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">世界规则</label>
        <textarea
          v-model="form.rules"
          rows="4"
          placeholder="这个世界的法则、魔法体系、物理规则..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">历史与传说</label>
        <textarea
          v-model="form.lore"
          rows="4"
          placeholder="这个世界中的重要历史事件、传说故事..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">势力与阵营（每行一个）</label>
        <textarea
          v-model="factionsText"
          rows="3"
          placeholder="凤凰社&#10;食死徒&#10;魔法部"
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">标签</label>
        <TagInput v-model="form.tags!" />
      </div>

      <div class="pt-4">
        <button
          type="submit"
          :disabled="saving || !form.name.trim()"
          class="w-full py-2.5 rounded-lg bg-accent text-bg-deep font-medium text-sm hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? '保存中...' : isEdit ? '保存修改' : '创建世界' }}
        </button>
      </div>
    </form>
  </main>
</template>
