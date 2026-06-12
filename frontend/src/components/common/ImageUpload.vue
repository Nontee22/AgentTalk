<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, X } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  modelValue: string | null
  category?: 'covers' | 'avatars'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'upload': [file: File]
}>()

const { showToast } = useToast()
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement>()

const previewUrl = computed(() => {
  if (!props.modelValue) return null
  return `/api/static/${props.modelValue}`
})

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) emitUpload(file)
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emitUpload(file)
  input.value = ''
}

function emitUpload(file: File) {
  if (file.size > 5 * 1024 * 1024) {
    showToast('文件大小不能超过 5MB', 'error')
    return
  }
  emit('upload', file)
}

function clear() {
  emit('update:modelValue', null)
}
</script>

<template>
  <div
    class="relative rounded-card border-2 border-dashed transition-colors cursor-pointer overflow-hidden"
    :class="
      isDragging
        ? 'border-accent bg-accent-dim'
        : 'border-white/[0.12] hover:border-white/[0.24]'
    "
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="fileInput?.click()"
  >
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/gif,image/webp"
      class="hidden"
      @change="handleFileSelect"
    />

    <div v-if="previewUrl" class="relative">
      <img :src="previewUrl" alt="Preview" class="w-full h-48 object-cover" />
      <button
        class="absolute top-2 right-2 p-1 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors"
        aria-label="移除图片"
        @click.stop="clear"
      >
        <X :size="14" />
      </button>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-10 text-text-muted">
      <Upload :size="24" class="mb-2" />
      <p class="text-sm">拖拽或点击上传图片</p>
      <p class="text-xs mt-1">支持 JPG, PNG, GIF, WebP (最大 5MB)</p>
    </div>
  </div>
</template>
