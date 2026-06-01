import redis
import json
from fastapi import FastAPI
import dotenv
import pathlib
from wtaapi.models import ResponseModel
from contextlib import asynccontextmanager

dotenv.load_dotenv('.env')

DB_KEY = 'wta-players'

DATA_DIR = pathlib.Path(dotenv.get_key('.env', 'DATA_DIR'))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis client and load data into Redis
    db = get_redis_client()
    files = DATA_DIR.glob("*.json")
    for file in files:
        db.hset(
            f'{DB_KEY}:{file.stem}',
            mapping={
                'path': str(file),
                'name': file.stem,
                'player_name': file.stem.replace('_', ' ').replace('corrected', '').strip(),
                'content': None
            }
        )
    yield


app = FastAPI(
    title="WTA data explorer",
    summary="A simple API to explore WTA data",
    description="A simple API to explore WTA data",
    lifespan=lifespan
)


def get_redis_client() -> redis.Redis:
    client = redis.Redis(host="localhost", port=6379, db=0)
    try:
        client.ping()
    except redis.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Redis server. Please ensure it is running.")
    return client


@app.get("/v1/players", response_model=ResponseModel)
async def root(player: str = None) -> ResponseModel:
    if player is None:
        return ResponseModel(results=[{"message": "Please provide a player name to search for."}])

    # Try to get the content from Redis. If it doesn't exist,
    # load it from the file and store it in Redis for future requests.
    db = get_redis_client()
    content = db.hget(f'{DB_KEY}:{player}_corrected', 'content')
    if content is None:
        path = db.hget(f'{DB_KEY}:{player}_corrected', 'path')
        if path is None:
            return ResponseModel(results=[{"message": f"No data found for player: {player}"}])

        # Load the content from the file and store
        # it in Redis for future requests
        path = pathlib.Path(path.decode('utf-8'))
        with path.open() as f:
            content = json.load(f)
            db.hset(
                f'{DB_KEY}:{player}_corrected',
                mapping={'content': json.dumps(content)}
            )

    json_data = json.loads(content)
    return ResponseModel(results=json_data)


@app.get("/v1/players/{player_id}")
async def get_player(player_id: int):
    return {"message": f"Player ID: {player_id}"}
