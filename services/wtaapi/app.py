from typing import Optional

import redis
import datetime
import pandas
from typing import Any
import json
from fastapi import FastAPI
import dotenv
import pathlib
from models import ResponseModel, StatisticsModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

dotenv.load_dotenv('.env')

DB_KEY = 'wta-players'

DATA_DIR = pathlib.Path(dotenv.get_key('.env', 'DATA_DIR'))


def get_redis_client() -> redis.Redis:
    client = redis.Redis(host="localhost", port=6379, db=0)
    try:
        client.ping()
    except redis.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Redis server. Please ensure it is running.")
    return client


async def load_files():
    db = get_redis_client()
    files = DATA_DIR.glob("*.json")
    for file in files:
        db.hset(
            f'{DB_KEY}:{file.stem}',
            mapping={
                'path': str(file),
                'name': file.stem,
                'player_name': file.stem.replace('_', ' ').replace('corrected', '').strip(),
                'content': b''
            }
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis client and load data into Redis
    await load_files()
    yield

origins = [
    'http://localhost:3000',
]

app = FastAPI(
    title="WTA data explorer",
    summary="A simple API to explore WTA data",
    description="A simple API to explore WTA data",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_storage_key(player_name: str) -> str:
    return f'{DB_KEY}:{player_name}_corrected'


@app.get("/v1/players", response_model=ResponseModel)
async def root() -> ResponseModel:
    return ResponseModel(results=[{"message": "Welcome to the WTA data explorer API! Use /v1/players/{player_name} to get player data."}])


@app.get("/v1/players/{player_name}", response_model=ResponseModel)
async def get_player(player_name: str):
    # Try to get the content from Redis. If it doesn't exist,
    # load it from the file and store it in Redis for future requests.
    db = get_redis_client()
    key = get_storage_key(player_name)

    content = db.hget(key, 'content')
    if content == b'':
        path = db.hget(key, 'path')
        if path == b'':
            return ResponseModel(results=[{"message": f"No data found for player: {player_name}"}])

        # Load the content from the file and store
        # it in Redis for future requests
        path = pathlib.Path(path.decode('utf-8'))
        with path.open() as f:
            content = json.load(f)
            db.hset(
                key,
                # exat=(15 * 60),  # Cache for 15 minutes
                mapping={'content': json.dumps(content)}
            )

    if type(content) == bytes:
        content = json.loads(content)

    return ResponseModel(results=content)


@app.get("/v1/players/{player_name}/filter", response_model=ResponseModel)
async def get_player(
    player_name: str,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
    min_month: Optional[int] = None,
    max_month: Optional[int] = None,
    levels: Optional[str] = None,
    surfaces: Optional[str] = None,
    min_opponent_rank: Optional[int] = None,
    max_opponent_rank: Optional[int] = None,
    first_set_tiebreak: Optional[bool] = None,
    second_set_tiebreak: Optional[bool] = None,
    third_set_tiebreak: Optional[bool] = None,
    walkover: Optional[bool] = None,
    number_of_sets: Optional[int] = None,
    first_set_won: Optional[bool] = None,
    region: Optional[str] = None,
    subregion: Optional[str] = None,
    fifa: Optional[str] = None,
    cod_alpha_2: Optional[str] = None,
    cod_alpha_3: Optional[str] = None,
    only_wins: Optional[bool] = None,
    only_losses: Optional[bool] = None,
):
    db = get_redis_client()
    key = get_storage_key(player_name)
    content = db.hget(key, 'content')

    d = datetime.datetime.now()

    if max_date is None:
        max_date = d.date()

    if max_year is None:
        max_year = d.year

    matches = []
    for item in content:
        if min_year is not None:
            if item['year'] >= min_year and item['year'] <= max_year:
                matches.append(item)

        if min_date is not None:
            start_date = datetime.datetime.strptime(
                item['start_date'],
                '%Y-%m-%d'
            ).date()

            end_date = datetime.datetime.strptime(
                item['end_date'],
                '%Y-%m-%d'
            ).date()

            _min_date = datetime.datetime.strptime(min_date, '%Y-%m-%d').date()
            _max_date = datetime.datetime.strptime(max_date, '%Y-%m-%d').date()

            if start_date >= _min_date and end_date <= _max_date:
                matches.append(item)


def flatten(data: list[dict[str, Any]]):
    flattened: list[dict[str, Any]] = []

    fields_to_rename = {
        'code_alpha_2': 'tour_code_alpha_2',
        'code_alpha_3': 'tour_code_alpha_3',
        'country_code_m49': 'tour_country_code_m49',
        'region_code': 'tour_region_code',
        'region': 'tour_region',
        'subregion': 'tour_subregion',
        'fifa': 'tour_fifa',
    }

    for tournament in data:
        matches = tournament.pop('matches', [])

        _tournament = {}
        for key, value in tournament.items():
            if key in fields_to_rename:
                _tournament[fields_to_rename[key]] = value
                continue
            _tournament[key] = value

        for match in matches:
            flattened.append(_tournament | match)
    return flattened


@app.get("/v1/players/{player_name}/statistics", response_model=StatisticsModel)
async def get_player(player_name: str):
    db = get_redis_client()
    key = get_storage_key(player_name)
    content = db.hget(key, 'content')

    json_data = json.loads(content)
    number_of_tournaments = len(json_data)

    flat_data = flatten(json_data)
    df = pandas.DataFrame(flat_data)

    wins = df[df['win_loss'] == 'W']
    losses = df[df['win_loss'] == 'L']

    template = {
        'number_of_matches': int(len(df)),
        'number_of_tournaments': int(number_of_tournaments),
        'wins': int(wins['win_loss'].count()),
        'losses': int(losses['win_loss'].count()),
        'win_percentage': 0.0,
        'wins_by_surface': {
            'hard': int(wins[wins['surface'] == 'Hard']['win_loss'].count()),
            'clay': int(wins[wins['surface'] == 'Clay']['win_loss'].count()),
            'grass': int(wins[wins['surface'] == 'Grass']['win_loss'].count()),
            'carpet': int(wins[wins['surface'] == 'Carpet']['win_loss'].count()),
        },
        'losses_by_surface': {
            'hard': int(losses[losses['surface'] == 'Hard']['win_loss'].count()),
            'clay': int(losses[losses['surface'] == 'Clay']['win_loss'].count()),
            'grass': int(losses[losses['surface'] == 'Grass']['win_loss'].count()),
            'carpet': int(losses[losses['surface'] == 'Carpet']['win_loss'].count()),
        },
        'years': [],
        'min_year': None,
        'max_year': None,
        'surfaces': [],
        'levels': [],
        'cities': [],
        'countries': [],
        'code_alpha_2': [],
        'code_alpha_3': [],
        'country_code_m49': [],
        'min_date': None,
        'max_date': None,
    }

    template['years'] = df['year'].unique().tolist()
    template['min_year'] = int(df['year'].min())
    template['max_year'] = int(df['year'].max())
    template['surfaces'] = df['surface'].unique().tolist()
    template['levels'] = df['level'].unique().tolist()
    template['cities'] = df['city'].unique().tolist()
    template['countries'] = df['country'].unique().tolist()
    template['code_alpha_2'] = df['code_alpha_2'].unique().tolist()
    template['code_alpha_3'] = df['code_alpha_3'].unique().tolist()
    template['country_code_m49'] = df['country_code_m49'].unique().tolist()
    template['min_date'] = df['start_date'].min()
    template['max_date'] = df['start_date'].max()

    if template['number_of_matches'] > 0:
        template['win_percentage'] = round(
            (template['wins'] / template['number_of_matches']) * 100, 2
        )

    db.hsetex(key, exat=(30*60), mapping={'statistics': json.dumps(template)})

    # Advanced statistics:
    # 'cumulative_wins': [],
    # 'cumulative_losses': []
    # Cumulative wins and losses over time
    # df['cumulative_wins'] = (df['win_loss'] == 'W').cumsum()
    # df['cumulative_losses'] = (df['win_loss'] == 'L').cumsum()

    return StatisticsModel(**template)
