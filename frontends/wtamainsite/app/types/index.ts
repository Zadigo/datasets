export interface Match {
	id: number
	name: string
	seed?: number
	country: string
	flag: string
	round: string
	win_loss: 'W' | 'L' | (string & {})
	score: string
	rank: number
	url_profile: string
	retired: boolean
	walkover: boolean
	bye: boolean
	first_set_tiebreak: boolean
	second_set_tiebreak: boolean
	third_set_tiebreak: boolean
	splitted_score: (number | null)[][]
	number_of_sets: number
	first_set_won: boolean
	code_alpha_2: string
	code_alpha_3: string
	country_code_m49: string
	region_code: string
	region: string
	subregion: string
	fifa: string
}

export interface Tournament {
	id: number
	title: string
	logo: string
	url: string
	level: string
	surface: string
	level_logo: string
	matches: Match[]
	start_date: string
	end_date: string
	year: number
	month: number
	city: string
	country: string
	state?: number
	code_alpha_2: string
	code_alpha_3: string
	country_code_m49: string
	region_code: string
	region: string
	subregion: string
	fifa: string
	rank: number
	points_gain: number
	prize_money: number
	draw: string
}

export type ApiResponse = {
  results: Tournament[]
}
