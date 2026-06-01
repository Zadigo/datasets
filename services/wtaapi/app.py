from typing import Optional

import redis
import json
from fastapi import FastAPI
import dotenv
import pathlib
from models import ResponseModel
from contextlib import asynccontextmanager

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


app = FastAPI(
    title="WTA data explorer",
    summary="A simple API to explore WTA data",
    description="A simple API to explore WTA data",
    lifespan=lifespan
)


@app.get("/v1/players", response_model=ResponseModel)
async def root() -> ResponseModel:
    return ResponseModel(results=[{"message": "Welcome to the WTA data explorer API! Use /v1/players/{player_name} to get player data."}])


@app.get("/v1/players/{player_name}", response_model=ResponseModel)
async def get_player(player_name: str):
    # Try to get the content from Redis. If it doesn't exist,
    # load it from the file and store it in Redis for future requests.
    db = get_redis_client()
    key = f'{DB_KEY}:{player_name}_corrected'
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
            db.hsetex(
                key,
                exat=(15 * 60),  # Cache for 15 minutes
                mapping={'content': json.dumps(content)}
            )

    return ResponseModel(results=content)
