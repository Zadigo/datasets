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
