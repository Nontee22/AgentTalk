<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { getCharacter, createCharacter, updateCharacter } from '@/api/characters'
import { uploadImage } from '@/api/upload'
import ImageUpload from '@/components/common/ImageUpload.vue'
import TagInput from '@/components/common/TagInput.vue'
import type { CharacterCreate, CharacterUpdate } from '@/types/world'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'character-edit')
const characterId = computed(() => route.params.id as string | undefined)
const worldId = computed(() => route.params.worldId as string | undefined)
const saving = ref(false)
const resolvedWorldId = ref('')

const form = ref<CharacterCreate>({
  name: '',
  avatar: undefined,
  identity: '',
  personality: '',
  background: '',
  relationships: '',
  language_style: '',
  knowledge: '',
  greeting: '',
  tags: [],
})

onMounted(async () => {
  if (isEdit.value && characterId.value) {
    const char = await getCharacter(characterId.value)
    resolvedWorldId.value = char.world_id
    form.value = {
      name: char.name,
      avatar: char.avatar || undefined,
      identity: char.identity || '',
      personality: char.personality || '',
      background: char.background || '',
      relationships: char.relationships || '',
      language_style: char.language_style || '',
      knowledge: char.knowledge || '',
      greeting: char.greeting || '',
      tags: char.tags || [],
    }
  } else if (worldId.value) {
    resolvedWorldId.value = worldId.value
  }
})

async function handleUpload(file: File) {
  const result = await uploadImage(file, 'avatars')
  form.value.avatar = result.path
}

async function handleSubmit() {
  if (!form.value.name.trim()) return
  saving.value = true

  try {
    if (isEdit.value && characterId.value) {
      await updateCharacter(characterId.value, form.value as CharacterUpdate)
      router.push({ name: 'world-detail', params: { id: resolvedWorldId.value } })
    } else {
      await createCharacter(resolvedWorldId.value, form.value)
      router.push({ name: 'world-detail', params: { id: resolvedWorldId.value } })
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
        {{ isEdit ? '编辑角色' : '创建角色' }}
      </h1>
      <div class="w-16" />
    </div>

    <form class="space-y-6" @submit.prevent="handleSubmit">
      <div>
        <label class="block text-sm text-text-secondary mb-2">角色名称 *</label>
        <input
          v-model="form.name"
          type="text"
          required
          maxlength="100"
          placeholder="角色的名字"
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">头像</label>
        <ImageUpload
          :model-value="form.avatar || null"
          @update:model-value="form.avatar = $event || undefined"
          @upload="handleUpload"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">身份描述</label>
        <input
          v-model="form.identity"
          type="text"
          placeholder="职业、地位、种族等"
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">性格特征</label>
        <textarea
          v-model="form.personality"
          rows="4"
          placeholder="详细描述角色的性格特点..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">个人经历</label>
        <textarea
          v-model="form.background"
          rows="4"
          placeholder="角色的背景故事..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">人际关系</label>
        <textarea
          v-model="form.relationships"
          rows="3"
          placeholder="与其他角色的关系..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">说话风格</label>
        <textarea
          v-model="form.language_style"
          rows="3"
          placeholder="口癖、句式、用词习惯..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">知识范围</label>
        <textarea
          v-model="form.knowledge"
          rows="3"
          placeholder="角色所知道的信息（不超出世界观范围）..."
          class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none"
        />
      </div>

      <div>
        <label class="block text-sm text-text-secondary mb-2">开场白</label>
        <textarea
          v-model="form.greeting"
          rows="3"
          placeholder="首次对话时角色的第一句话..."
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
          {{ saving ? '保存中...' : isEdit ? '保存修改' : '创建角色' }}
        </button>
      </div>
    </form>
  </main>
</template>
