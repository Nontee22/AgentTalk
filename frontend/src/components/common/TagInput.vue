<script setup lang="ts">
import { ref } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const inputValue = ref('')

function addTag() {
  const tag = inputValue.value.trim()
  if (tag && !props.modelValue.includes(tag)) {
    emit('update:modelValue', [...props.modelValue, tag])
  }
  inputValue.value = ''
}

function removeTag(index: number) {
  const updated = [...props.modelValue]
  updated.splice(index, 1)
  emit('update:modelValue', updated)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    addTag()
  }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-2 mb-2" v-if="modelValue.length">
      <span
        v-for="(tag, index) in modelValue"
        :key="tag"
        class="inline-flex items-center gap-1 rounded-full bg-accent-dim px-2.5 py-1 text-xs text-accent"
      >
        {{ tag }}
        <button
          class="hover:text-accent-hover transition-colors"
          @click="removeTag(index)"
        >
          <X :size="12" />
        </button>
      </span>
    </div>
    <div class="flex gap-2">
      <input
        v-model="inputValue"
        type="text"
        placeholder="输入标签后按回车添加"
        class="flex-1 rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
        @keydown="handleKeydown"
      />
      <button
        type="button"
        class="px-3 py-2 rounded-lg bg-white/[0.06] text-text-secondary text-sm hover:bg-white/[0.1] transition-colors"
        @click="addTag"
      >
        添加
      </button>
    </div>
  </div>
</template>
