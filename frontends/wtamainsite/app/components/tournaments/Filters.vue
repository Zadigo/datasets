<template>
  <u-card>
    {{ data }}
  </u-card>
</template> 

<script setup lang="ts">

type Filter = {
  min_year: number | null
  max_year: number | null
  min_date: string | null
  max_date: string | null
  min_month: number | null
  max_month: number | null
  levels: string[]
  surfaces: string[]
  min_opponent_rank: number | null
  max_opponent_rank: number | null
  first_set_tiebreak: boolean | null
  second_set_tiebreak: boolean | null
  third_set_tiebreak: boolean | null
  walkover: boolean | null
  number_of_sets: number | null
  first_set_won: boolean | null
  region: string | null
  subregion: string | null
  fifa: number | null
  code_alpha_2: string | null
  code_alpha_3: string | null
  only_wins: boolean | null
  only_losses: boolean | null
}

const filters = ref<Filter>({
  min_year : null,
  max_year : null,
  min_date : null,
  max_date : null,
  min_month : null,
  max_month : null,
  levels: [],
  surfaces: [],
  min_opponent_rank: null,
  max_opponent_rank: null,
  first_set_tiebreak: null,
  second_set_tiebreak: null,
  third_set_tiebreak: null,
  walkover: null,
  number_of_sets: null,
  first_set_won: null,
  region: null,
  subregion: null,
  fifa: null,
  code_alpha_2: null,
  code_alpha_3: null,
  only_wins: null,
  only_losses: null,
})

const data = computedAsync(async () => {
  return $fetch('/v1/players/azarenka/statistics', {
    method: 'GET',
    baseURL: 'http://127.0.0.1:8000',
  })
})
</script>
