import pydantic
from typing import Optional, Any
from pydantic import Field


class PlayerModelMatchModel(pydantic.BaseModel):
    id: int = Field(..., ge=0)
    name: str = Field(...)
    seed: Optional[int] = Field(None, ge=1)
    country: str = Field(...)
    flag: str = Field(...)
    round: str = Field(...)
    win_loss: str = Field(...)
    score: str = Field(...)
    rank: int = Field(..., ge=0)
    url_profile: str = Field(...)
    retired: bool = Field(...)
    walkover: bool = Field(...)
    bye: bool = Field(...)
    first_set_tiebreak: bool = Field(...)
    second_set_tiebreak: bool = Field(...)
    third_set_tiebreak: bool = Field(...)
    splitted_score: list[list[int | str | None]
                         ] = Field(default_factory=lambda: [])
    number_of_sets: int = Field(...)
    first_set_won: bool = Field(...)
    code_alpha_2: Optional[str] = Field(None)
    code_alpha_3: Optional[str] = Field(None)
    country_code_m49: Optional[int] = Field(None)
    region_code: Optional[str] = Field(None)
    region: Optional[str] = Field(None)
    subregion: Optional[str] = Field(None)
    fifa: Optional[str] = Field(None)


class PlayerModel(pydantic.BaseModel):
    id: int = Field(...)
    title: str = Field(...)
    logo: str = Field(...)
    url: Optional[str] = Field(None)
    level: str = Field(...)
    surface: str = Field(...)
    level_logo: str = Field(...)
    matches: list[PlayerModelMatchModel] = Field(default_factory=lambda: [])
    start_date: str = Field(...)
    end_date: str = Field(...)
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    city: Optional[str] = Field(None)
    country: str = Field(...)
    state: Optional[str] = Field(None)
    code_alpha_2: Optional[str] = Field(None)
    code_alpha_3: Optional[str] = Field(None)
    country_code_m49: Optional[int] = Field(None)
    region_code: Optional[str] = Field(None)
    region: Optional[str] = Field(None)
    subregion: Optional[str] = Field(None)
    fifa: Optional[str] = Field(None)
    rank: int = Field(..., ge=0)
    points_gain: int = Field(..., ge=0)
    prize_money: int = Field(..., ge=0)
    draw: str = Field(...)


class ResponseModel(pydantic.BaseModel):
    results: list[PlayerModel | dict[str, Any]]


class FlatPlayerModel(PlayerModel, PlayerModelMatchModel):
    """A model that combines the fields of PlayerModel and 
    PlayerModelMatchModel for flattened data."""

    tour_code_alpha_2: Optional[str] = Field(None)
    tour_code_alpha_3: Optional[str] = Field(None)
    tour_country_code_m49: Optional[int] = Field(None)
    tour_region_code: Optional[str] = Field(None)
    tour_region: Optional[str] = Field(None)
    tour_subregion: Optional[str] = Field(None)
    tour_fifa: Optional[str] = Field(None)


class StatisticsModel(pydantic.BaseModel):
    years: list[int] = Field(default_factory=lambda: [])
    min_year: Optional[int] = Field(None)
    max_year: Optional[int] = Field(None)
    surfaces: list[str] = Field(default_factory=lambda: [])
    levels: list[str] = Field(default_factory=lambda: [])
    cities: list[str] = Field(default_factory=lambda: [])
    countries: list[str] = Field(default_factory=lambda: [])
    code_alpha_2: list[str] = Field(default_factory=lambda: [])
    code_alpha_3: list[str] = Field(default_factory=lambda: [])
    country_code_m49: list[int] = Field(default_factory=lambda: [])
    number_of_matches: int = Field(..., ge=0)
    number_of_tournaments: int = Field(..., ge=0)
    wins: int = Field(..., ge=0)
    losses: int = Field(..., ge=0)
    wins_by_surface: dict[str, int] = Field(default_factory=lambda: {})
    losses_by_surface: dict[str, int] = Field(default_factory=lambda: {})
    min_date: Optional[str] = Field(None)
    max_date: Optional[str] = Field(None)
    win_percentage: float = Field(..., ge=0.0, le=100.0)
