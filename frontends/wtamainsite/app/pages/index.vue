<template>
  <div class="px-20 mt-10">
    <u-card>
      <u-input v-model="playerName" />
      <u-button @click="search">
        Search
      </u-button>
    </u-card>

    <!-- Filters -->
    <async-tournaments-filter />

    <!-- Tournaments -->
    <lazy-tournaments-base :results="results" />
  </div>
</template>

<script setup lang="ts">
import type { ApiResponse } from '~/types'

const AsyncTournamentsFilter = defineAsyncComponent({
  loader: () => import('~/components/tournaments/Filters.vue'),
  loadingComponent: {
    template: '<div>Loading...</div>',
  },
})

const playerName = ref('')
const responseData = ref<ApiResponse>()
const results = computed(() => responseData.value?.results || [])

const { load } = useMemoize(async (player: string) => {
  try {
    return await $fetch<ApiResponse>(`/v1/players/${player}`, {
      method: 'GET',
      baseURL: 'http://127.0.0.1:8000',
    })
  } catch (error) {
    console.error('Error fetching player data:', error)
  }
})

async function search() {
  responseData.value = await load(playerName.value)
}
</script>


