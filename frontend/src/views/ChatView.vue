<template>
  <v-app theme="dark">
    <v-main>
      <div class="d-flex flex-column" style="height: 100vh">
        <!-- 헤더 -->
        <v-toolbar color="grey-darken-4" flat border="b">
          <v-toolbar-title class="text-body-1 font-weight-medium">
            NAS 검색
          </v-toolbar-title>
          <template #append>
            <v-chip 
              v-if="isLoading" 
              color="primary" 
              size="small" 
              prepend-icon="mdi-loading" 
              class="mdi-spin mr-2"
            >
              검색 중...
            </v-chip>
            <v-btn icon size="small" class="mr-2" @click="clearChat">
              <v-icon>mdi-delete</v-icon>
              <v-tooltip activator="parent" location="bottom">초기화</v-tooltip>
            </v-btn>
          </template>
        </v-toolbar>

        <!-- 메시지 영역 -->
        <div
          ref="messagesContainer"
          class="flex-grow-1 overflow-y-auto pa-4"
          style="background: #1a1a1a"
        >
          <!-- 빈 상태 -->
          <div
            v-if="messages.length === 0"
            class="d-flex flex-column align-center justify-center"
            style="height: 100%"
          >
            <v-icon size="64" color="grey-darken-1">mdi-file-search</v-icon>
            <div class="text-h6 text-medium-emphasis mt-4">NAS 파일을 검색해보세요</div>
            <div class="text-body-2 text-disabled mt-2">자연어로 원하는 파일을 찾을 수 있습니다</div>
            
            <!-- 예시 쿼리 -->
            <div class="mt-6 w-100" style="max-width: 500px">
              <div class="text-caption text-medium-emphasis mb-2">예시:</div>
              <v-chip
                v-for="example in examples"
                :key="example"
                variant="outlined"
                size="small"
                class="ma-1"
                @click="sendQuery(example)"
              >
                {{ example }}
              </v-chip>
            </div>
          </div>

          <!-- 메시지 목록 -->
          <MessageBubble
            v-for="msg in messages"
            :key="msg.id"
            :content="msg.content"
            :role="msg.role"
            :created-at="msg.timestamp"
          />

          <!-- 로딩 표시 -->
          <div v-if="isLoading" class="d-flex justify-start mb-4">
            <v-avatar size="32" color="primary" class="mr-2 flex-shrink-0">
              <v-icon size="18">mdi-robot</v-icon>
            </v-avatar>
            <v-card color="grey-darken-3" rounded="lg" class="px-4 py-3">
              <div class="d-flex gap-2">
                <v-progress-circular size="20" width="2" indeterminate color="primary" />
                <span class="text-body-2">응답을 생성하는 중입니다...</span>
              </div>
            </v-card>
          </div>
        </div>

        <!-- 입력 영역 -->
        <div class="pa-4 pt-2">
          <v-card color="grey-darken-3" rounded="xl" flat>
            <v-textarea
              v-model="inputText"
              placeholder="자연어로 질문을 입력하세요... (예: Python 파일 찾아줄래?)"
              variant="none"
              rows="1"
              auto-grow
              max-rows="6"
              hide-details
              class="px-3 pt-3 pb-0"
              :disabled="isLoading"
              @keydown.enter.exact.prevent="submit"
            />
            <div class="d-flex align-center justify-space-between pa-2 pt-1">
              <div class="text-caption text-medium-emphasis ml-2">
                <v-icon size="12" class="mr-1">mdi-circle</v-icon>
                <span v-if="isLoading" class="text-primary">처리 중...</span>
                <span v-else>Claude · 자연어 검색</span>
              </div>
              <v-btn
                icon
                size="small"
                :color="canSubmit ? 'primary' : undefined"
                :disabled="!canSubmit"
                @click="submit"
              >
                <v-icon>{{ isLoading ? 'mdi-loading mdi-spin' : 'mdi-send' }}</v-icon>
              </v-btn>
            </div>
          </v-card>
        </div>
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import axios from 'axios'
import MessageBubble from '../components/MessageBubble.vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

const messages = ref<Message[]>([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
let messageCounter = 0

const examples = [
  'Python 파일을 찾아줄래?',
  '가장 큰 파일이 뭐야?',
  'ZIP 파일 있나?',
  'README.md 파일 내용 보여줘',
  '최근에 수정된 파일들 뭐가 있어?'
]

const canSubmit = computed(() => inputText.value.trim().length > 0 && !isLoading.value)

function generateId(): string {
  return `msg-${++messageCounter}-${Date.now()}`
}

function addMessage(role: 'user' | 'assistant', content: string) {
  messages.value.push({
    id: generateId(),
    role,
    content,
    timestamp: new Date().toISOString()
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(messages, () => {
  scrollToBottom()
})

async function submit() {
  if (!canSubmit.value) return
  await sendQuery(inputText.value)
  inputText.value = ''
}

async function sendQuery(query: string) {
  if (!query.trim()) return

  // 사용자 메시지 추가
  addMessage('user', query)
  isLoading.value = true

  try {
    console.log('[Chat] 자연어 쿼리 전송:', query)
    const response = await axios.post('/api/chat', {
      message: query
    })

    console.log('[Chat] 응답:', response.data)

    if (response.data.success) {
      // Claude의 설명 추가
      addMessage('assistant', response.data.response)
      
      // 파일 목록이 있으면 추가 표시
      if (response.data.files && response.data.files.length > 0) {
        const fileList = response.data.files
          .map((f: any) => `• ${f.name} (${formatSize(f.size)})`)
          .join('\n')
        addMessage('assistant', `**검색된 파일:**\n${fileList}`)
      }
    } else {
      addMessage('assistant', `오류: ${response.data.error}`)
    }
  } catch (error: any) {
    console.error('[Chat] 에러:', error)
    addMessage('assistant', `서버 오류: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function clearChat() {
  messages.value = []
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.mdi-spin {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
