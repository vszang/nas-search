<template>
  <v-dialog v-model="isOpen" max-width="800px">
    <v-card v-if="fileInfo">
      <!-- Dialog Header -->
      <v-card-title class="d-flex align-center">
        <v-icon :icon="getFileIcon(fileInfo.type)" class="mr-2"></v-icon>
        {{ fileInfo.name }}
      </v-card-title>

      <!-- Dialog Content -->
      <v-card-text>
        <!-- File Metadata -->
        <v-row class="mb-4">
          <v-col cols="6">
            <div class="mb-2">
              <strong>경로</strong>
              <p class="text-grey text-sm">{{ fileInfo.path }}</p>
            </div>
          </v-col>
          <v-col cols="6">
            <div class="mb-2">
              <strong>크기</strong>
              <p class="text-grey text-sm">{{ formatSize(fileInfo.size) }}</p>
            </div>
          </v-col>
        </v-row>

        <v-row class="mb-4">
          <v-col cols="6">
            <div class="mb-2">
              <strong>타입</strong>
              <p class="text-grey text-sm">{{ fileInfo.type }}</p>
            </div>
          </v-col>
          <v-col cols="6">
            <div class="mb-2">
              <strong>수정일</strong>
              <p class="text-grey text-sm">{{ formatDate(fileInfo.modified_date) }}</p>
            </div>
          </v-col>
        </v-row>

        <!-- File Preview -->
        <v-divider class="mb-4"></v-divider>
        <div>
          <v-card-subtitle>미리보기</v-card-subtitle>
          
          <v-progress-linear
            v-if="loadingPreview"
            indeterminate
            class="mb-2"
          ></v-progress-linear>

          <template v-else>
            <!-- Text Preview -->
            <div v-if="isTextFile" class="bg-grey-lighten-3 pa-3 rounded">
              <pre class="text-sm" style="max-height: 300px; overflow-y: auto">{{ preview }}</pre>
            </div>

            <!-- Binary File -->
            <div v-else class="text-center py-8 text-grey">
              <v-icon size="large" class="mb-2">mdi-file-alert</v-icon>
              <p>이진 파일입니다</p>
              <p class="text-sm">미리보기를 사용할 수 없습니다</p>
            </div>
          </template>
        </div>
      </v-card-text>

      <!-- Dialog Actions -->
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="grey" variant="text" @click="isOpen = false">
          닫기
        </v-btn>
        <v-btn color="primary" variant="tonal" @click="copyPath(fileInfo.path)">
          경로 복사
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean,
  fileInfo: Object
})

const emit = defineEmits(['update:modelValue'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const preview = ref('')
const loadingPreview = ref(false)

const isTextFile = computed(() => {
  if (!props.fileInfo) return false
  const textTypes = ['text', 'python', 'markdown', 'json', 'xml', 'javascript', 'html', 'css']
  return textTypes.includes(props.fileInfo.type) || 
         props.fileInfo.name?.endsWith('.txt') ||
         props.fileInfo.name?.endsWith('.py') ||
         props.fileInfo.name?.endsWith('.md')
})

// Watch for file changes and load preview
watch(() => props.fileInfo, async (newFile) => {
  if (newFile && isTextFile.value) {
    await loadPreview(newFile)
  }
})

const loadPreview = async (file) => {
  loadingPreview.value = true
  try {
    const response = await axios.post('/api/preview', {
      file_path: file.path,
      max_bytes: 5000
    })

    if (response.data.success) {
      preview.value = response.data.content
    } else {
      preview.value = '[미리보기 불가]'
    }
  } catch (error) {
    preview.value = '[오류 발생]'
  } finally {
    loadingPreview.value = false
  }
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR')
}

const getFileIcon = (type) => {
  const iconMap = {
    'zip': 'mdi-archive',
    'folder': 'mdi-folder',
    'python': 'mdi-language-python',
    'markdown': 'mdi-markdown',
    'text': 'mdi-file-document',
    'json': 'mdi-code-json',
    'default': 'mdi-file'
  }
  return iconMap[type] || iconMap['default']
}

const copyPath = (path) => {
  navigator.clipboard.writeText(path)
  alert('경로가 복사되었습니다: ' + path)
}
</script>

<style scoped>
pre {
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.text-sm {
  font-size: 0.875rem;
}

.bg-grey-lighten-3 {
  background-color: #f5f5f5;
}
</style>
