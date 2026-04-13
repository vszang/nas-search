<template>
  <v-card class="mb-4">
    <v-card-title>파일 검색</v-card-title>
    <v-card-text>
      <v-form @submit.prevent="handleSearch">
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="query"
              label="검색어 입력"
              placeholder="파일명, 타입 등..."
              prepend-icon="mdi-magnify"
              @keyup.enter="handleSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="fileType"
              label="파일 타입"
              :items="fileTypes"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="2" class="d-flex align-center">
            <v-btn
              @click="handleSearch"
              color="primary"
              block
              :loading="loading"
            >
              검색
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['search'])

const query = ref('')
const fileType = ref('')
const loading = ref(false)

const fileTypes = [
  { title: 'ZIP', value: 'zip' },
  { title: 'Python', value: 'python' },
  { title: 'Markdown', value: 'markdown' },
  { title: 'Text', value: 'text' },
  { title: 'Archive', value: 'archive' }
]

const handleSearch = async () => {
  if (!query.value) {
    alert('검색어를 입력해주세요')
    return
  }

  loading.value = true
  try {
    console.log('[SearchForm] 검색 시작:', { query: query.value, fileType: fileType.value })
    const response = await axios.post('/api/search', {
      query: query.value,
      file_type: fileType.value || null,
      max_results: 20
    })

    console.log('[SearchForm] 응답:', response.data)
    if (response.data.success) {
      console.log('[SearchForm] 검색 성공. 결과:', response.data.results)
      emit('search', response.data.results)
    } else {
      console.error('[SearchForm] 검색 실패:', response.data.error)
      alert('검색 실패: ' + response.data.error)
    }
  } catch (error) {
    console.error('[SearchForm] 에러:', error)
    alert('서버 오류: ' + error.message)
  } finally {
    loading.value = false
  }
}
</script>
