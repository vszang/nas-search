<template>
  <v-card>
    <v-card-title>디렉토리 탐색</v-card-title>
    <v-card-text>
      <!-- Breadcrumb Navigation -->
      <v-breadcrumbs :items="breadcrumbs" class="mb-4">
        <template #divider>
          <v-icon icon="mdi-chevron-right"></v-icon>
        </template>
        <template #item="{ item }">
          <span
            @click="navigateTo(item)"
            :class="{ 'font-weight-bold': item.current }"
            class="cursor-pointer text-blue"
          >
            {{ item.title }}
          </span>
        </template>
      </v-breadcrumbs>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </div>

      <!-- Directory Contents -->
      <div v-else>
        <!-- Folder List -->
        <v-list v-if="folders.length > 0" class="mb-2">
          <v-list-item
            v-for="folder in folders"
            :key="folder.path"
            @click="openFolder(folder)"
            class="cursor-pointer"
          >
            <template #prepend>
              <v-icon icon="mdi-folder" color="amber"></v-icon>
            </template>
            <v-list-item-title>{{ folder.name }}</v-list-item-title>
            <template #append>
              <v-chip size="small" variant="tonal">
                {{ folder.item_count || 0 }}개
              </v-chip>
            </template>
          </v-list-item>
        </v-list>

        <!-- File List -->
        <v-list v-if="files.length > 0">
          <v-list-item
            v-for="file in files"
            :key="file.path"
            @click="$emit('selectFile', file)"
            class="cursor-pointer"
          >
            <template #prepend>
              <v-icon :icon="getFileIcon(file.type)"></v-icon>
            </template>
            <v-list-item-title>{{ file.name }}</v-list-item-title>
            <template #append>
              {{ formatSize(file.size) }}
            </template>
          </v-list-item>
        </v-list>

        <!-- Empty State -->
        <div v-if="folders.length === 0 && files.length === 0" class="text-center py-8">
          <v-icon class="mb-2" size="large" color="grey">mdi-folder-open</v-icon>
          <p class="text-grey">폴더가 비어있습니다</p>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const emit = defineEmits(['selectFile'])

const currentPath = ref('/nas/media')
const contents = ref([])
const loading = ref(false)

const folders = computed(() =>
  contents.value
    .filter(item => item.type === 'folder')
    .sort((a, b) => a.name.localeCompare(b.name))
)

const files = computed(() =>
  contents.value
    .filter(item => item.type !== 'folder')
    .sort((a, b) => a.name.localeCompare(b.name))
)

const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(p => p)
  const items = [
    { title: 'Home', path: '/', current: parts.length === 0 }
  ]
  let path = ''
  for (const part of parts) {
    path += '/' + part
    items.push({
      title: part,
      path: path,
      current: path === currentPath.value
    })
  }
  return items
})

const loadDirectory = async (path) => {
  loading.value = true
  try {
    const response = await axios.post('/api/directory', {
      path: path,
      recursive: false
    })

    if (response.data.success) {
      contents.value = response.data.contents
      currentPath.value = path
    } else {
      alert('디렉토리 로드 실패: ' + response.data.error)
    }
  } catch (error) {
    alert('서버 오류: ' + error.message)
  } finally {
    loading.value = false
  }
}

const openFolder = (folder) => {
  loadDirectory(folder.path)
}

const navigateTo = (item) => {
  loadDirectory(item.path)
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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

// Initial load
loadDirectory(currentPath.value)
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.text-blue {
  color: #1976d2;
}

.text-blue:hover {
  text-decoration: underline;
}
</style>
