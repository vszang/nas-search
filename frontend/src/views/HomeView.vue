<template>
  <div>
    <RouterLink to="/" class="text-decoration-none">
      <v-app theme="dark">
        <v-main>
          <div class="d-flex align-center justify-center" style="height: 100vh">
            <v-card max-width="500" flat rounded="lg" color="grey-darken-4" class="pa-8">
              <v-card-title class="text-h5 text-center mb-6">
                <v-icon size="40" color="primary" class="mb-2">mdi-file-search</v-icon>
                <div>NAS 검색 시스템</div>
              </v-card-title>
              <v-card-text class="text-center text-body-2 text-medium-emphasis mb-4">
                Claude AI를 이용해 자연어로 NAS 파일을 검색할 수 있습니다.
              </v-card-text>
              <v-btn color="primary" block size="large">
                검색 시작하기
              </v-btn>
            </v-card>
          </div>
        </v-main>
      </v-app>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
