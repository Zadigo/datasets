<template>
  <u-card v-for="tournament in results" :key="tournament.id" class="mt-4">
    <h1 class="font-bold text-2xl">
      ({{ tournament.year }}) {{ tournament.title }}
    </h1>

    <u-badge>
      {{ tournament.level }}
    </u-badge>

    <div class="ps-20 mt-15">
      <tournaments-matches v-for="match in tournament.matches" :key="match.id" :match="match" />
    </div>
  </u-card>
</template>

<script setup lang="ts">
import type { Tournament } from '~/types'

defineProps<{
  results: Tournament[]
}>()
</script>
