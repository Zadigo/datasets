<template>
  <u-card class="mt-2">
    <div class="flex justify-start gap-5 items-center">
      <div :class="{ 'bg-green-100': match.win_loss === 'W', 'bg-red-100': match.win_loss === 'L' }" class="rounded-md px-2 py-5 w-14 text-center">
        {{ match.win_loss }}
      </div>

      <div>
        <h2 class="font-semibold text-xl">
          {{ match.name }}
        </h2>
        <div>
          {{ match.country }}
        </div>
      </div>
    </div>
  </u-card>
</template>

<script setup lang="ts">
import type { Match } from '~/types'
defineProps<{
  match: Match
}>()
</script>
