<template>
  <div
    class="d-flex mb-4"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <!-- AI 아바타 -->
    <v-avatar v-if="!isUser" size="32" color="primary" class="mr-2 mt-1 flex-shrink-0">
      <v-icon size="18">mdi-robot</v-icon>
    </v-avatar>

    <div :style="{ maxWidth: '80%' }">
      <v-card
        :color="isUser ? 'primary' : 'grey-darken-3'"
        rounded="lg"
        flat
        class="px-4 py-3"
      >
        <!-- 마크다운 스타일 텍스트 (굵게, 기울임) -->
        <div
          class="text-body-2"
          style="white-space: pre-wrap; word-break: break-word; line-height: 1.6"
          v-html="processMarkdown(content)"
        />
      </v-card>
      <div class="text-caption text-medium-emphasis mt-1" :class="isUser ? 'text-right' : ''">
        {{ formatTime(createdAt) }}
      </div>
    </div>

    <!-- 유저 아바타 -->
    <v-avatar v-if="isUser" size="32" color="grey-darken-2" class="ml-2 mt-1 flex-shrink-0">
      <v-icon size="18">mdi-account</v-icon>
    </v-avatar>
  </div>
</template>

<script setup lang="ts">
interface Props {
  content: string
  role: 'user' | 'assistant'
  createdAt: string
}

const props = defineProps<Props>()
const isUser = props.role === 'user'

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

function processMarkdown(text: string): string {
  // **굵게** → <strong>굵게</strong>
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  // *기울임* → <em>기울임</em>
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
  // 줄바꿈 유지
  text = text.replace(/\n/g, '<br>')
  return text
}
</script>

<style scoped>
div {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>
