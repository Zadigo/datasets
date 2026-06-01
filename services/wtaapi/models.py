import pydantic


class ResponseModel(pydantic.BaseModel):
    results: list[PlayerModel]


class PlayerModelMatchModel(pydantic.BaseModel):
    id: int
    name: str
    seed: int | None
    country: str
    flag: str
    round: str
    win_loss: str
    score: str
    rank: int
    url_profile: str
    retired: bool
    walkover: bool
    bye: bool
    first_set_tiebreak: bool
    second_set_tiebreak: bool
    third_set_tiebreak: bool
    splitted_score: list[list[int | str | None]]
    number_of_sets: int
    first_set_won: bool
    code_alpha_2: str
    code_alpha_3: str
    country_code_m49: int
    region_code: str
    region: str
    subregion: str
    fifa: str


class PlayerModel(pydantic.BaseModel):
    id: int
    title: str
    logo: str
    url: str
    level: str
    surface: str
    level_logo: str
    matches: list[PlayerModelMatchModel]
    start_date: str
    end_date: str
    year: int
    month: int
    city: str | None
    country: str
    state: str | None
    code_alpha_2: str | None
    code_alpha_3: str | None
    country_code_m49: int | None
    region_code: str | None
    region: str | None
    subregion: str | None
    fifa: str | None
    rank: int
    points_gain: int
    prize_money: int
    draw: str
