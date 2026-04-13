<template>
  <v-card>
    <v-card-title>
      검색 결과 ({{ results.length }}개)
    </v-card-title>
    <v-card-text>
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <p class="mt-2">검색 중...</p>
      </div>

      <div v-else-if="results.length === 0" class="text-center py-8 text-grey">
        <p class="text-h6">검색 결과가 없습니다</p>
        <p class="text-sm">다른 검색어로 시도해주세요</p>
      </div>

      <v-table v-else>
        <thead>
          <tr>
            <th>파일명</th>
            <th>크기</th>
            <th>타입</th>
            <th>수정일</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(file, idx) in results" :key="idx">
            <td>
              <div class="d-flex align-center">
                <v-icon size="small" class="mr-2">{{ getFileIcon(file.type) }}</v-icon>
                <span class="text-truncate">{{ file.name }}</span>
              </div>
            </td>
            <td>{{ formatSize(file.size) }}</td>
            <td>{{ file.type }}</td>
            <td>{{ formatDate(file.modified_date) }}</td>
            <td>
              <v-btn
                size="small"
                variant="text"
                color="primary"
                @click="$emit('view', file)"
              >
                보기
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view'])

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
  return date.toLocaleDateString('ko-KR')
}

const getFileIcon = (type) => {
  const iconMap = {
    'zip': 'mdi-archive',
    'folder': 'mdi-folder',
    'python': 'mdi-language-python',
    'markdown': 'mdi-markdown',
    'text': 'mdi-file-document',
    'json': 'mdi-code-json',
    'xml': 'mdi-code-xml',
    'default': 'mdi-file'
  }
  return iconMap[type] || iconMap['default']
}
</script>
